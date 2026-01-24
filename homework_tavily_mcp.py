import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"

mcp = FastMCP("Tavily MCP")


def _post_api(url: str, payload: dict) -> dict:
    body = payload.copy()
    body.setdefault("api_key", TAVILY_API_KEY)

    try:
        resp = requests.post(url, json=body, timeout=15)
    except requests.RequestException as exc:
        return {"error": {"type": "request", "message": str(exc)}}

    if not resp.ok:
        return {
            "error": {
                "type": "http",
                "status": resp.status_code,
                "message": resp.text,
            }
        }

    try:
        return resp.json()
    except ValueError:
        return {"error": {"type": "parse", "message": "Invalid JSON response"}}


@mcp.tool(description="Search the web using Tavily. Returns sources, snippets, and optional answer.")
def tavily_search(
    query,
    search_depth="basic",
    max_results=5,
    include_answer=False,
    include_raw_content=False,
    include_images=False,
    include_domains=None,
    exclude_domains=None,
) -> dict:
    payload = {
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
        "include_images": include_images,
    }
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains

    return _post_api(TAVILY_SEARCH_URL, payload)


@mcp.tool(description="Extract webpage content with Tavily. Provide one or more URLs.")
def tavily_extract(urls, include_raw_content=False, extract_depth="basic") -> dict:
    payload = {
        "urls": urls,
        "include_raw_content": include_raw_content,
        "extract_depth": extract_depth,
    }

    return _post_api(TAVILY_EXTRACT_URL, payload)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8003)
