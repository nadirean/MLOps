import base64
import io
import matplotlib.pyplot as plt
from fastmcp import FastMCP

mcp = FastMCP("Visualization Server")

@mcp.tool(description="Create a line plot from given data and return it as a base64 encoded image.")
def line_plot(
    data, title
) -> str:
    plt.figure()
    plt.plot(data)
    plt.title(title)
    plt.xlabel("X")
    plt.ylabel("Y")

    buf = io.BytesIO()
    plt.savefig(buf)
    buf.seek(0)

    return base64.b64encode(buf.read()).decode('utf-8')

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8001)
