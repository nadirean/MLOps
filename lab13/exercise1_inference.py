import time
from openai import OpenAI

def measure_inference(prompts):
    client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
    start_time = time.time()

    for prompt in prompts:
        client.chat.completions.create(
            model="",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=500,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}}
        )

    end_time = time.time()
    total_time = end_time - start_time

    print(f"Total time for {len(prompts)} prompts: {total_time:.2f}s")
    print(f"Average time per prompt: {total_time / len(prompts):.2f}s")

if __name__ == "__main__":
    test_prompts = [
        "What is the meaning of life?",
        "Explain to me how to pass a semester of university.",
        "What is the difference between analyst and analystics?",
        "How does a plane fly?",
        "Summarize the benefits of exerciing daily.",
        "What is the capital of France?",
        "What's the best place to visit in italy?",
        "What is 2+2?",
        "Give me a recipe for banana bread.",
        "What is love?"
    ]

    measure_inference(test_prompts)
