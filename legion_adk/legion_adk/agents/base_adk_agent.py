# agents/base_adk_agent.py

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

import google.generativeai as genai
print("base_adk_agent: Using google.generativeai SDK")

from services.adk_communication import A2ATask, A2AResponse, get_communication_manager

class BaseADKAgent(ABC):
    """
    Base class for all ADK agents with conversational A2A communication capabilities.
    Provides common functionality for agent-to-agent conversations powered by Gemini.
    """
    
    def __init__(self, agent_name: str, state_manager, api_key: Optional[str] = None):
        self.agent_name = agent_name
        self.state_manager = state_manager
        self.communication_manager = get_communication_manager(state_manager)
        
        # Initialize Gemini for conversations
        self.gemini_available = False
        
        if api_key:
            self._init_gemini(api_key)
    
    def _init_gemini(self, api_key: str):
        """Initialize Gemini client for conversational capabilities"""
        try:
            genai.configure(api_key=api_key)
            self.gemini_available = True
            print(f"{self.agent_name.upper()}: Initialized with Google Generative AI SDK")
        except Exception as e:
            print(f"{self.agent_name.upper()}: Failed to initialize Gemini: {e}")
    
    async def receive_a2a_task(self, task: A2ATask) -> A2AResponse:
        """
        Main A2A endpoint - receives tasks from other agents and processes them conversationally
        """
        print(f"{self.agent_name.upper()}: Received A2A task from {task.from_agent.upper()}")
        
        # Log the agent conversation in comms
        await self.state_manager.add_agent_conversation(
            chat_id=task.chat_id,
            from_agent=task.from_agent.upper(),
            to_agent=self.agent_name.upper(),
            message=f"Task request: {task.task_type}",
            conversation_type="task_request"
        )
        
        # Show task processing as operation
        await self.state_manager.add_agent_operation(
            chat_id=task.chat_id,
            agent=self.agent_name.upper(),
            operation_type="analyzing",
            title="Processing A2A Task",
            details=f"Analyzing {task.task_type} request from {task.from_agent.upper()}",
            status="active",
            progress=25,
            data={"task_type": task.task_type, "from_agent": task.from_agent}
        )
        
        try:
            # Generate conversational response to the task
            conversation_response = await self._generate_task_conversation(task)
            
            # Update operation progress
            await self.state_manager.add_agent_operation(
                chat_id=task.chat_id,
                agent=self.agent_name.upper(),
                operation_type="analyzing",
                title="Task Analysis Complete",
                details=f"Decision: {conversation_response.get('action', 'proceed')}",
                status="active",
                progress=50
            )
            
            # Process based on conversation decision
            if conversation_response.get("action") == "clarify":
                # Agent needs clarification
                await self.state_manager.add_agent_conversation(
                    chat_id=task.chat_id,
                    from_agent=self.agent_name.upper(),
                    to_agent=task.from_agent.upper(),
                    message=conversation_response.get("message", "Need clarification"),
                    conversation_type="clarification_request"
                )
                
                await self.communication_manager.request_clarification(
                    task.task_id,
                    conversation_response.get("questions", []),
                    task.chat_id
                )
                
                # Complete operation as needs clarification
                await self.state_manager.add_agent_operation(
                    chat_id=task.chat_id,
                    agent=self.agent_name.upper(),
                    operation_type="analyzing",
                    title="Clarification Requested",
                    details="Waiting for additional information",
                    status="paused",
                    progress=50,
                    data={"questions_asked": len(conversation_response.get("questions", []))}
                )
                
                return A2AResponse(
                    task_id=task.task_id,
                    status="needs_clarification",
                    response_data={"questions": conversation_response.get("questions", [])},
                    conversation_message=conversation_response.get("message", ""),
                    artifacts=[],
                    created_at=datetime.now().isoformat()
                )
                
            elif conversation_response.get("action") == "proceed":
                # Agent understands and will proceed
                await self.state_manager.add_agent_conversation(
                    chat_id=task.chat_id,
                    from_agent=self.agent_name.upper(),
                    to_agent=task.from_agent.upper(),
                    message=conversation_response.get("message", "Task accepted, proceeding"),
                    conversation_type="task_acceptance"
                )
                
                await self.communication_manager.send_agent_response(
                    task.task_id,
                    "in_progress", 
                    {"status": "accepted"},
                    conversation_response.get("message", ""),
                    []
                )
                
                # Update operation for task execution
                await self.state_manager.add_agent_operation(
                    chat_id=task.chat_id,
                    agent=self.agent_name.upper(),
                    operation_type="processing",
                    title=f"Executing {task.task_type}",
                    details="Running task execution logic",
                    status="active",
                    progress=75
                )
                
                # Execute the actual task
                task_result = await self._execute_agent_task(task)
                
                # Complete the operation
                await self.state_manager.add_agent_operation(
                    chat_id=task.chat_id,
                    agent=self.agent_name.upper(),
                    operation_type="processing",
                    title=f"Task Complete: {task.task_type}",
                    details=f"Successfully completed {task.task_type}",
                    status="completed",
                    progress=100,
                    data={"result_status": task_result.get("status", "completed")}
                )
                
                # Log completion conversation
                await self.state_manager.add_agent_conversation(
                    chat_id=task.chat_id,
                    from_agent=self.agent_name.upper(),
                    to_agent=task.from_agent.upper(),
                    message=f"Task completed: {task_result.get('summary', 'Task finished successfully')}",
                    conversation_type="task_completion"
                )
                
                # Send completion response
                return await self.communication_manager.send_agent_response(
                    task.task_id,
                    "completed",
                    task_result,
                    f"Task completed successfully. {task_result.get('summary', '')}",
                    task_result.get("artifacts", [])
                )
                
            else:
                # Agent declines or has issues
                await self.state_manager.add_agent_conversation(
                    chat_id=task.chat_id,
                    from_agent=self.agent_name.upper(),
                    to_agent=task.from_agent.upper(),
                    message=conversation_response.get("message", "Cannot process this task"),
                    conversation_type="task_decline"
                )
                
                # Mark operation as error
                await self.state_manager.add_agent_operation(
                    chat_id=task.chat_id,
                    agent=self.agent_name.upper(),
                    operation_type="analyzing",
                    title="Task Declined",
                    details="Unable to process the requested task",
                    status="error",
                    progress=0,
                    data={"decline_reason": conversation_response.get("reasoning", "Unknown")}
                )
                
                return A2AResponse(
                    task_id=task.task_id,
                    status="error",
                    response_data={"error": "Could not process task"},
                    conversation_message=conversation_response.get("message", "Unable to process this task"),
                    artifacts=[],
                    created_at=datetime.now().isoformat()
                )
                
        except Exception as e:
            print(f"{self.agent_name.upper()}: Error processing A2A task: {e}")
            
            # Log error conversation
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id,
                from_agent=self.agent_name.upper(),
                to_agent=task.from_agent.upper(),
                message=f"Error processing task: {str(e)}",
                conversation_type="error"
            )
            
            # Mark operation as failed
            await self.state_manager.add_agent_operation(
                chat_id=task.chat_id,
                agent=self.agent_name.upper(),
                operation_type="processing",
                title="Task Processing Error",
                details=f"Error: {str(e)}",
                status="error",
                progress=0,
                data={"error": str(e)}
            )
            
            return A2AResponse(
                task_id=task.task_id,
                status="error", 
                response_data={"error": str(e)},
                conversation_message=f"I encountered an error processing your request: {str(e)}",
                artifacts=[],
                created_at=datetime.now().isoformat()
            )
    
    async def _generate_task_conversation(self, task: A2ATask) -> Dict[str, Any]:
        """
        Generate conversational response to an incoming task using Gemini
        """
        if not self.gemini_available:
            return await self._fallback_task_conversation(task)
        
        # Build conversation prompt for task analysis
        conversation_prompt = self._build_task_conversation_prompt(task)
        
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await model.generate_content_async(conversation_prompt)
            response_text = response.text
            
            # Parse the response
            return self._parse_conversation_response(response_text)
        
        except Exception as e:
            print(f"{self.agent_name.upper()}: Gemini conversation failed: {e}")
            return await self._fallback_task_conversation(task)
    
    def _build_task_conversation_prompt(self, task: A2ATask) -> str:
        """Build prompt for agent to analyze incoming task"""
        
        # Check if clarification was already provided
        has_clarification = task.parameters.get("clarification_provided", False)
        clarifications = task.parameters.get("clarifications", {})
        
        # Get conversation context
        context_messages = ""
        if task.conversation_context:
            context_messages = "\n".join([
                f"{msg.get('from', 'unknown')}: {msg.get('message', '')}" 
                for msg in task.conversation_context[-5:]  # Last 5 messages
            ])
            
        clarification_context = ""
        if has_clarification:
            clarification_context = f"""
IMPORTANT: Clarification has already been provided for this task:
{json.dumps(clarifications, indent=2)}

You should proceed with the task using this clarification information.
"""
        
        prompt = f"""You are {self.agent_name.upper()}, {self._get_agent_personality()}.

Another agent ({task.from_agent.upper()}) has sent you a task:

TASK TYPE: {task.task_type}
PARAMETERS: {json.dumps(task.parameters, indent=2)}

{clarification_context}

CONVERSATION CONTEXT:
{context_messages}

Your job is to analyze this task and respond conversationally. Consider:
1. Do you understand what's being asked?
2. Do you have enough information to proceed?
3. Are there any ambiguities or missing details?
4. Can you complete this task with your capabilities?

{"Since clarification was already provided, you should proceed with the task." if has_clarification else ""}

Respond with a JSON object:
{{
    "message": "Your conversational response to the requesting agent",
    "action": "proceed|clarify|decline", 
    "reasoning": "Why you chose this action",
    "questions": ["question1", "question2"] // Only if action is "clarify"
}}

Be conversational and specific. If you need clarification, ask focused questions.
If you can proceed, briefly confirm what you'll do.
If you must decline, explain why politely.

Respond with ONLY the JSON object."""
        
        return prompt
    
    def _parse_conversation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse agent's conversational response"""
        try:
            # Clean and extract JSON
            cleaned = response_text.strip()
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = cleaned[start_idx:end_idx + 1]
                parsed = json.loads(json_str)
                
                # Ensure required fields
                if "message" not in parsed:
                    parsed["message"] = f"I'll help with the {self.agent_name} task."
                if "action" not in parsed:
                    parsed["action"] = "proceed"
                    
                return parsed
            else:
                return {
                    "message": cleaned,
                    "action": "proceed",
                    "reasoning": "Plain text response"
                }
                
        except Exception as e:
            print(f"{self.agent_name.upper()}: Failed to parse conversation response: {e}")
            return {
                "message": f"I'll work on your {self.agent_name} task.",
                "action": "proceed", 
                "reasoning": "Fallback response"
            }
    
    async def _fallback_task_conversation(self, task: A2ATask) -> Dict[str, Any]:
        """Fallback conversation when Gemini unavailable"""
        
        # Simple heuristic responses based on task type
        if task.task_type in ["data_collection", "research"]:
            if not task.parameters.get("query") and not task.parameters.get("research_query"):
                return {
                    "message": f"I'd be happy to help with data collection! Could you specify what exactly you want me to research?",
                    "action": "clarify",
                    "questions": ["What specific topic should I research?", "Any particular sources or scope you prefer?"]
                }
            else:
                return {
                    "message": f"Got it! I'll start collecting data on that topic right away.",
                    "action": "proceed"
                }
                
        elif task.task_type in ["analysis", "analyze_data"]:
            if not task.parameters.get("data") and not task.parameters.get("analysis_data"):
                return {
                    "message": f"I'm ready to analyze data for you. Could you provide the data to analyze?",
                    "action": "clarify", 
                    "questions": ["What data should I analyze?", "Any specific analysis focus or metrics?"]
                }
            else:
                return {
                    "message": f"Perfect! I'll analyze this data and extract key insights.",
                    "action": "proceed"
                }
                
        elif task.task_type in ["generate_content", "create_deliverable"]:
            if not task.parameters.get("content") and not task.parameters.get("analysis_results"):
                return {
                    "message": f"I can create the deliverable! What content or analysis should I base it on?",
                    "action": "clarify",
                    "questions": ["What content should I use as the foundation?", "What format do you prefer?"]
                }
            else:
                return {
                    "message": f"Understood! I'll create a professional deliverable based on the provided content.",
                    "action": "proceed"
                }
        
        # Default response
        return {
            "message": f"I'll work on your {task.task_type} task.",
            "action": "proceed"
        }
    
    async def send_task_to_agent(self, to_agent: str, task_type: str, 
                               parameters: Dict[str, Any], chat_id: str, 
                               conversation_message: str = "") -> str:
        """
        Send a task to another agent with conversational message
        """
        # Log outgoing conversation
        await self.state_manager.add_agent_conversation(
            chat_id=chat_id,
            from_agent=self.agent_name.upper(),
            to_agent=to_agent.upper(),
            message=conversation_message or f"Sending {task_type} task",
            conversation_type="task_delegation"
        )
        
        return await self.communication_manager.send_agent_task(
            self.agent_name, to_agent, task_type, parameters, chat_id, conversation_message
        )
    
    async def broadcast_status(self, status: str, chat_id: str, message: str = ""):
        """Broadcast status to other agents and frontend"""
        # Log status broadcast as conversation
        if message:
            await self.state_manager.add_agent_conversation(
                chat_id=chat_id,
                from_agent=self.agent_name.upper(),
                to_agent="ALL",
                message=message,
                conversation_type="status_broadcast"
            )
        
        await self.communication_manager.broadcast_agent_status(
            self.agent_name, status, chat_id, message
        )
    
    @abstractmethod
    async def _execute_agent_task(self, task: A2ATask) -> Dict[str, Any]:
        """
        Execute the actual agent-specific task logic.
        Must be implemented by each agent.
        """
        pass
    
    @abstractmethod 
    def _get_agent_personality(self) -> str:
        """
        Return a description of the agent's personality for conversation prompts.
        Must be implemented by each agent.
        """
        pass
    
    # Legacy compatibility methods - route through A2A system
    async def process_data(self, chat_id: str, data: Any) -> Any:
        """Legacy method - creates internal A2A task"""
        task = A2ATask(
            task_id=f"legacy_{self.agent_name}_{datetime.now().timestamp()}",
            from_agent="system",
            to_agent=self.agent_name,
            task_type="process_data",
            parameters={"data": data},
            conversation_context=[],
            created_at=datetime.now().isoformat(),
            chat_id=chat_id
        )
        
        response = await self.receive_a2a_task(task)
        return response.response_data.get("result", data)