import joblib
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from .settings import get_settings


def export_classifier_to_onnx():
    settings = get_settings()
    classifier = joblib.load(settings.classifier_joblib_path)
    initial_type = [("float_input", FloatTensorType([None, settings.embedding_dim]))]
    onnx_model = convert_sklearn(classifier, initial_types=initial_type)
    settings.onnx_classifier_path.parent.mkdir(parents=True, exist_ok=True)

    with open(settings.onnx_classifier_path, "wb") as f:
        f.write(onnx_model.SerializeToString())

    print(f"Saved ONNX classifier to {settings.onnx_classifier_path}")


if __name__ == "__main__":
    export_classifier_to_onnx()
