import json
from typing import Callable
import polars as pl
from openai import OpenAI

def read_remote_csv(url: str) -> str:
    return str(pl.read_csv(url, n_rows=10))

def read_remote_parquet(url: str) -> str:
    return str(pl.read_parquet(url, n_rows=10))

def get_tool_definitions() -> tuple[list[dict], dict[str, Callable]]:
    tool_definitions = [
        {
            "type": "function",
            "function": {
                "name": "read_remote_csv",
                "description": "Read a CSV file from a URL and return its first rows as text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL of the CSV file."}
                    },
                    "required": ["url"]
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_remote_parquet",
                "description": "Read a Parquet file from a URL and return its first rows as text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL of the Parquet file."}
                    },
                    "required": ["url"]
                },
            },
        },
    ]

    tool_name_to_callable = {
        "read_remote_csv": read_remote_csv,
        "read_remote_parquet": read_remote_parquet,
    }

    return tool_definitions, tool_name_to_callable

def make_llm_request(prompt: str):
    client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    messages = [
        {"role": "system", "content": "You are a data assistant. Use the provided tools to read remote files when a URL is given."},
        {"role": "user", "content": prompt},
    ]

    tool_definitions, tool_name_to_func = get_tool_definitions()

    for _ in range(5):
        response = client.chat.completions.create(
            model="",
            messages=messages,
            tools=tool_definitions,
            tool_choice="auto",
            max_completion_tokens=2000,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        resp_message = response.choices[0].message
        messages.append(resp_message.model_dump())

        if resp_message.tool_calls:
            for tool_call in resp_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"Calling tool: {func_name} with args: {func_args}")
                func = tool_name_to_func[func_name]
                func_result = func(**func_args)

                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(func_result),
                        "tool_call_id": tool_call.id,
                    }
                )
        else:
            return resp_message.content

    return "Max iterations reached."

if __name__ == "__main__":
    csv_url = "https://raw.githubusercontent.com/j-adamczyk/ApisTox_dataset/master/outputs/dataset_final.csv"
    parquet_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet"

    print("Response:\n", make_llm_request(f"Please read the first 10 rows of the CSV file at {csv_url} and tell me what the columns are."))
    print()
    print("Response:\n", make_llm_request(f"How many rows and columns are in the CSV at {csv_url}? Provide only numbers."))
    print()
    print("Response:\n", make_llm_request(f"Please read the first 10 rows of the Parquet file at {parquet_url} and tell me what the columns are."))
    print()
    print("Response:\n", make_llm_request(f"How many rows and columns are in the Parquet file at {parquet_url}? Provide only numbers."))
