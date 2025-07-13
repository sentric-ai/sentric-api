import io
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import torch
import json
import base64

# Sentric Engine'i import et
# Bu, 'sentric-engine' reposunun kurulmuş olmasını gerektirir
from sentric_engine.engine import SentricEngine

app = FastAPI(
    title="Sentric Voice API",
    description="XTTS-v2 tabanlı, yüksek kaliteli, çok dilli ses klonlama ve sentezleme API'si.",
    version="1.0.0",
)

# Global Engine nesnesi (Uygulama başladığında bir kere yüklenir)
# Production ortamında bu yüklemeyi startup event'i içinde yapmak daha iyidir.
engine = SentricEngine(use_cuda=True)

class TTSRequest(BaseModel):
    text: str
    language: str
    voice_profile_b64: str  # Base64-encoded JSON of the voice profile
    speed: float = 1.0
    temperature: float = 0.75
    top_p: float = 0.85
    # Diğer inference parametreleri eklenebilir

@app.post("/clone-voice", summary="Ses Klonlama")
async def clone_voice(wav_file: UploadFile = File(...)):
    """
    Yüklenen bir WAV dosyasından bir ses profili (conditioning latents) oluşturur.
    Bu profil, daha sonraki TTS isteklerinde sesi klonlamak için kullanılır.
    """
    if wav_file.content_type not in ["audio/wav", "audio/x-wav"]:
        raise HTTPException(status_code=400, detail="Desteklenmeyen dosya formatı. Lütfen .wav dosyası yükleyin.")

    try:
        # Dosyayı geçici bir yere kaydetmek yerine doğrudan memory'de işleyelim
        temp_wav_path = f"/tmp/{wav_file.filename}"
        with open(temp_wav_path, "wb") as f:
            f.write(await wav_file.read())
            
        voice_profile = engine.get_conditioning_latents(audio_path=temp_wav_path)
        
        # Tensorları CPU'ya alıp listeye çevirerek serileştirilebilir hale getir
        serializable_profile = {
            "speaker_embedding": voice_profile["speaker_embedding"].cpu().tolist(),
            "gpt_cond_latents": voice_profile["gpt_cond_latents"].cpu().tolist(),
        }
        
        # Sonucu JSON olarak base64 formatında döndür
        profile_json_str = json.dumps(serializable_profile)
        profile_b64 = base64.b64encode(profile_json_str.encode('utf-8')).decode('utf-8')
        
        return {"voice_profile_b64": profile_b64}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ses profili oluşturulurken bir hata oluştu: {str(e)}")
    finally:
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)


@app.post("/tts-stream", summary="Gerçek Zamanlı Ses Sentezi (Streaming)")
async def tts_stream(request: TTSRequest):
    """
    Metni ve ses profilini kullanarak sesi parça parça (streaming) olarak sentezler.
    Gerçek zamanlı uygulamalar için idealdir.
    """
    try:
        # Base64'ten profili çöz
        profile_json_str = base64.b64decode(request.voice_profile_b64).decode('utf-8')
        profile_data = json.loads(profile_json_str)

        # Listeleri tensörlere dönüştür
        voice_profile = {
            "speaker_embedding": torch.tensor(profile_data["speaker_embedding"]).to(engine.device),
            "gpt_cond_latents": torch.tensor(profile_data["gpt_cond_latents"]).to(engine.device)
        }

        # Generator fonksiyonunu çağır
        audio_chunk_generator = engine.tts_stream(
            text=request.text,
            language=request.language,
            voice_profile=voice_profile,
            speed=request.speed,
            temperature=request.temperature,
            top_p=request.top_p,
        )
        return StreamingResponse(audio_chunk_generator, media_type="audio/raw")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ses sentezlenirken bir hata oluştu: {str(e)}")

@app.get("/supported-languages", summary="Desteklenen Diller")
async def get_languages():
    """
    Model tarafından desteklenen dillerin listesini döndürür.
    """
    return {"languages": engine.model.config.languages}