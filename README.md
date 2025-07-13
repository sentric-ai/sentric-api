# Sentric API

Bu API, `sentric-engine` kütüphanesini kullanarak ses klonlama ve sentezleme hizmeti sunar.

## Kurulum

Öncelikle, `sentric-engine` kütüphanesinin bir üst dizinde klonlandığından ve kurulduğundan emin olun.

```bash
# Bir üst dizine git
cd .. 
# sentric-engine'i kur (eğer kurulmadıysa)
pip install -e ./sentric-engine

# API bağımlılıklarını kur
cd sentiric-api
pip install -r requirements.txt
```

## Çalıştırma
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Sunucu çalışmaya başladıktan sonra, interaktif dokümantasyona http://localhost:8000/docs adresinden ulaşabilirsiniz.