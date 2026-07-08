from app.core.settings import settings

def test_settings_load():
    assert settings.APP_NAME == "Knowledge Ingestion Platform"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000
    assert settings.MONGO_URI is not None
    assert settings.MONGO_DATABASE is not None
