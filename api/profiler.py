import base64
import json
import os
from tempfile import NamedTemporaryFile

import torch
from fastapi import UploadFile

from sentric_engine import SentricEngine

async def create_voice_profile(engine: SentricEngine, wav_file: UploadFile) -> str:
    """
    Geçici bir dosyaya yazılan WAV'dan ses profili oluşturur ve bunu Base64 olarak kodlar.
    """
    try:
        # FastAPI'nin UploadFile nesnesini geçici bir dosyaya yaz
        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await wav_file.read()
            temp_file.write(content)
            temp_wav_path = temp_file.name

        # Engine'i kullanarak profili oluştur
        voice_profile = engine.get_conditioning_latents(audio_path=temp_wav_path)
        
        # Tensorları serileştirilebilir formata çevir
        serializable_profile = {
            "speaker_embedding": voice_profile["speaker_embedding"].cpu().tolist(),
            "gpt_cond_latents": voice_profile["gpt_cond_latents"].cpu().tolist(),
        }
        
        # JSON string'e ve ardından Base64'e çevir
        profile_json_str = json.dumps(serializable_profile)
        profile_b64 = base64.b64encode(profile_json_str.encode('utf-8')).decode('utf-8')
        
        return profile_b64
    finally:
        # Geçici dosyayı sil
        if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

def load_voice_profile(profile_b64: str, device: torch.device) -> dict:
    """
    Base64 ile kodlanmış ses profilini çözer ve tensörlere dönüştürür.
    """
    profile_json_str = base64.b64decode(profile_b64).decode('utf-8')
    profile_data = json.loads(profile_json_str)
    
    voice_profile = {
        "speaker_embedding": torch.tensor(profile_data["speaker_embedding"]).to(device),
        "gpt_cond_latents": torch.tensor(profile_data["gpt_cond_latents"]).to(device)
    }
    return voice_profile