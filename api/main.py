from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import torch

from sentric_engine import SentricEngine

from .schemas import TTSRequest, CloneResponse, LanguagesResponse
from .profiler import create_voice_profile, load_voice_profile

app = FastAPI(
    title="Sentric Voice API",
    description="XTTS-v2 tabanlı, yüksek kaliteli, çok dilli ses klonlama ve sentezleme API'si.",
    version="1.0.0",
)

# Global Engine nesnesi
engine = SentricEngine(use_cuda=True)

@app.post("/clone_voice", response_model=CloneResponse, summary="Ses Profili Oluştur")
async def clone_voice_endpoint(wav_file: UploadFile = File(..., description="Klonlanacak referans ses dosyası (.wav formatında).")):
    """
    Yüklenen bir WAV dosyasından bir 'ses profili' oluşturur.
    Bu profil, daha sonraki TTS isteklerinde sesi klonlamak için kullanılır.
    """
    if wav_file.content_type not in ["audio/wav", "audio/x-wav"]:
        raise HTTPException(status_code=400, detail="Desteklenmeyen dosya formatı. Lütfen .wav dosyası yükleyin.")

    try:
        profile_b64 = await create_voice_profile(engine, wav_file)
        return CloneResponse(voice_profile_b64=profile_b64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ses profili oluşturulurken bir hata oluştu: {e}")

@app.post("/tts_stream", summary="Gerçek Zamanlı Ses Sentezi (Streaming)")
async def tts_stream_endpoint(request: TTSRequest):
    """
    Metni ve ses profilini kullanarak sesi parça parça (streaming) olarak sentezler.
    Gerçek zamanlı uygulamalar için idealdir.
    """
    try:
        voice_profile = load_voice_profile(request.voice_profile_b64, engine.device)

        audio_generator = engine.tts_stream(
            text=request.text,
            language=request.language,
            voice_profile=voice_profile,
            speed=request.speed,
            temperature=request.temperature,
            top_p=request.top_p,
        )
        return StreamingResponse(audio_generator, media_type="audio/raw")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ses sentezlenirken bir hata oluştu: {e}")

@app.get("/supported_languages", response_model=LanguagesResponse, summary="Desteklenen Dilleri Listele")
async def get_languages_endpoint():
    """
    Model tarafından desteklenen dillerin listesini döndürür.
    """
    return LanguagesResponse(languages=engine.model.config.languages)