import datetime
from fastmcp import FastMCP

mcp = FastMCP("DateTime Server")

@mcp.tool(description="Get current date in the format YYYY-MM-DD")
def get_current_date() -> str:
    return datetime.date.today().isoformat()

@mcp.tool(description="Get current date and time in ISO 8601 format")
def get_current_datetime() -> str:
    return datetime.datetime.now().isoformat()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8002)
