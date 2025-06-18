import os
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from services.state_manager import StateManager
from services.adk_communication import A2ATask, A2AResponse
from agents.base_adk_agent import BaseADKAgent

class ConsulADKAgent(BaseADKAgent):
    """Strategic mission planner with simplified clarification handling"""

    def __init__(self, state_manager: StateManager, api_key: Optional[str] = None):
        super().__init__("consul", state_manager, api_key)
        self.conversations = {}
        
        if not api_key:
            raise ValueError("CONSUL requires Gemini API key for conversational planning")

    def _get_agent_personality(self) -> str:
        return """a strategic mission planner and conversation coordinator. You excel at understanding research requirements, 
        creating detailed mission plans with specific research questions, and providing intelligent clarifications to other agents."""

    async def _execute_agent_task(self, task: A2ATask) -> Dict[str, Any]:
        """Execute CONSUL-specific tasks through A2A interface"""
        task_type = task.task_type
        parameters = task.parameters
        chat_id = task.chat_id
        
        if task_type == "coordinate_mission":
            return await self._coordinate_research_mission(parameters, chat_id)
        elif task_type == "plan_mission":
            return await self._create_mission_plan(parameters, chat_id)
        elif task_type == "generate_research_questions":
            return await self._generate_research_questions(parameters, chat_id)
        elif task_type == "provide_clarification":
            return await self._provide_smart_clarification(parameters, chat_id)
        elif task_type == "handle_user_conversation":
            return await self._handle_user_conversation(parameters, chat_id)
        else:
            return {
                "status": "completed",
                "result": f"CONSUL processed {task_type} task",
                "summary": "Task completed successfully"
            }

    async def receive_a2a_task(self, task: A2ATask) -> A2AResponse:
        """Handle A2A tasks with simplified clarification flow"""
        try:
            # Log task receipt
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id,
                from_agent=task.from_agent.upper(),
                to_agent="CONSUL",
                message=f"Task request: {task.task_type}",
                conversation_type="task_request"
            )
            
            # Execute the task
            result = await self._execute_agent_task(task)
            
            # Send response back to requesting agent
            completion_message = result.get("summary", f"Task {task.task_type} completed")
            
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id,
                from_agent="CONSUL",
                to_agent=task.from_agent.upper(),
                message=completion_message,
                conversation_type="task_completion"
            )
            
            return A2AResponse(
                task_id=task.task_id,
                status="completed",
                response_data=result,
                conversation_message=completion_message,
                artifacts=result.get("artifacts", []),
                created_at=task.created_at
            )
            
        except Exception as e:
            error_message = f"Error processing task: {str(e)}"
            
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id,
                from_agent="CONSUL",
                to_agent=task.from_agent.upper(),
                message=error_message,
                conversation_type="error"
            )
            
            return A2AResponse(
                task_id=task.task_id,
                status="error",
                response_data={"error": str(e)},
                conversation_message=error_message,
                artifacts=[],
                created_at=task.created_at
            )

    async def _provide_smart_clarification(self, parameters: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        """Provide smart clarifications based on mission context - SIMPLIFIED"""
        
        original_task = parameters.get("original_task", {})
        agent_questions = parameters.get("agent_questions", [])
        task_type = parameters.get("task_type", "")
        requesting_agent = parameters.get("from_agent", "UNKNOWN")
        
        print(f"CONSUL: Providing clarifications for {requesting_agent}")
        print(f"CONSUL: Questions: {agent_questions}")
        
        await self.state_manager.add_agent_operation(
            chat_id=chat_id,
            agent="CONSUL",
            operation_type="analyzing",
            title="Providing Clarifications",
            details=f"Answering {len(agent_questions)} questions from {requesting_agent}",
            status="active",
            progress=50
        )
        
        try:
            # Get mission context from conversation state
            conv = self.conversations.get(chat_id, {})
            mission_plan = conv.get("mission_plan", {})
            mission_title = mission_plan.get("mission_title", "")
            
            # Smart contextual answers based on mission and question content
            clarifications = {}
            
            for i, question in enumerate(agent_questions):
                answer = self._generate_smart_answer(question, mission_title, original_task, requesting_agent)
                clarifications[f"question_{i+1}"] = answer
                
                # Send immediate clarification to agent
                await self.state_manager.add_agent_conversation(
                    chat_id=chat_id,
                    from_agent="CONSUL",
                    to_agent=requesting_agent.upper(),
                    message=f"Clarification: {answer}",
                    conversation_type="clarification_response"
                )
            
            await self.state_manager.add_agent_operation(
                chat_id=chat_id,
                agent="CONSUL",
                operation_type="analyzing",
                title="Clarifications Complete",
                details=f"Provided {len(agent_questions)} clarifications",
                status="completed",
                progress=100
            )
            
            return {
                "status": "completed",
                "clarifications": clarifications,
                "summary": f"Provided clarifications for {requesting_agent}"
            }
            
        except Exception as e:
            await self.state_manager.add_agent_operation(
                chat_id=chat_id,
                agent="CONSUL",
                operation_type="analyzing",
                title="Clarification Error",
                details=f"Failed to provide clarifications: {str(e)}",
                status="error",
                progress=0
            )
            raise

    def _generate_smart_answer(self, question: str, mission_title: str, original_task: Dict[str, Any], requesting_agent: str) -> str:
        """Generate smart contextual answers for ANY research topic"""
        
        question_lower = question.lower()
        
        # Handle clarification requests based on question type, not hardcoded topics
        if any(word in question_lower for word in ["selected", "major", "key", "which", "what are", "list"]):
            return (f"Use the key examples most relevant to {mission_title}. Base your selection on "
                   f"the criteria established in previous research questions. Focus on items with "
                   f"significant impact and clear relevance to the research objectives.")
        
        elif "criteria" in question_lower:
            return (f"Apply the criteria established in the previous research. Use consistent standards "
                   f"to evaluate relevance, significance, and impact related to {mission_title}.")
        
        elif "scope" in question_lower or "how much" in question_lower or "depth" in question_lower:
            return (f"Provide comprehensive coverage of {mission_title}. Include multiple authoritative "
                   f"sources, different perspectives, and sufficient detail for thorough analysis.")
        
        elif "sources" in question_lower or "where" in question_lower or "what type" in question_lower:
            return (f"Prioritize authoritative sources relevant to {mission_title}: academic publications, "
                   f"government data, industry reports, expert analysis, and credible institutions.")
        
        elif "format" in question_lower or "structure" in question_lower or "how to" in question_lower:
            return (f"Use clear, professional format appropriate for {mission_title} research. "
                   f"Include proper citations, evidence-based analysis, and logical organization.")
        
        elif "focus" in question_lower or "prioritize" in question_lower or "emphasis" in question_lower:
            return (f"Focus on aspects most relevant to {mission_title} and the specific research "
                   f"objectives outlined in the mission plan. Prioritize quality and relevance.")
        
        elif "timeline" in question_lower or "when" in question_lower:
            return (f"Use appropriate timeframes relevant to {mission_title}. Consider both "
                   f"historical context and current developments as applicable.")
        
        elif "approach" in question_lower or "methodology" in question_lower:
            return (f"Apply systematic research methodology appropriate for {mission_title}. "
                   f"Use evidence-based analysis and maintain objectivity throughout.")
        
        # Default intelligent response for any research topic
        return (f"Apply best research practices for {mission_title}. Use authoritative sources, "
               f"maintain focus on the specific objectives, and ensure comprehensive coverage "
               f"of the key aspects identified in the mission plan.")

    async def _generate_research_questions(self, parameters: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        """Generate specific research questions for question-driven workflow"""
        research_topic = parameters.get("research_focus", parameters.get("research_query", ""))
        mission_plan = parameters.get("mission_plan", {})
        
        await self.state_manager.add_agent_operation(
            chat_id=chat_id,
            agent="CONSUL",
            operation_type="planning",
            title="Research Question Generation",
            details=f"Creating research questions for: {research_topic}",
            status="active",
            progress=25
        )
        
        try:
            questions_prompt = self._build_questions_prompt(research_topic, mission_plan)
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(questions_prompt)
            questions_text = response.text
            
            research_questions = self._parse_research_questions(questions_text, research_topic)
            
            await self.state_manager.add_agent_operation(
                chat_id=chat_id,
                agent="CONSUL",
                operation_type="composing",
                title="Questions Ready",
                details=f"Generated {len(research_questions)} research questions",
                status="completed",
                progress=100
            )
            
            return {
                "status": "completed",
                "research_questions": research_questions,
                "question_count": len(research_questions),
                "summary": f"Generated {len(research_questions)} research questions for: {research_topic}"
            }
            
        except Exception as e:
            await self.state_manager.add_agent_operation(
                chat_id=chat_id,
                agent="CONSUL",
                operation_type="planning",
                title="Question Generation Error",
                details=f"Failed to generate questions: {str(e)}",
                status="error",
                progress=0
            )
            raise

    def _build_questions_prompt(self, research_topic: str, mission_plan: Dict[str, Any]) -> str:
        """Build prompt for generating research questions"""
        objectives = mission_plan.get("objectives", [])
        objectives_text = "\n".join(f"- {obj}" for obj in objectives) if objectives else "No specific objectives provided"
        
        return f"""As CONSUL, create specific, focused research questions for: {research_topic}

Mission Objectives:
{objectives_text}

Create 5-8 specific research questions that:
1. Cover different aspects of the topic comprehensively
2. Are answerable through research and data collection
3. Build upon each other logically
4. Enable creation of a comprehensive final report

Categories to consider:
- Current State: What is the current situation/status?
- Key Players: Who are the main stakeholders/companies/organizations?
- Trends & Developments: What are the latest trends, changes, or innovations?
- Challenges & Opportunities: What are the main problems and potential solutions?
- Market/Economic Impact: What are the financial or market implications?
- Future Outlook: What does the future look like for this topic?

Format as JSON:
{{
    "research_questions": [
        {{
            "question": "Specific, focused research question",
            "category": "current_state|key_players|trends|challenges|market_impact|future_outlook",
            "priority": 1-8,
            "context": "Brief context for why this question is important"
        }}
    ]
}}"""

    def _parse_research_questions(self, questions_text: str, research_topic: str) -> List[Dict[str, Any]]:
        """Parse research questions from Gemini response"""
        try:
            start_idx = questions_text.find('{')
            end_idx = questions_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = questions_text[start_idx:end_idx + 1]
                parsed = json.loads(json_str)
                questions = parsed.get("research_questions", [])
                
                validated_questions = []
                for i, q in enumerate(questions):
                    if isinstance(q, dict) and q.get("question"):
                        validated_questions.append({
                            "question": q.get("question", ""),
                            "category": q.get("category", "general"),
                            "priority": q.get("priority", i + 1),
                            "context": q.get("context", "")
                        })
                
                if validated_questions:
                    return validated_questions
            
            return self._extract_questions_manually(questions_text, research_topic)
                
        except Exception as e:
            print(f"CONSUL: Failed to parse research questions: {e}")
            return self._generate_default_questions(research_topic)

    def _extract_questions_manually(self, text: str, research_topic: str) -> List[Dict[str, Any]]:
        """Extract questions manually from text if JSON parsing fails"""
        questions = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line and '?' in line:
                clean_line = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
                if clean_line and len(clean_line) > 10:
                    questions.append({
                        "question": clean_line,
                        "category": self._categorize_question(clean_line),
                        "priority": i + 1,
                        "context": f"Research question for {research_topic}"
                    })
        
        return questions[:8] if len(questions) >= 3 else self._generate_default_questions(research_topic)

    def _categorize_question(self, question: str) -> str:
        """Categorize a question based on keywords"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["current", "status", "state", "today", "now"]):
            return "current_state"
        elif any(word in question_lower for word in ["who", "companies", "organizations", "players", "leaders"]):
            return "key_players"
        elif any(word in question_lower for word in ["trends", "developments", "changes", "innovations"]):
            return "trends"
        elif any(word in question_lower for word in ["challenges", "problems", "opportunities", "solutions"]):
            return "challenges"
        elif any(word in question_lower for word in ["market", "economic", "financial", "cost", "revenue"]):
            return "market_impact"
        elif any(word in question_lower for word in ["future", "outlook", "forecast", "prediction", "will"]):
            return "future_outlook"
        return "general"

    def _generate_default_questions(self, research_topic: str) -> List[Dict[str, Any]]:
        """Generate default research questions when AI fails"""
        questions = [
            {"question": f"What is the current state of {research_topic}?", "category": "current_state"},
            {"question": f"Who are the key players in {research_topic}?", "category": "key_players"},
            {"question": f"What are the latest trends in {research_topic}?", "category": "trends"},
            {"question": f"What challenges and opportunities exist in {research_topic}?", "category": "challenges"},
            {"question": f"What is the market impact of {research_topic}?", "category": "market_impact"},
            {"question": f"What does the future hold for {research_topic}?", "category": "future_outlook"}
        ]
        
        for i, q in enumerate(questions):
            q["priority"] = i + 1
            q["context"] = f"Research question for {research_topic}"
        
        return questions

    async def _coordinate_research_mission(self, parameters: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        """Coordinate the research mission and prepare for agent collaboration"""
        research_query = parameters.get("research_query", parameters.get("query", ""))
        
        await self.state_manager.add_agent_operation(
            chat_id=chat_id,
            agent="CONSUL",
            operation_type="planning",
            title="Mission Coordination",
            details=f"Coordinating research mission: {research_query}",
            status="active",
            progress=50
        )
        
        # Get mission plan from conversation state if available
        conv = self.conversations.get(chat_id, {})
        mission_plan = conv.get("mission_plan")
        research_questions = conv.get("research_questions")
        
        await self.state_manager.add_agent_operation(
            chat_id=chat_id,
            agent="CONSUL",
            operation_type="planning",
            title="Coordination Complete",
            details="Ready to execute question-driven research",
            status="completed",
            progress=100
        )
        
        return {
            "status": "completed",
            "research_query": research_query,
            "mission_plan": mission_plan,
            "research_questions": research_questions,
            "workflow_type": "question_driven",
            "coordination_complete": True,
            "summary": f"Mission coordination complete for: {research_query}"
        }

    async def _create_mission_plan(self, parameters: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        """Create a detailed mission plan using Gemini AI"""
        topic = parameters.get("topic", parameters.get("research_query", ""))
        user_requirements = parameters.get("requirements", "")
        
        await self.state_manager.add_agent_operation(
            chat_id=chat_id,
            agent="CONSUL",
            operation_type="planning",
            title="Mission Planning",
            details=f"Creating detailed plan for: {topic}",
            status="active",
            progress=50
        )
        
        try:
            plan_prompt = f"""As CONSUL, create a detailed research mission plan for: {topic}
            
User requirements: {user_requirements}

Create a comprehensive plan with:
1. Mission title
2. Specific objectives (3-4 clear goals)
3. Research approach (question-driven methodology)
4. Deliverable format description

Format as JSON:
{{
    "mission_title": "Title",
    "objectives": ["obj1", "obj2", "obj3"],
    "research_approach": "question-driven research methodology",
    "deliverable_format": "description"
}}"""
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(plan_prompt)
            plan_text = response.text
            
            mission_plan = self._parse_mission_plan(plan_text, topic)
            
            await self.state_manager.add_agent_operation(
                chat_id=chat_id,
                agent="CONSUL",
                operation_type="composing",
                title="Mission Plan Complete",
                details=f"Plan ready: {mission_plan['mission_title']}",
                status="completed",
                progress=100
            )
            
            return {
                "status": "completed",
                "mission_plan": mission_plan,
                "summary": f"Mission plan created for: {topic}"
            }
            
        except Exception as e:
            await self.state_manager.add_agent_operation(
                chat_id=chat_id,
                agent="CONSUL",
                operation_type="planning",
                title="Planning Error",
                details=f"Plan creation failed: {str(e)}",
                status="error",
                progress=0
            )
            raise

    def _parse_mission_plan(self, plan_text: str, topic: str) -> Dict[str, Any]:
        """Parse mission plan from Gemini response"""
        try:
            start_idx = plan_text.find('{')
            end_idx = plan_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = plan_text[start_idx:end_idx + 1]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"CONSUL: Failed to parse mission plan: {e}")
            return {
                "mission_title": f"Question-Driven Research: {topic}",
                "objectives": [
                    f"Generate focused research questions about {topic}",
                    "Systematically collect data for each question",
                    "Analyze all findings to extract key insights",
                    "Synthesize results into comprehensive report"
                ],
                "research_approach": "Question-driven methodology with targeted data collection and comprehensive analysis",
                "deliverable_format": "Comprehensive research report organized by research questions and findings"
            }

    def _format_mission_plan_for_user(self, mission_plan: Dict[str, Any], research_questions: List[Dict[str, Any]]) -> str:
        """Format mission plan in a user-friendly way"""
        if not mission_plan:
            return "Mission plan not available."
        
        title = mission_plan.get("mission_title", "Research Mission")
        objectives = mission_plan.get("objectives", [])
        approach = mission_plan.get("research_approach", "")
        deliverable = mission_plan.get("deliverable_format", "")
        
        # Format objectives
        objectives_text = ""
        if objectives:
            objectives_text = "**Objectives:**\n"
            for i, obj in enumerate(objectives, 1):
                objectives_text += f"*   {obj}\n"
        
        # Format research questions
        questions_text = ""
        if research_questions:
            questions_text = "\n**Here are some sample research questions to guide our investigation:**\n\n"
            for q in research_questions:
                question = q.get("question", "") if isinstance(q, dict) else str(q)
                category = q.get("category", "General") if isinstance(q, dict) else "General"
                priority = q.get("priority", 1) if isinstance(q, dict) else 1
                context = q.get("context", "") if isinstance(q, dict) else ""
                
                questions_text += f"*   **Question:** {question} \n"
                questions_text += f"    **Category:** {category.replace('_', ' ').title()}\n"
                questions_text += f"    **Priority:** {priority}\n"
                if context:
                    questions_text += f"    **Context:** {context}\n"
                questions_text += "\n"
        
        return f"""**Mission Title:** {title}

{objectives_text}
**Research Approach:**
{approach}

**Deliverable Format:**
{deliverable}
{questions_text}"""

    # MAIN CONVERSATION HANDLER
    async def handle_user_message(self, chat_id: str, user_message: str) -> Dict[str, Any]:
        """Main conversational handler for user interactions"""
        await self.state_manager.add_agent_operation(
            chat_id=chat_id,
            agent="CONSUL",
            operation_type="analyzing",
            title="Processing Request",
            details="Understanding user requirements",
            status="active",
            progress=50
        )
        
        # Get or create conversation context
        if chat_id not in self.conversations:
            self.conversations[chat_id] = {
                "messages": [],
                "mission_plan": None,
                "research_questions": None,
                "plan_ready": False,
                "mission_approved": False
            }
        
        conv = self.conversations[chat_id]
        conv["messages"].append({"role": "user", "content": user_message})
        
        response = await self._generate_conversational_response(chat_id, user_message, conv)
        conv["messages"].append({"role": "assistant", "content": response["message"]})
        
        # Update conversation state
        if response.get("mission_plan"):
            conv["mission_plan"] = response["mission_plan"]
        if response.get("research_questions"):
            conv["research_questions"] = response["research_questions"]
        if response.get("action") == "ready_for_mission":
            conv["mission_approved"] = True
            conv["plan_ready"] = True
        
        await self.state_manager.add_agent_operation(
            chat_id=chat_id,
            agent="CONSUL",
            operation_type="analyzing",
            title="Request Analysis Complete",
            details=f"Status: {'Approved' if conv.get('mission_approved') else 'Planning'}",
            status="completed",
            progress=100
        )
        
        # Send response to frontend
        await self.state_manager._send_websocket_message(chat_id, {
            "event": "consul_response",
            "agent": "CONSUL",
            "message": response.get("message", ""),
            "requires_response": response.get("requires_response", False),
            "mission_plan": conv.get("mission_plan"),
            "research_questions": conv.get("research_questions"),
            "status": response.get("status"),
            "action": response.get("action"),
            "ready_to_execute": conv.get("mission_approved", False)
        })
        
        return response

    async def _generate_conversational_response(self, chat_id: str, user_message: str, conv: Dict) -> Dict[str, Any]:
        """Generate contextual, conversational response"""
        try:
            conversation_prompt = self._build_conversation_prompt(user_message, conv)
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(conversation_prompt)
            response_text = response.text
            
            if not response_text:
                raise ValueError("Empty response from Gemini")
            
            parsed_response = self._parse_consul_response(response_text)
            
            # Handle response types and update conversation state
            if parsed_response.get("action") == "ready_for_mission":
                conv["plan_ready"] = True
                if conv.get("mission_plan") and not parsed_response.get("mission_plan"):
                    parsed_response["mission_plan"] = conv["mission_plan"]
                if conv.get("research_questions") and not parsed_response.get("research_questions"):
                    parsed_response["research_questions"] = conv["research_questions"]
                parsed_response["status"] = "mission_approved"
                parsed_response["ready_to_execute"] = True
                
            # Store mission data in conversation state
            if parsed_response.get("mission_plan"):
                conv["mission_plan"] = parsed_response["mission_plan"]
            if parsed_response.get("research_questions"):
                conv["research_questions"] = parsed_response["research_questions"]
                
            return parsed_response
            
        except Exception as e:
            print(f"CONSUL: Error in conversational response: {e}")
            return {
                "message": "I'm here to help you plan your research mission. What would you like to explore?",
                "action": "continue_conversation",
                "requires_response": True,
                "reasoning": f"Error: {str(e)}"
            }

    def _build_conversation_prompt(self, current_message: str, conv: Dict) -> str:
        """Build conversation prompt for Gemini"""
        history = ""
        for msg in conv["messages"][-10:]:
            role = "User" if msg["role"] == "user" else "Consul"
            history += f"{role}: {msg['content']}\n"
        
        mission_context = ""
        if conv.get("mission_plan") and conv.get("research_questions"):
            plan = conv["mission_plan"]
            if conv.get("mission_approved"):
                mission_context = f"CONTEXT: Mission '{plan.get('mission_title', 'Research Mission')}' is APPROVED and ready for execution."
            elif conv.get("plan_ready"):
                mission_context = f"CONTEXT: Mission '{plan.get('mission_title', 'Research Mission')}' is ready for approval."
            else:
                mission_context = f"CONTEXT: Working on mission plan for '{plan.get('mission_title', 'Research Mission')}'."

        return f"""You are CONSUL, an intelligent research mission planner. You create detailed mission plans with specific research questions.

CONVERSATION HISTORY:
{history}

CURRENT MESSAGE:
User: {current_message}

{mission_context}

INSTRUCTIONS:
- Handle greetings naturally ("Hi" -> "Hello! I'm CONSUL, your research mission planner. What would you like to research?")
- For research requests, create detailed plans AND research questions
- If user approves a plan, set action to "ready_for_mission"
- Remember context from previous messages
- Present plans in readable format, not raw JSON

Respond with JSON:
{{
    "message": "Your conversational response (formatted for users, not raw JSON)",
    "action": "continue_conversation|clarify_requirements|ready_for_mission",
    "mission_plan": {{"mission_title": "...", "objectives": [...], "research_approach": "...", "deliverable_format": "..."}},
    "research_questions": [{{"question": "...", "category": "...", "priority": 1, "context": "..."}}],
    "reasoning": "Brief explanation"
}}"""

    def _parse_consul_response(self, response_text: str) -> Dict[str, Any]:
        """Parse CONSUL's conversational response"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx + 1]
                parsed = json.loads(json_str)
                
                # Format mission plans for users instead of showing raw JSON
                if parsed.get("mission_plan") and parsed.get("research_questions"):
                    formatted_plan = self._format_mission_plan_for_user(
                        parsed["mission_plan"], 
                        parsed["research_questions"]
                    )
                    # Replace raw JSON message with formatted plan
                    if "mission_title" in str(parsed.get("message", "")):
                        parsed["message"] = f"I can create a research plan focused on {parsed['mission_plan'].get('mission_title', 'your topic')}. Here's a draft plan:\n\n{formatted_plan}\n\nDo you approve this mission plan? Would you like to refine it in any way?"
                
                # Ensure required fields
                if "message" not in parsed:
                    parsed["message"] = "I'm here to help you plan your research mission."
                if "action" not in parsed:
                    parsed["action"] = "continue_conversation"
                    
                return parsed
            else:
                return {
                    "message": response_text.strip(),
                    "action": "continue_conversation"
                }
                
        except Exception as e:
            print(f"CONSUL: Failed to parse response: {e}")
            return {
                "message": "I'm here to help you plan your research mission. What would you like to explore?",
                "action": "continue_conversation"
            }