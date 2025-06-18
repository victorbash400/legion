# agents/adk_augur.py - AUGUR generates ACTUAL content with citations

import google.generativeai as genai
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from services.state_manager import StateManager
from services.adk_communication import A2ATask, A2AResponse
from agents.base_adk_agent import BaseADKAgent

class AugurADKAgent(BaseADKAgent):
    """
    AUGUR agent - analysis specialist that processes data and generates ACTUAL deliverable content with citations
    """

    def __init__(self, state_manager: StateManager, api_key: Optional[str] = None):
        super().__init__("augur", state_manager, api_key)
        print("AUGUR: Initialized with Google Generative AI SDK for full content generation")

    def _get_agent_personality(self) -> str:
        """Return AUGUR's personality for conversation prompts"""
        return """an analytical specialist and content generation expert. You excel at finding patterns in data, 
        extracting key insights, and creating comprehensive, ready-to-publish documents. You analyze research data 
        and generate complete content for documents, spreadsheets, and presentations."""

    async def _execute_agent_task(self, task: A2ATask) -> Dict[str, Any]:
        """Execute AUGUR-specific tasks through A2A interface"""
        return await self._execute_task(task)

    async def receive_a2a_task(self, task: A2ATask) -> A2AResponse:
        """Process analysis tasks and generate complete content"""
        print(f"AUGUR: Received A2A task from {task.from_agent.upper()}: {task.task_type}")
        
        try:
            # Log task receipt
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id,
                from_agent=task.from_agent.upper(),
                to_agent="AUGUR",
                message=f"Requesting data analysis and content generation: {task.task_type}",
                conversation_type="task_assignment"
            )
            
            # Acknowledge and proceed immediately
            ack_message = f"Understood, {task.from_agent.upper()}. I'll analyze the data and generate complete deliverable content."
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id,
                from_agent="AUGUR",
                to_agent=task.from_agent.upper(),
                message=ack_message,
                conversation_type="task_acknowledgment"
            )
            
            # Execute the task
            result = await self._execute_task(task)
            
            # Send completion message
            deliverable_count = len(result.get("deliverables", []))
            completion_msg = f"Analysis complete! Generated {deliverable_count} complete deliverable(s) ready for publication."
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id,
                from_agent="AUGUR",
                to_agent=task.from_agent.upper(),
                message=completion_msg,
                conversation_type="task_completion"
            )
            
            return A2AResponse(
                task_id=task.task_id,
                status="completed",
                response_data=result,
                conversation_message=completion_msg,
                artifacts=result.get("artifacts", []),
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            error_msg = f"Content generation failed: {str(e)}"
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id,
                from_agent="AUGUR",
                to_agent=task.from_agent.upper(),
                message=error_msg,
                conversation_type="task_error"
            )
            
            return A2AResponse(
                task_id=task.task_id,
                status="error",
                response_data={"error": str(e)},
                conversation_message=error_msg,
                artifacts=[],
                created_at=datetime.now().isoformat()
            )

    async def _execute_task(self, task: A2ATask) -> Dict[str, Any]:
        """Execute the analysis task and generate complete content"""
        
        # Start operation tracking
        operation_id = await self.state_manager.add_agent_operation(
            chat_id=task.chat_id,
            agent="AUGUR",
            operation_type="content_generation",
            title="Analyzing data and generating complete deliverables",
            details="Processing research data and creating publication-ready content",
            status="active",
            progress=0
        )
        
        try:
            # Debug: Log what we're receiving
            print(f"AUGUR DEBUG: Task parameters keys: {task.parameters.keys()}")
            print(f"AUGUR DEBUG: Task parameters: {json.dumps(task.parameters, indent=2)[:500]}...")
            
            # Handle different data structures
            data = {}
            citations = []
            
            # Check if this is the all_collected_data structure from orchestrator
            if "all_collected_data" in task.parameters:
                # Merge all collected data from multiple questions
                all_sources = []
                all_citations = []
                
                for question_data in task.parameters["all_collected_data"]:
                    q_data = question_data.get("data", {})
                    
                    # Check if this question had successful data collection
                    if q_data.get("status") == "completed" and "collected_data" in q_data:
                        collected = q_data["collected_data"]
                        if "sources" in collected:
                            all_sources.extend(collected["sources"])
                        if "citations" in collected:
                            all_citations.extend(collected["citations"])
                    elif q_data.get("status") == "error":
                        print(f"AUGUR DEBUG: Question had error: {q_data.get('error')}")
                
                # Create merged data structure
                data = {
                    "sources": all_sources,
                    "citations": all_citations,
                    "query": task.parameters.get("research_focus", "Research Analysis")
                }
                citations = all_citations
                
            else:
                # Original single data structure
                data = task.parameters.get("collected_data") or task.parameters.get("data") or {}
                citations = data.get("citations", [])
            
            # Debug: Log what data we extracted
            print(f"AUGUR DEBUG: Extracted data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
            print(f"AUGUR DEBUG: Number of sources: {len(data.get('sources', [])) if isinstance(data, dict) else 0}")
            print(f"AUGUR DEBUG: Number of citations: {len(citations)}")
            
            # Update progress
            await self.state_manager.update_agent_operation(
                chat_id=task.chat_id,
                operation_id=operation_id,
                progress=20,
                details="Analyzing research data..."
            )
            
            # Determine formats needed
            formats = self._determine_formats(task, data)
            
            # Update progress
            await self.state_manager.update_agent_operation(
                chat_id=task.chat_id,
                operation_id=operation_id,
                progress=40,
                details=f"Generating content for {len(formats)} format(s)..."
            )
            
            # Generate complete content for each format
            deliverables = []
            for i, format_type in enumerate(formats):
                progress = 40 + (i + 1) * (50 / len(formats))
                await self.state_manager.update_agent_operation(
                    chat_id=task.chat_id,
                    operation_id=operation_id,
                    progress=int(progress),
                    details=f"Generating {format_type} content..."
                )
                
                deliverable = await self._generate_complete_deliverable(format_type, data, task, citations)
                if deliverable:
                    deliverables.append(deliverable)
            
            # Complete operation
            await self.state_manager.update_agent_operation(
                chat_id=task.chat_id,
                operation_id=operation_id,
                status="completed",
                progress=100,
                details=f"Generated {len(deliverables)} complete deliverable(s)"
            )
            
            # Return in format SCRIBE expects
            return {
                "status": "completed",
                "deliverables": deliverables,
                "deliverable_instructions": {
                    "primary_format": formats[0] if formats else "docs",
                    "additional_formats": formats[1:] if len(formats) > 1 else []
                },
                "analysis_results": {
                    "deliverables": deliverables
                },
                "summary": f"Generated {len(deliverables)} complete deliverable(s)"
            }
            
        except Exception as e:
            await self.state_manager.update_agent_operation(
                chat_id=task.chat_id,
                operation_id=operation_id,
                status="error",
                details=f"Content generation failed: {str(e)}"
            )
            raise

    def _determine_formats(self, task: A2ATask, data: Any) -> List[str]:
        """Determine what formats to generate based on request and data"""
        formats = []
        
        # Check if specific format requested
        params = task.parameters
        mission_context = params.get("mission_context", {})
        mission_plan = mission_context.get("mission_plan", {})
        
        # Check for explicit format requests
        research_query = (params.get("question_context") or 
                         params.get("research_query") or 
                         params.get("query") or "").lower()
        
        # Check various indicators
        wants_presentation = any(word in research_query for word in ['presentation', 'present', 'slides', 'deck'])
        wants_spreadsheet = any(word in research_query for word in ['spreadsheet', 'excel', 'data table', 'csv'])
        wants_document = any(word in research_query for word in ['report', 'document', 'analysis', 'paper'])
        
        # Mission plan format
        deliverable_format = mission_plan.get("deliverable_format", "").lower()
        
        # Determine formats
        if wants_presentation or "slide" in deliverable_format or "presentation" in deliverable_format:
            formats.append("slides")
        
        if wants_spreadsheet or "sheet" in deliverable_format or "spreadsheet" in deliverable_format:
            formats.append("sheets")
        
        if wants_document or "doc" in deliverable_format or not formats:
            formats.append("docs")
        
        # If data is very structured, also create spreadsheet
        if isinstance(data, dict) and "sources" in data and len(data["sources"]) > 5 and "sheets" not in formats:
            formats.append("sheets")
        
        return formats

    async def _generate_complete_deliverable(self, format_type: str, data: Any, task: A2ATask, citations: List[Dict]) -> Dict[str, Any]:
        """Generate complete, ready-to-publish content for the specified format"""
        
        # Extract context
        research_topic = self._extract_research_topic(task, data)
        content_text = self._prepare_content_for_analysis(data)
        
        if format_type == "docs":
            return await self._generate_document_content(content_text, research_topic, citations)
        elif format_type == "sheets":
            return await self._generate_spreadsheet_content(content_text, research_topic, citations)
        elif format_type == "slides":
            return await self._generate_presentation_content(content_text, research_topic, citations)
        
        return None

    def _extract_research_topic(self, task: A2ATask, data: Any) -> str:
        """Extract the research topic from task parameters"""
        params = task.parameters
        research_topic = (params.get("research_focus") or 
                         params.get("mission_title") or
                         params.get("question_context") or 
                         params.get("research_query") or 
                         params.get("query") or "")
        
        if not research_topic and isinstance(data, dict) and "query" in data:
            research_topic = data["query"]
        
        return research_topic or "Research Analysis"

    def _prepare_content_for_analysis(self, data: Any) -> str:
        """Prepare raw data for AI analysis"""
        if isinstance(data, dict) and "sources" in data and len(data["sources"]) > 0:
            # Handle CENTURION's research data
            content_parts = []
            for i, source in enumerate(data["sources"][:15]):  # Use more sources
                title = source.get('title', f'Source {i+1}')
                content = source.get('content', '')
                url = source.get('url', '')
                citation_index = source.get('citation_index', i+1)
                
                content_parts.append(f"""
SOURCE {i+1} [Citation {citation_index}]: {title}
URL: {url}
CONTENT:
{content}

---
""")
            return "\n".join(content_parts)
        else:
            # No sources available - prepare a message for the AI
            if isinstance(data, dict):
                query = data.get('query', 'Research topic')
                return f"""No research sources were found for the query: {query}
                
Please generate a comprehensive analysis based on your knowledge about this topic. 
Note that no external sources were available for citation."""
            else:
                return str(data)

    def _format_citations_section(self, citations: List[Dict]) -> str:
        """Format citations into a proper bibliography section"""
        if not citations:
            return ""
        
        citations_text = "\n\n## References\n\n"
        
        for citation in citations:
            index = citation.get('index', '')
            title = citation.get('title', 'Untitled')
            url = citation.get('url', '')
            date = citation.get('date', '')
            domain = citation.get('domain', '')
            
            # Format: [1] Title. Domain. Date. URL
            citation_line = f"[{index}] {title}"
            if domain:
                citation_line += f". {domain}"
            if date:
                citation_line += f". {date}"
            if url:
                citation_line += f". {url}"
            
            citations_text += citation_line + "\n\n"
        
        return citations_text

    async def _generate_document_content(self, content_text: str, research_topic: str, citations: List[Dict]) -> Dict[str, Any]:
        """Generate complete document content using AI with citations"""
        
        # Prepare citations reference for the AI
        citations_info = ""
        if citations:
            citations_info = "\n\nAvailable citations for reference:"
            for cite in citations:
                citations_info += f"\n[{cite['index']}] {cite['title']} - {cite['url']}"
        
        prompt = f"""You are creating a comprehensive professional document about: {research_topic}

Using this research data:
{content_text[:12000]}
{citations_info}

Generate a COMPLETE, PUBLICATION-READY report. This should be a deep, well-researched, and engaging long-form document of **at least 4000-6000 words**, designed for expert or public consumption. Think of this as a substantial piece that someone would spend 20-30 minutes reading thoroughly.

IMPORTANT: When referencing information from sources, include inline citations using [1], [2], etc. format that corresponds to the citation numbers provided above.

Critical Length Requirements:
- Each major section should be 800-1200 words minimum
- Include detailed subsections within major sections
- Expand on every key point with examples, context, and implications
- Use extensive data integration from the research sources WITH CITATIONS
- Add comparative analysis, historical context, and future implications where relevant

Instructions:
- **DO NOT** follow a fixed structure like "Executive Summary → Intro → Findings" unless it emerges naturally from the research
- Come up with a **specific, compelling title** that reflects the key insight or tension in the research
- Organize content into **clearly titled sections** that follow the natural logic and flow of the material
- Include as many **specific facts, figures, case examples, and citations from the research** as possible
- Include inline citations [1], [2], etc. when referencing source material
- Feel free to include subsections, quoted material, bold insights, or provocative statements where appropriate
- The tone should be professional but readable—avoid filler, corporate-speak, or generic phrasing
- Each section must be **multi-paragraph and information-rich**, not superficial summaries
- DO NOT include a References section - that will be added automatically

Length Enforcement:
- Target 5-8 major sections, each 600-1000+ words
- Use detailed explanations rather than bullet points
- Expand technical concepts with accessible explanations
- Include multiple perspectives and counterarguments where appropriate
- Weave in broader industry/societal context throughout

Output format (JSON):
{{
  "format": "docs",
  "title": "Compelling, Specific Report Title",
  "content": {{
    "sections": [
      {{
        "title": "Custom Section Title",
        "content": "Multiple comprehensive paragraphs of in-depth, analytical prose using extensive data and examples. Include citations like [1] when referencing sources. Each section should be substantial enough to stand alone as a meaningful analysis...",
        "formatting": "heading1"
      }},
      {{
        "title": "Next Section Title",
        "content": "More fully developed, data-driven analysis with detailed explanations [2], contextual information, and extensive use of research findings [3]...",
        "formatting": "heading1"
      }}
      // Add 5-8 sections minimum to develop the argument intelligently and comprehensively
    ]
  }}
}}
"""

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(prompt)
            
            # Parse response
            response_text = response.text.strip()
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Add citations section to the document
                if citations and result.get("format") == "docs":
                    citations_section = {
                        "title": "References",
                        "content": self._format_citations_section(citations),
                        "formatting": "heading1"
                    }
                    result["content"]["sections"].append(citations_section)
                
                return result
            else:
                # If JSON parsing fails, create structured content from response
                return self._create_doc_from_text(response_text, research_topic, citations)
                
        except Exception as e:
            print(f"AUGUR: Document generation error: {e}")
            # Generate using pure AI without JSON constraint
            return await self._generate_document_fallback(content_text, research_topic, citations)

    async def _generate_document_fallback(self, content_text: str, research_topic: str, citations: List[Dict]) -> Dict[str, Any]:
        """Fallback document generation without JSON constraints"""
        
        citations_info = ""
        if citations:
            citations_info = "\n\nCite sources using [1], [2], etc. based on these references:"
            for cite in citations:
                citations_info += f"\n[{cite['index']}] {cite['title']}"
        
        prompt = f"""Write a comprehensive professional report about: {research_topic}

Using this research data:
{content_text[:12000]}
{citations_info}

Create a detailed, thorough report with multiple sections. This should be a substantial document of 4000-6000 words minimum. 

Requirements:
- Each major section should be 800+ words with detailed analysis
- Include extensive use of specific data, quotes, and insights from the research
- Add inline citations [1], [2], etc. when referencing sources
- Elaborate on implications, context, and broader significance
- Use descriptive, analytical prose rather than brief summaries
- Integrate multiple perspectives and comprehensive coverage of the topic
- Think of this as a publication-quality piece that demonstrates deep expertise

Make it comprehensive, professional, and substantive enough for serious academic or business consumption."""

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(prompt)
            
            # Split into sections based on common headers
            content = response.text
            sections = []
            
            # Try to identify sections
            lines = content.split('\n')
            current_section = {"title": "Introduction", "content": "", "formatting": "heading1"}
            
            for line in lines:
                if line.strip() and (line.isupper() or line.strip().endswith(':') or 
                                   any(word in line.lower() for word in ['summary', 'introduction', 'findings', 
                                                                          'analysis', 'implications', 'recommendations', 
                                                                          'conclusion'])):
                    if current_section["content"]:
                        sections.append(current_section)
                    current_section = {"title": line.strip().rstrip(':'), "content": "", "formatting": "heading1"}
                else:
                    current_section["content"] += line + "\n"
            
            if current_section["content"]:
                sections.append(current_section)
            
            # Add citations section
            if citations:
                citations_section = {
                    "title": "References",
                    "content": self._format_citations_section(citations),
                    "formatting": "heading1"
                }
                sections.append(citations_section)
            
            return {
                "format": "docs",
                "title": f"{research_topic} - Comprehensive Analysis Report",
                "content": {"sections": sections}
            }
            
        except Exception as e:
            print(f"AUGUR: Fallback generation error: {e}")
            raise

    async def _generate_spreadsheet_content(self, content_text: str, research_topic: str, citations: List[Dict]) -> Dict[str, Any]:
        """Generate complete spreadsheet content using AI"""
        
        citations_info = ""
        if citations:
            citations_info = "\n\nInclude a Citations worksheet with these references:"
            for cite in citations:
                citations_info += f"\n[{cite['index']}] {cite['title']} - {cite['url']}"
        
        prompt = f"""You are creating a data-rich spreadsheet about: {research_topic}

Using this research data:
{content_text[:10000]}
{citations_info}

Generate COMPLETE spreadsheet content with multiple worksheets:

1. Create a specific, descriptive title
2. Design 3-5 worksheets with different data views:
   - Summary/Overview sheet with key metrics
   - Detailed findings with categorization
   - Comparative analysis or timeline data
   - Recommendations tracker or action items
   - Citations/References sheet (if citations provided)

For each worksheet, provide:
- Meaningful column headers
- At least 10-20 rows of ACTUAL data extracted/derived from the research
- Use specific numbers, dates, categories from the sources
- Include source references where applicable

Format as JSON:
{{
  "format": "sheets",
  "title": "Specific Spreadsheet Title",
  "content": {{
    "worksheets": [
      {{
        "name": "Overview",
        "data": [
          ["Metric", "Value", "Source", "Date", "Notes"],
          ["Specific metric 1", "Actual value", "Source [1]", "2024-01-15", "Relevant note"],
          // ... many more rows with REAL data
        ]
      }},
      {{
        "name": "Detailed Findings",
        "data": [
          ["Finding", "Category", "Impact", "Evidence", "Priority", "Citation"],
          ["Specific finding from research", "Technology", "High", "Quote or data", "1", "[1]"],
          // ... many more rows
        ]
      }},
      {{
        "name": "References",
        "data": [
          ["Index", "Title", "URL", "Date", "Type"],
          ["1", "Source title", "https://...", "2024-01-01", "Article"],
          // ... all citations
        ]
      }}
    ]
  }}
}}"""

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(prompt)
            
            # Parse response
            response_text = response.text.strip()
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Ensure citations worksheet exists if we have citations
                if citations and result.get("format") == "sheets":
                    has_citations_sheet = any(ws["name"].lower() in ["references", "citations"] 
                                            for ws in result["content"]["worksheets"])
                    
                    if not has_citations_sheet:
                        citations_data = [["Index", "Title", "URL", "Date", "Domain"]]
                        for cite in citations:
                            citations_data.append([
                                str(cite.get('index', '')),
                                cite.get('title', ''),
                                cite.get('url', ''),
                                cite.get('date', ''),
                                cite.get('domain', '')
                            ])
                        
                        result["content"]["worksheets"].append({
                            "name": "References",
                            "data": citations_data
                        })
                
                return result
            else:
                return await self._generate_spreadsheet_fallback(content_text, research_topic, citations)
                
        except Exception as e:
            print(f"AUGUR: Spreadsheet generation error: {e}")
            return await self._generate_spreadsheet_fallback(content_text, research_topic, citations)

    async def _generate_spreadsheet_fallback(self, content_text: str, research_topic: str, citations: List[Dict]) -> Dict[str, Any]:
        """Fallback spreadsheet generation"""
        
        prompt = f"""Create structured data tables about: {research_topic}

From this research:
{content_text[:8000]}

Generate multiple data tables with headers and rows. Extract specific facts, numbers, dates, and categories.
Create at least 3 different views of the data. Include citation references where applicable."""

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(prompt)
            
            # Try to extract tabular data from response
            content = response.text
            
            worksheets = [
                {
                    "name": "Key Findings",
                    "data": self._extract_table_from_text(content, "findings")
                },
                {
                    "name": "Data Summary", 
                    "data": self._extract_table_from_text(content, "summary")
                }
            ]
            
            # Add citations worksheet
            if citations:
                citations_data = [["Index", "Title", "URL", "Date", "Domain"]]
                for cite in citations:
                    citations_data.append([
                        str(cite.get('index', '')),
                        cite.get('title', ''),
                        cite.get('url', ''),
                        cite.get('date', ''),
                        cite.get('domain', '')
                    ])
                
                worksheets.append({
                    "name": "References",
                    "data": citations_data
                })
            
            # Create basic structure
            return {
                "format": "sheets",
                "title": f"{research_topic} - Data Analysis",
                "content": {"worksheets": worksheets}
            }
            
        except Exception as e:
            print(f"AUGUR: Spreadsheet fallback error: {e}")
            raise

    async def _generate_presentation_content(self, content_text: str, research_topic: str, citations: List[Dict]) -> Dict[str, Any]:
        """Generate complete presentation content using AI"""
        
        citations_info = ""
        if citations:
            citations_info = "\n\nInclude citation references [1], [2], etc. on slides and add a References slide at the end with:"
            for cite in citations:
                citations_info += f"\n[{cite['index']}] {cite['title']}"
        
        prompt = f"""You are creating an executive presentation about: {research_topic}

Using this research data:
{content_text[:10000]}
{citations_info}

Generate a complete, professional slide deck that tells a compelling story. Be flexible and creative with structure—do **not** follow a rigid template.

Instructions:
- Come up with a strong, specific presentation title
- Create 10–20 slides that together deliver a powerful narrative
- Use storytelling, data, and insight to keep the audience engaged
- Include citation references [1], [2] on slides when referencing sources
- Include recommendations or calls to action **only if they're meaningful**
- Not all presentations need a "problem/opportunity" or "recommendation" slide—only include what's impactful
- Highlight key findings, bold insights, implications, etc., as needed
- Add a References slide at the end if citations are provided

For each slide, include:
- Slide number
- A compelling slide title
- (Optional) subtitle for clarity or punch
- Bullet points with specific, relevant content (include citations)
- Speaker notes with context or explanation

Format the response as JSON:
{{
  "format": "slides",
  "title": "Generated Presentation Title",
  "content": {{
    "slides": [
      {{
        "number": 1,
        "title": "Slide Title",
        "subtitle": "Optional subtitle",
        "content": "• Bullet point 1\\n• Bullet point 2 [1]\\n• Data point [2]",
        "notes": "Presenter notes explaining visuals or intent"
      }},
      ...
      {{
        "number": 15,
        "title": "References",
        "subtitle": "",
        "content": "• [1] First source title\\n• [2] Second source title\\n• [3] Third source title",
        "notes": "Complete citations are provided in accompanying materials"
      }}
    ]
  }}
}}
"""

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(prompt)
            
            # Parse response
            response_text = response.text.strip()
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Ensure references slide exists if we have citations
                if citations and result.get("format") == "slides":
                    has_references_slide = any(slide["title"].lower() in ["references", "citations", "sources"] 
                                             for slide in result["content"]["slides"])
                    
                    if not has_references_slide:
                        citations_content = []
                        for cite in citations[:10]:  # Limit to 10 for slide readability
                            citations_content.append(f"• [{cite['index']}] {cite['title']}")
                        
                        result["content"]["slides"].append({
                            "number": len(result["content"]["slides"]) + 1,
                            "title": "References",
                            "subtitle": "",
                            "content": "\n".join(citations_content),
                            "notes": "Complete citations with URLs are provided in the accompanying document"
                        })
                
                return result
            else:
                return await self._generate_presentation_fallback(content_text, research_topic, citations)
                
        except Exception as e:
            print(f"AUGUR: Presentation generation error: {e}")
            return await self._generate_presentation_fallback(content_text, research_topic, citations)

    async def _generate_presentation_fallback(self, content_text: str, research_topic: str, citations: List[Dict]) -> Dict[str, Any]:
        """Fallback presentation generation"""
        
        prompt = f"""Create an executive presentation about: {research_topic}

From this research:
{content_text[:8000]}

Create content for a compelling, visually engaging slide deck (8–10 slides). Each slide should stand on its own with a clear message, but together they should tell a cohesive story.

Include citation references where applicable. Add a references slide if citations are provided.

Focus on:
- A strong opening slide (title + executive summary)
- Visually structured key findings (with charts, comparisons, or bold stats)
- Insightful analysis where it adds value
- Highlight unexpected patterns, contradictions, or bold takes
- Include recommendations or next steps only if relevant and impactful

Don't follow a rigid template—make the slides dynamic, high-impact, and presentation-ready."""

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(prompt)
            
            # Convert text response to slide structure
            content = response.text
            slides = []
            
            # Create basic slide structure from content
            sections = content.split('\n\n')
            slide_num = 1
            
            for section in sections[:12]:  # Max 12 slides
                if section.strip():
                    lines = section.strip().split('\n')
                    title = lines[0] if lines else f"Slide {slide_num}"
                    content_lines = '\n'.join([f"• {line}" for line in lines[1:5] if line.strip()])
                    
                    slides.append({
                        "number": slide_num,
                        "title": title,
                        "subtitle": "",
                        "content": content_lines,
                        "notes": '\n'.join(lines[5:]) if len(lines) > 5 else ""
                    })
                    slide_num += 1
            
            # Add references slide if citations provided
            if citations:
                citations_content = []
                for cite in citations[:10]:  # Limit to 10 for readability
                    citations_content.append(f"• [{cite['index']}] {cite['title']}")
                
                slides.append({
                    "number": slide_num,
                    "title": "References",
                    "subtitle": "",
                    "content": "\n".join(citations_content),
                    "notes": "Complete citations with URLs are provided in accompanying materials"
                })
            
            return {
                "format": "slides",
                "title": f"{research_topic} - Executive Presentation",
                "content": {"slides": slides}
            }
            
        except Exception as e:
            print(f"AUGUR: Presentation fallback error: {e}")
            raise

    def _extract_table_from_text(self, text: str, table_type: str) -> List[List[str]]:
        """Extract tabular data from text content"""
        rows = []
        
        if table_type == "findings":
            rows = [["Finding", "Category", "Impact", "Source", "Date"]]
            # Extract findings from text
            lines = text.split('\n')
            for i, line in enumerate(lines[:20]):
                if line.strip() and len(line.strip()) > 20:
                    rows.append([
                        line.strip()[:100],
                        "Analysis",
                        "High",
                        f"Research Data",
                        datetime.now().strftime("%Y-%m-%d")
                    ])
        else:
            rows = [["Item", "Description", "Value", "Status"]]
            lines = text.split('\n')
            for i, line in enumerate(lines[:15]):
                if line.strip():
                    rows.append([
                        f"Item {i+1}",
                        line.strip()[:100],
                        "Analyzed",
                        "Complete"
                    ])
        
        return rows

    def _create_doc_from_text(self, text: str, research_topic: str, citations: List[Dict]) -> Dict[str, Any]:
        """Create document structure from plain text with citations"""
        sections = []
        
        # Split text into paragraphs
        paragraphs = text.split('\n\n')
        current_section = {"title": "Overview", "content": "", "formatting": "heading1"}
        
        for para in paragraphs:
            if len(para.strip()) > 0:
                current_section["content"] += para + "\n\n"
                
                # Create new section every few paragraphs
                if len(current_section["content"]) > 1000:
                    sections.append(current_section)
                    current_section = {"title": f"Section {len(sections) + 1}", "content": "", "formatting": "heading1"}
        
        if current_section["content"]:
            sections.append(current_section)
        
        # Add citations section
        if citations:
            citations_section = {
                "title": "References",
                "content": self._format_citations_section(citations),
                "formatting": "heading1"
            }
            sections.append(citations_section)
        
        return {
            "format": "docs",
            "title": f"{research_topic} - Analysis Report",
            "content": {"sections": sections}
        }

    # Legacy compatibility methods - KEEP THESE
    async def analyze_data(self, chat_id: str, data: str) -> str:
        """Legacy method - maintained for compatibility"""
        task = A2ATask(
            task_id=f"legacy_{chat_id}_{datetime.now().timestamp()}",
            from_agent="system",
            to_agent="augur", 
            task_type="analyze_data",
            parameters={"data": data},
            conversation_context=[],
            created_at=datetime.now().isoformat(),
            chat_id=chat_id
        )
        
        response = await self.receive_a2a_task(task)
        deliverables = response.response_data.get("deliverables", [])
        if deliverables and deliverables[0].get("format") == "docs":
            sections = deliverables[0].get("content", {}).get("sections", [])
            return "\n\n".join([s.get("content", "") for s in sections])
        return "Analysis completed"

    async def process_data(self, chat_id: str, data: Any) -> str:
        """Legacy method - maintained for compatibility"""
        return await self.analyze_data(chat_id, str(data))