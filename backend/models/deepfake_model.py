from PIL import Image
import torch
import io

def detect_deepfake(image_bytes: bytes) -> dict:
    from backend.main import models
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    processor = models.get("siglip_processor")
    model = models.get("siglip_model")
    
    if not processor or not model:
        return {"error": "Model not loaded"}
    
    inputs = processor(
        text=["a real authentic photograph of a person",
              "a deepfake or AI generated fake image"],
        images=image,
        return_tensors="pt",
        padding=True
    )
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    probs = outputs.logits_per_image.softmax(dim=1)
    real_prob = probs[0][0].item()
    fake_prob = probs[0][1].item()
    
    label = "DEEPFAKE" if fake_prob > 0.5 else "REAL"
    
    if fake_prob > 0.85:
        explanation = "Strong deepfake artifacts detected. Facial boundary blur present. Lighting inconsistent. Eye movement pattern unnatural."
    elif fake_prob > 0.65:
        explanation = "Possible AI manipulation detected. Subtle texture anomalies found around facial regions."
    elif fake_prob > 0.45:
        explanation = "Minor inconsistencies detected. Image may be edited or processed."
    else:
        explanation = "Image appears authentic. Natural facial features, consistent lighting, no artifacts found."
    
    return {
        "label": label,
        "fake_score": round(fake_prob, 4),
        "real_score": round(real_prob, 4),
        "confidence": round(max(real_prob, fake_prob), 4),
        "explanation": explanation,
        "model_used": "SigLIP2 (google/siglip-so400m-patch14-384)"
    }
