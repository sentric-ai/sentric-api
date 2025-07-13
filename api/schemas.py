from pydantic import BaseModel, Field
from typing import List

class TTSRequest(BaseModel):
    text: str = Field(..., description="Sentezlenecek metin.", example="Merhaba dünya, bu bir test mesajıdır.")
    language: str = Field(..., description="Metnin dili (örn: 'tr', 'en', 'de').", example="tr")
    voice_profile_b64: str = Field(..., description="'/clone_voice' endpoint'inden alınan Base64 kodlanmış ses profili.")
    speed: float = Field(1.0, description="Konuşma hızı. 1.0 normaldir. <1 yavaş, >1 hızlı.", ge=0.5, le=2.0)
    temperature: float = Field(0.75, description="Üretimdeki rastlantısallık seviyesi. Yüksek değerler daha çeşitli, düşük değerler daha deterministik sonuçlar verir.", ge=0.0, le=1.0)
    top_p: float = Field(0.85, description="Nucleus sampling için kümülatif olasılık eşiği.", ge=0.0, le=1.0)

class CloneResponse(BaseModel):
    voice_profile_b64: str = Field(..., description="TTS isteklerinde kullanılacak, Base64 ile kodlanmış ses profili.")

class LanguagesResponse(BaseModel):
    languages: List[str] = Field(..., description="Desteklenen dillerin listesi.", example=["en", "tr", "de", "es"])