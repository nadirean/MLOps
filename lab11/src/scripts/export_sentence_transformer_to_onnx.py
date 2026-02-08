import os
from .settings import Settings, get_settings
import torch
from transformers import AutoTokenizer, AutoModel


# Wrapper to include Mean Pooling in the ONNX graph
class SentenceEmbeddingModel(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, input_ids, attention_mask):
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
        # Last hidden state: (Batch, Seq, Hidden)
        last_hidden_state = outputs.last_hidden_state

        # Mean Pooling operation
        # attention_mask: (Batch, Seq) -> expand to (Batch, Seq, Hidden)
        mask_expanded = (
            attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        )

        # Sum embeddings where mask is 1
        sum_embeddings = torch.sum(last_hidden_state * mask_expanded, 1)

        # Sum mask to get count of valid tokens
        sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)

        # Divide to get mean
        mean_pooled = sum_embeddings / sum_mask
        return mean_pooled


def export_model_to_onnx(settings: Settings):
    # Use AutoModel to get embeddings (not classification logits)
    base_model = AutoModel.from_pretrained(settings.sentence_transformer_dir)
    tokenizer = AutoTokenizer.from_pretrained(settings.sentence_transformer_dir)

    # Wrap model
    model = SentenceEmbeddingModel(base_model)

    model.eval()
    dummy_text = "This is a sample input for ONNX export."
    inputs = tokenizer(dummy_text, return_tensors="pt")

    onnx_path = settings.onnx_embedding_model_path
    os.makedirs(os.path.dirname(onnx_path), exist_ok=True)

    with torch.no_grad():
        torch.onnx.export(
            model,
            (inputs["input_ids"], inputs.get("attention_mask")),
            onnx_path,
            input_names=["input_ids", "attention_mask"],
            output_names=["sentence_embedding"],  # pooled embedding (Batch, Hidden)
            dynamic_axes={
                "input_ids": {0: "batch_size", 1: "sequence"},
                "attention_mask": {0: "batch_size", 1: "sequence"},
                "sentence_embedding": {0: "batch_size"},
            },
            opset_version=18,
            dynamo=False,
        )

    print(f"ONNX model exported to {onnx_path}")
    return onnx_path

if __name__ == "__main__":
    export_model_to_onnx(get_settings())
