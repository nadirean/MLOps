import os
import json
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

WEATHER_MCP_URL = "http://weather-mcp:8002/mcp"
TAVILY_MCP_URL = "http://tavily-mcp:8003/mcp"
VLLM_BASE_URL = "http://vllm:8000/v1"

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

client = OpenAI(api_key="EMPTY", base_url=VLLM_BASE_URL)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather for a city. Returns temperature, humidity, description, wind, sunrise/sunset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g., Warsaw"},
                    "units": {"type": "string", "enum": ["metric", "imperial", "standard"]},
                },
                "required": ["city", "units"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tavily_search",
            "description": "Search the web using Tavily. Returns sources, snippets, and optional answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "search_depth": {"type": "string", "enum": ["basic", "advanced"]},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
                    "include_answer": {"type": "boolean"},
                    "include_raw_content": {"type": "boolean"},
                    "include_images": {"type": "boolean"},
                    "include_domains": {"type": "array", "items": {"type": "string"}},
                    "exclude_domains": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tavily_extract",
            "description": "Extract webpage content using Tavily.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}},
                    "include_raw_content": {"type": "boolean"},
                    "extract_depth": {"type": "string", "enum": ["basic", "advanced"]},
                },
                "required": ["urls"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are a helpful trip planning assistant. Restrict your answers to trip planning, travel details, sightseeing, weather, transport, and related topics. If the user asks about unrelated topics, politely decline."
)

def chat_loop():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    async def call_mcp_tool(route_url, tool_name_str, tool_args):
        try:
            async with streamable_http_client(route_url) as (read, write, _):
                async with ClientSession(read, write) as s:
                    await s.initialize()
                    return await s.call_tool(tool_name_str, arguments=tool_args)
        except Exception as e:
            print(f"[Error calling MCP tool at {route_url}: {e}]")

    while True:
        user = input("User: ")
        messages.append({"role": "user", "content": user})

        try:
            resp = client.chat.completions.create(
                model="",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_completion_tokens=512,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )

            resp_message = resp.choices[0].message
            content = resp_message.content.strip() if resp_message.content else ""
            tool_calls = resp_message.tool_calls or []

            if tool_calls:
                tool_call_dicts = [tc.model_dump() for tc in tool_calls]
                messages.append(
                    {
                        "role": "assistant",
                        "content": resp_message.content or "",
                        "tool_calls": tool_call_dicts,
                    }
                )

                tool_routes = {
                    "get_current_weather": {
                        "url": WEATHER_MCP_URL,
                        "label": "Weather",
                    },
                    "tavily_search": {
                        "url": TAVILY_MCP_URL,
                        "label": "Tavily search",
                    },
                    "tavily_extract": {
                        "url": TAVILY_MCP_URL,
                        "label": "Tavily extract",
                    },
                }

                for tool_call in tool_calls:
                    tool_call_dict = tool_call.model_dump()
                    tool_call_id = tool_call_dict.get("id")
                    function_payload = tool_call_dict.get("function") or {}
                    tool_name = function_payload.get("name")
                    tool_args = json.loads(function_payload.get("arguments") or "{}")
                    tool_name_str = str(tool_name)
                    route = tool_routes.get(tool_name_str)
                    route_url = route["url"]
                    route_label = route["label"]
                    print(f"[Using {route_label.lower()} tool..]")

                    try:
                        tool_result = asyncio.run(call_mcp_tool(route_url, tool_name_str, tool_args))
                        if tool_result.content:
                            tool_payload = getattr(tool_result.content[0], "text", str(tool_result.content[0]))
                        else:
                            tool_payload = ""
                    except Exception as e:
                        print(f"[Error during MCP tool call: {e}]")

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": tool_payload,
                        }
                    )

                final_resp = client.chat.completions.create(
                    model="",
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_completion_tokens=512,
                    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                )

                final_message = final_resp.choices[0].message
                final_content = final_message.content.strip() if final_message.content else ""
                print("Assistant:")
                print(final_content)
                messages.append({"role": "assistant", "content": final_content})
            else:
                print("Assistant:")
                print(content)
                messages.append({"role": "assistant", "content": content})

        except Exception as e:
            print("Error during request:", e)


if __name__ == "__main__":
    chat_loop()
