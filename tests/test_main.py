import os
from main import export_envs


def test_export_envs():
    export_envs("test")
    assert os.getenv("ENVIRONMENT") == "test"
    assert os.getenv("APP_NAME") == "MLOps-lab1"
