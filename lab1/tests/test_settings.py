from settings import Settings


def test_settings_load():
    settings = Settings()
    assert settings.ENVIRONMENT == "test"
    assert settings.APP_NAME == "MLOps-lab1"
    assert settings.API_KEY == "KD2BNSUDU3S"


def test_environment_validation():
    settings = Settings()
    assert settings.ENVIRONMENT in ("dev", "test", "prod")
