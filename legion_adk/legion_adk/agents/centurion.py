# agents/adk_centurion.py - Fixed Sonar Integration with Citations

import google.generativeai as genai
from typing import List, Dict, Any, Optional
import aiohttp
from datetime import datetime
from services.state_manager import StateManager
from services.adk_communication import A2ATask
from agents.base_adk_agent import BaseADKAgent

class CenturionADKAgent(BaseADKAgent):
    """CENTURION agent - Fixed search with proper Sonar content extraction and citations"""

    def __init__(self, state_manager: StateManager, sonar_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        super().__init__("centurion", state_manager, gemini_api_key)
        self.sonar_api_key = sonar_api_key
        self.session = None
        
        if not sonar_api_key:
            raise ValueError("CENTURION requires Sonar API key")

    async def _get_http_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()

    def _get_agent_personality(self) -> str:
        return """a focused search specialist. You find relevant information quickly and efficiently."""

    async def _execute_agent_task(self, task: A2ATask) -> Dict[str, Any]:
        """Execute search tasks through A2A interface"""
        task_type = task.task_type
        parameters = task.parameters
        chat_id = task.chat_id
        
        # Extract query from various parameter formats
        query = (parameters.get("research_query") or 
                parameters.get("query") or 
                parameters.get("question") or 
                parameters.get("specific_question", ""))
        
        if not query:
            return {
                "status": "error",
                "error": "No search query provided",
                "summary": "Search failed: missing query"
            }

        return await self._perform_search(query, parameters, chat_id)

    async def _perform_search(self, query: str, parameters: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        """Main search method"""
        max_results = parameters.get("max_results", 15)
        
        await self.state_manager.add_agent_operation(
            chat_id=chat_id,
            agent="CENTURION",
            operation_type="searching",
            title=f"Searching: {query}",
            details="Collecting information",
            status="active",
            progress=50
        )

        try:
            sources, citations = await self._search_with_sonar(query, max_results)
            
            await self.state_manager.add_agent_operation(
                chat_id=chat_id,
                agent="CENTURION",
                operation_type="searching",
                title=f"Search Complete: {query}",
                details=f"Found {len(sources)} sources with {len(citations)} citations",
                status="completed",
                progress=100
            )

            return {
                "status": "completed",
                "collected_data": {
                    "query": query,
                    "sources": sources,
                    "citations": citations,  # Include citations in the response
                    "metadata": {
                        "total_sources": len(sources),
                        "total_citations": len(citations),
                        "timestamp": datetime.now().isoformat()
                    }
                },
                "source_count": len(sources),
                "citation_count": len(citations),
                "next_agent": "augur",
                "ready_for_analysis": True,
                "summary": f"Found {len(sources)} sources with {len(citations)} citations for: {query}"
            }
            
        except Exception as e:
            await self.state_manager.add_agent_operation(
                chat_id=chat_id,
                agent="CENTURION",
                operation_type="searching",
                title=f"Search Failed: {query}",
                details=f"Error: {str(e)}",
                status="error",
                progress=0
            )
            
            return {
                "status": "error",
                "error": f"Search failed: {str(e)}", 
                "summary": f"Search error: {str(e)}"
            }

    async def _search_with_sonar(self, query: str, max_results: int) -> tuple[List[Dict], List[Dict]]:
        """FIXED: Search using Sonar API with proper content extraction and citations"""
        session = await self._get_http_session()
        
        headers = {
            "Authorization": f"Bearer {self.sonar_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": f"Research and find detailed information about: {query}"}],
            "max_tokens": 3000,
            "return_citations": True
        }
        
        async with session.post("https://api.perplexity.ai/chat/completions", 
                               json=payload, headers=headers) as response:
            
            if response.status != 200:
                raise Exception(f"Sonar API returned status {response.status}")
            
            data = await response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            search_results = data.get("search_results", [])
            
            if not content:
                raise Exception("No content received from Sonar API")
            
            sources = []
            formatted_citations = []
            
            # Process search results and citations together
            if search_results:
                # Use search_results for richer metadata
                for i, result in enumerate(search_results[:max_results]):
                    url = result.get("url", "")
                    title = result.get("title", f"Source {i+1}")
                    date = result.get("date", "")
                    
                    # Extract relevant content for this source
                    content_start = i * (len(content) // len(search_results))
                    content_end = content_start + (len(content) // len(search_results))
                    source_content = content[content_start:content_end].strip()
                    
                    sources.append({
                        "title": title,
                        "content": source_content,
                        "url": url,
                        "date": date,
                        "relevance": 0.9 - (i * 0.05),
                        "source_type": self._classify_source(url),
                        "domain": self._extract_domain(url),
                        "citation_index": i + 1  # For referencing in citations
                    })
                    
                    # Create formatted citation
                    formatted_citations.append({
                        "index": i + 1,
                        "url": url,
                        "title": title,
                        "date": date,
                        "domain": self._extract_domain(url)
                    })
                    
            elif citations:
                # Fallback to citations if no search_results
                content_per_source = len(content) // len(citations) if len(citations) > 0 else len(content)
                
                for i, url in enumerate(citations[:max_results]):
                    domain = self._extract_domain(url)
                    
                    # Extract content for this source
                    start_pos = i * content_per_source
                    end_pos = start_pos + content_per_source if i < len(citations) - 1 else len(content)
                    source_content = content[start_pos:end_pos].strip()
                    
                    # Ensure minimum content length
                    if len(source_content) < 200 and len(content) > 200:
                        source_content = content[:500]
                    
                    sources.append({
                        "title": f"{domain} - {query}",
                        "content": source_content,
                        "url": url,
                        "date": "",
                        "relevance": 0.9 - (i * 0.05),
                        "source_type": self._classify_source(url),
                        "domain": domain,
                        "citation_index": i + 1
                    })
                    
                    # Create formatted citation
                    formatted_citations.append({
                        "index": i + 1,
                        "url": url,
                        "title": f"{domain} - {query}",
                        "date": "",
                        "domain": domain
                    })
            else:
                # No citations or search results, create one source with all content
                sources.append({
                    "title": f"Research Results - {query}",
                    "content": content,
                    "url": "https://www.perplexity.ai/",
                    "date": datetime.now().isoformat(),
                    "relevance": 0.9,
                    "source_type": "ai_research",
                    "domain": "perplexity.ai",
                    "citation_index": 1
                })
                
                formatted_citations.append({
                    "index": 1,
                    "url": "https://www.perplexity.ai/",
                    "title": f"Research Results - {query}",
                    "date": datetime.now().isoformat(),
                    "domain": "perplexity.ai"
                })
            
            return sources, formatted_citations

    def _extract_domain(self, url: str) -> str:
        try:
            return url.split("//")[1].split("/")[0] if "//" in url else url.split("/")[0]
        except:
            return "unknown"

    def _classify_source(self, url: str) -> str:
        url_lower = url.lower()
        if ".edu" in url_lower:
            return "academic"
        elif ".gov" in url_lower:
            return "government"
        elif any(news in url_lower for news in ["news", "times", "post", "reuters", "bbc"]):
            return "news"
        elif any(journal in url_lower for journal in ["journal", "scholar", "research", "pubmed"]):
            return "journal"
        elif any(tech in url_lower for tech in ["github", "stackoverflow", "medium"]):
            return "technical"
        return "web"

    # Legacy compatibility
    async def collect_data(self, chat_id: str, research_query: str) -> Dict[str, Any]:
        task = A2ATask(
            task_id=f"legacy_{chat_id}",
            from_agent="system",
            to_agent="centurion",
            task_type="search",
            parameters={"research_query": research_query},
            conversation_context=[],
            created_at=datetime.now().isoformat(),
            chat_id=chat_id
        )
        
        response = await self.receive_a2a_task(task)
        return response.response_data.get("collected_data", {"sources": [], "citations": []})