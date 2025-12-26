from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    s3_bucket: str = "mlops-lab11-models-wbart1"
    local_model_dir: Path = Path("model")
    sentence_transformer_dir: Path = local_model_dir / "sentence_transformer.model"
    classifier_joblib_path: Path = local_model_dir / "classifier.joblib"
    onnx_embedding_model_path: Path = local_model_dir / "onnx" / "embedding.onnx"
    onnx_classifier_path: Path = local_model_dir / "onnx" / "classifier.onnx"
    onnx_tokenizer_path: Path = local_model_dir / "onnx" / "tokenizer.json"
    embedding_dim: int = 768


def get_settings() -> Settings:
    return Settings()
