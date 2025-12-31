import sys
from src.scripts.download_artifacts import main as download
from src.scripts.export_classifier_to_onnx import export_classifier_to_onnx
from src.scripts.export_sentence_transformer_to_onnx import export_model_to_onnx
from src.scripts.settings import get_settings

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py [download|export]")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "download":
        download()
    elif action == "export":
        export_classifier_to_onnx()
        export_model_to_onnx(get_settings())
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
