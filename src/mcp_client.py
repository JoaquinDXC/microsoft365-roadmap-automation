"""Microsoft Release Communications MCP Client - Direct connection."""

import asyncio
import httpx
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from logger import logger


class MCPClient:
    """Client for Microsoft Release Communications MCP Server (Streamable HTTP)."""

    def __init__(
        self,
        endpoint: str = "https://www.microsoft.com/releasecommunications/mcp",
        timeout: int = 30
    ):
        self.endpoint = endpoint
        self.timeout = timeout
        self.request_id = 0
        self.tools_cache = None

    def _get_next_id(self) -> int:
        self.request_id += 1
        return self.request_id

    def _build_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Build JSON-RPC 2.0 request with MCP protocol metadata."""
        if params is None:
            params = {}

        if "_meta" not in params:
            params["_meta"] = {}

        params["_meta"]["io.modelcontextprotocol/protocolVersion"] = "2026-07-28"
        params["_meta"]["io.modelcontextprotocol/clientInfo"] = {
            "name": "m365-roadmap-client",
            "version": "2.0.0"
        }

        return {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params
        }

    async def _parse_sse_response(self, response_text: str) -> Optional[Dict]:
        """Parse Server-Sent Events response containing JSON-RPC message."""
        for line in response_text.split('\n'):
            if line.startswith('data: '):
                json_data = line[6:]
                try:
                    return json.loads(json_data)
                except json.JSONDecodeError:
                    pass
        return None

    async def _call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a tool on the MCP server."""
        request = self._build_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    json=request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    logger.error(f"MCP tools/call returned HTTP {response.status_code}")
                    return {"error": f"HTTP {response.status_code}"}

                parsed = await self._parse_sse_response(response.text)

                if not parsed:
                    logger.error("Failed to parse MCP response")
                    return {"error": "Unable to parse response"}

                # Unwrap MCP result format
                if "result" in parsed:
                    result = parsed["result"]
                    if "content" in result and isinstance(result["content"], list):
                        if result["content"]:
                            content_item = result["content"][0]
                            if "text" in content_item:
                                try:
                                    return json.loads(content_item["text"])
                                except json.JSONDecodeError:
                                    return content_item
                    return result

                return parsed

        except httpx.TimeoutException:
            logger.error(f"MCP request timeout after {self.timeout}s")
            return {"error": "Timeout"}
        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            return {"error": str(e)}

    async def discover_tools(self) -> List[Dict]:
        """Discover available tools via tools/list."""
        if self.tools_cache:
            return self.tools_cache

        request = self._build_request("tools/list", {})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    json=request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    logger.error(f"tools/list failed: HTTP {response.status_code}")
                    return []

                parsed = await self._parse_sse_response(response.text)

                if parsed and "result" in parsed:
                    tools = parsed["result"].get("tools", [])
                    self.tools_cache = tools
                    return tools

                return []

        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")
            return []

    async def get_recent_roadmaps(self, skip: int = 0) -> Dict:
        """Get recent M365 roadmap items with pagination."""
        # First determine which tool to use
        tools = await self.discover_tools()
        tool_names = [t.get("name") for t in tools]

        if "get_recent_m365_roadmaps" in tool_names:
            tool_name = "get_recent_m365_roadmaps"
        elif "get_recent_roadmaps" in tool_names:
            tool_name = "get_recent_roadmaps"
        else:
            logger.error("No compatible roadmap listing tool found")
            return {"error": "Tool not found", "items": []}

        logger.debug(f"Using tool: {tool_name}")

        result = await self._call_tool(tool_name, {"skip": skip})

        if "error" in result:
            return result

        return result

    async def get_roadmap_by_id(self, roadmap_id: str) -> Dict:
        """Get full details of a specific roadmap item by ID."""
        # Determine which tool to use
        tools = await self.discover_tools()
        tool_names = [t.get("name") for t in tools]

        if "get_m365_roadmap_by_id" in tool_names:
            tool_name = "get_m365_roadmap_by_id"
        elif "get_roadmap_by_id" in tool_names:
            tool_name = "get_roadmap_by_id"
        else:
            logger.error("No compatible roadmap detail tool found")
            return {"error": "Tool not found"}

        result = await self._call_tool(tool_name, {"id": str(roadmap_id)})
        return result
