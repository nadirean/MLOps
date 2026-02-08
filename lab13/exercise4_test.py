import asyncio
import json
import base64
from openai import OpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def main():
    client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    prompt = (
        'You are a visualization assistant. Call function "line_plot" with JSON arguments: '
        '{"data":[1,5,2,8,3,10],"title":"Lab 13 Test"}'
    )

    resp = client.chat.completions.create(
        model="",
        messages=[
            {"role":"user","content":prompt}
        ],
        max_completion_tokens=500,
        extra_body={"chat_template_kwargs":{"enable_thinking": False}},
    )

    text = resp.choices[0].message.content.strip()
    # extract JSON object from the model response
    start = text.find('{')
    end = text.rfind('}')

    json_text = text[start:end+1]
    args = json.loads(json_text)

    async with streamable_http_client("http://localhost:8001/mcp") as (read, write, sid):
        async with ClientSession(read, write) as s:
            await s.initialize()
            result = await s.call_tool("line_plot", arguments=args)
            b64 = result.content[0].text
            open("output_plot.png","wb").write(base64.b64decode(b64))
            print("Saved output_plot.png")

if __name__ == "__main__":
    asyncio.run(main())
