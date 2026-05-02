import asyncio
import json
import uuid
import subprocess
import tempfile
import os
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.db.sqlite_logger import log_session_chunk, finalize_session

router = APIRouter()

OTP_PHRASES = [
    "otp", "one time password", "verification code",
    "otp bata", "pin bata", "otp share karo", "otp bhejo",
    "otp batao", "password bata", "code bata", "otp kya hai",
    "secret code", "passcode"
]

SCAM_PHRASES = [
    "account block", "account band", "suspend", "kyc update",
    "kyc verify", "ek rupaya bhejo", "prize", "lottery",
    "screen share", "remote access", "anydesk", "teamviewer",
    "sbi se bol raha", "bank se bol raha", "rbi se bol raha",
    "reward claim", "fee bhejo", "processing fee"
]

def detect_otp(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in OTP_PHRASES)

def detect_scam_keywords(text: str) -> list:
    t = text.lower()
    return [p for p in SCAM_PHRASES if p in t]

def determine_action(score: float, otp_count: int) -> str:
    if otp_count >= 2:
        return "CUT_CALL"
    elif score > 0.75 or otp_count == 1:
        return "ALERT_USER"
    else:
        return "continue"

def get_status(score: float, otp_count: int) -> str:
    if otp_count >= 2 or score > 0.85:
        return "Imposter"
    elif score > 0.5 or otp_count == 1:
        return "Suspicious"
    else:
        return "Safe"

@router.websocket("/api/v1/call/ws")
async def call_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    otp_count = 0
    chunk_index = 0

    # Send session started confirmation
    await websocket.send_text(json.dumps({
        "type": "session_started",
        "session_id": session_id,
        "message": "ShieldCall Live connected. Monitoring started.",
        "timestamp": datetime.utcnow().isoformat()
    }))

    print(f"[ShieldCall] Session: {session_id}")

    try:
        while True:
            try:
                audio_bytes = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "message": "Listening..."
                }))
                continue

            chunk_index += 1
            timestamp = datetime.utcnow().isoformat()

            # ── STEP 1: Send "processing" immediately so UI updates ──
            await websocket.send_text(json.dumps({
                "type": "processing",
                "chunk": chunk_index,
                "message": f"Processing chunk {chunk_index}...",
                "stage": "converting_audio"
            }))

            # ── STEP 2: Transcribe (in thread — non-blocking) ──
            await websocket.send_text(json.dumps({
                "type": "processing",
                "chunk": chunk_index,
                "message": "Whisper transcribing audio...",
                "stage": "transcribing"
            }))

            transcript = await asyncio.to_thread(
                _transcribe_chunk, audio_bytes
            )

            # ── STEP 3: If empty — tell UI ──
            if not transcript or transcript.strip() == "":
                await websocket.send_text(json.dumps({
                    "type": "chunk_empty",
                    "chunk": chunk_index,
                    "message": "No speech detected in this chunk. Keep talking...",
                    "timestamp": timestamp
                }))
                continue

            # ── STEP 4: Tell UI transcript received, now analyzing ──
            await websocket.send_text(json.dumps({
                "type": "processing",
                "chunk": chunk_index,
                "message": "Running scam detection...",
                "stage": "analyzing",
                "transcript_preview": transcript[:50] + "..." if len(transcript) > 50 else transcript
            }))

            # ── STEP 5: OTP + Scam detection ──
            if detect_otp(transcript):
                otp_count += 1

            triggered_rules = detect_scam_keywords(transcript)
            if detect_otp(transcript):
                triggered_rules.append("otp_request_detected")

            # Score calculation
            base_score = len(triggered_rules) * 0.15
            if detect_otp(transcript):
                base_score += 0.35
            if otp_count >= 2:
                base_score = max(base_score, 0.95)
            score = min(base_score, 1.0)

            action = determine_action(score, otp_count)
            status = get_status(score, otp_count)

            # ── STEP 6: Log to SQLite ──
            await asyncio.to_thread(
                log_session_chunk,
                session_id=session_id,
                chunk_index=chunk_index,
                transcript=transcript,
                score=score,
                status=status,
                otp_count=otp_count,
                timestamp=timestamp
            )

            # ── STEP 7: Send FULL analysis result ──
            response = {
                "type": "analysis",
                "session_id": session_id,
                "chunk": chunk_index,
                "timestamp": timestamp,
                "transcript": transcript,
                "status": status,
                "score": round(score, 4),
                "score_percent": round(score * 100, 1),
                "otp_count": otp_count,
                "action": action,
                "label": _get_label(status, triggered_rules),
                "triggered_rules": triggered_rules
            }

            await websocket.send_text(json.dumps(response))

            # ── STEP 8: CUT_CALL final warning ──
            if action == "CUT_CALL":
                await websocket.send_text(json.dumps({
                    "type": "final_warning",
                    "message": "SCAM CONFIRMED — OTP requested multiple times. HANG UP IMMEDIATELY.",
                    "session_id": session_id,
                    "action": "CUT_CALL",
                    "timestamp": timestamp
                }))
                break

    except WebSocketDisconnect:
        print(f"[ShieldCall] Disconnected: {session_id}")
    except Exception as e:
        print(f"[ShieldCall] Error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Processing error: {str(e)}"
            }))
        except:
            pass
    finally:
        await asyncio.to_thread(finalize_session, session_id)

def _transcribe_chunk(audio_bytes: bytes) -> str:
    wav_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            webm_path = f.name

        wav_path = webm_path.replace(".webm", ".wav")

        result = subprocess.run([
            "ffmpeg", "-y", "-i", webm_path,
            "-ar", "16000", "-ac", "1", "-f", "wav", wav_path
        ], capture_output=True, timeout=10)

        os.unlink(webm_path)

        if result.returncode != 0:
            return ""

        from backend.main import models
        whisper_model = models.get("whisper")
        if not whisper_model:
            return ""

        out = whisper_model.transcribe(
            wav_path,
            language="hi",
            fp16=False,
            verbose=False,
            temperature=0.0,
            condition_on_previous_text=False
        )
        return out.get("text", "").strip()

    except Exception as e:
        print(f"[STT] {e}")
        return ""
    finally:
        if wav_path and os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
            except:
                pass

def _get_label(status: str, rules: list) -> str:
    if status == "Imposter":
        rule_desc = rules[0] if rules else "Multiple suspicious patterns"
        return f"SCAM DETECTED — {rule_desc.upper()}"
    elif status == "Suspicious":
        return "SUSPICIOUS ACTIVITY DETECTED"
    else:
        return "Call appears safe"
