import subprocess
import tempfile
import os

def transcribe_audio_chunk(audio_bytes: bytes) -> str:
    wav_path = None
    try:
        # Write webm bytes to temp file
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            webm_path = f.name
        
        wav_path = webm_path.replace(".webm", ".wav")
        
        # Convert webm → 16kHz mono wav
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", webm_path,
            "-ar", "16000",
            "-ac", "1",
            "-f", "wav",
            wav_path
        ], capture_output=True, timeout=10)
        
        os.unlink(webm_path)
        
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr.decode()}")
            return ""
        
        from backend.main import models
        # Use pre-loaded whisper model (fast — already in memory)
        whisper_model = models.get("whisper")
        if not whisper_model:
            return ""
        
        output = whisper_model.transcribe(
            wav_path,
            language="hi",
            task="transcribe",
            fp16=False,
            verbose=False,
            temperature=0.0,
            condition_on_previous_text=False
        )
        
        return output.get("text", "").strip()
        
    except Exception as e:
        print(f"[STT] Error: {e}")
        return ""
    finally:
        if wav_path and os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
            except:
                pass
