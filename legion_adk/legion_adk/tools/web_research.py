# legion_adk/tools/web_research.py

import os
import httpx
from google.adk import Tool
from config import SONAR_API_KEY
import asyncio

class WebResearchTool(Tool):
    """
    Multi-source intelligence gathering using Sonar API. 
    This tool provides a placeholder for integrating with web search services.
    """

    def __init__(self):
        super().__init__(
            name="web_research_tool",
            description="Performs web research using the Sonar API to find information.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"],
            },
        )
        self.sonar_api_key = SONAR_API_KEY
        self.sonar_api_url = "https://api.perplexity.ai/chat/completions" # Sonar API endpoint (Perplexity)

    async def invoke(self, query: str) -> dict:
        """
        Executes the web research using Sonar API.
        """
        print(f"WEB_RESEARCH_TOOL: Searching for '{query}' using Sonar API...")
        headers = {
            "Authorization": f"Bearer {self.sonar_api_key}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        data = {
            "model": "sonar-medium-online",  # or "sonar-small-online"
            "messages": [
                {"role": "system", "content": "You are an intelligent web researcher. Provide concise and relevant information."},
                {"role": "user", "content": f"Research: {query}"}
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.sonar_api_url, headers=headers, json=data)
                response.raise_for_status()  # Raise an exception for bad status codes
                results = response.json()
                print("WEB_RESEARCH_TOOL: Sonar API call successful.")
                # Extract relevant information
                if results and "choices" in results and len(results["choices"]) > 0:
                    content = results["choices"][0]["message"]["content"]
                    return {"success": True, "results": [{"content": content}]}
                else:
                    return {"success": False, "error": "No meaningful results from Sonar API."}
        except httpx.RequestError as e:
            print(f"WEB_RESEARCH_TOOL: HTTP Request failed: {e}")
            return {"success": False, "error": f"Network error during web research: {e}"}
        except httpx.HTTPStatusError as e:
            print(f"WEB_RESEARCH_TOOL: HTTP Status error: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"API error during web research: {e.response.status_code}"}
        except Exception as e:
            print(f"WEB_RESEARCH_TOOL: An unexpected error occurred during web research: {e}")
            return {"success": False, "error": f"Unexpected error during web research: {e}"}