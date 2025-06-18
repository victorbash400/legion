import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
import json

from services.adk_communication import get_communication_manager, A2ATask, A2AResponse
from services.state_manager import StateManager

@dataclass
class WorkflowStep:
    agent_name: str
    task_type: str
    depends_on: Optional[str] = None
    parameters: Dict[str, Any] = None

@dataclass
class ResearchQuestion:
    id: int
    question: str
    priority: int
    category: str
    context: str = ""
    answered: bool = False
    collected_data: Dict[str, Any] = None

class ADKWorkflowOrchestrator:
    """Streamlined ADK workflow orchestrator with question-driven research"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.communication_manager = get_communication_manager(state_manager)
        self.agents: Dict[str, Any] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(self, agent_name: str, agent_instance) -> None:
        self.agents[agent_name] = agent_instance
        print(f"ADK_ORCHESTRATOR: Registered agent {agent_name.upper()}")

    async def execute_workflow_with_context(self, workflow_name: str, chat_id: str, 
                                          mission_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute question-driven research workflow"""
        
        research_questions = mission_context.get("research_questions", [])
        
        if not research_questions:
            raise ValueError("No research questions provided for question-driven workflow")
        
        return await self._execute_question_driven_workflow(chat_id, mission_context)

    async def _execute_question_driven_workflow(self, chat_id: str, 
                                              mission_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the question-driven research workflow"""
        
        workflow_id = f"question_research_{chat_id}_{datetime.now().timestamp()}"
        research_focus = mission_context.get("research_focus", "research topic")
        research_questions = mission_context.get("research_questions", [])
        
        # Convert research questions to ResearchQuestion objects
        questions = []
        for i, q_data in enumerate(research_questions):
            if isinstance(q_data, dict):
                question = ResearchQuestion(
                    id=i+1,
                    question=q_data.get("question", ""),
                    priority=q_data.get("priority", i+1),
                    category=q_data.get("category", "general"),
                    context=q_data.get("context", "")
                )
            else:
                question = ResearchQuestion(
                    id=i+1,
                    question=str(q_data),
                    priority=i+1,
                    category="general"
                )
            questions.append(question)
        
        # Initialize workflow tracking
        self.active_workflows[workflow_id] = {
            "workflow_name": "question_driven_research",
            "chat_id": chat_id,
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "mission_context": mission_context,
            "research_questions": questions,
            "collected_data": []
        }
        
        await self._notify_frontend(chat_id, "workflow_started", {
            "workflow_id": workflow_id,
            "workflow_name": "question_driven_research",
            "total_questions": len(questions),
            "message": f"Question-driven research started with {len(questions)} research questions"
        })
        
        try:
            # Step 1: CONSUL coordination
            await self._notify_frontend(chat_id, "workflow_step_started", {
                "workflow_id": workflow_id,
                "step_number": 1,
                "agent_name": "CONSUL",
                "task_type": "coordinate_mission"
            })
            
            consul_agent = self._get_agent("consul")
            coordination_result = await self._execute_consul_coordination(
                consul_agent, chat_id, mission_context
            )
            
            await self._notify_frontend(chat_id, "workflow_step_completed", {
                "workflow_id": workflow_id,
                "step_number": 1,
                "agent_name": "CONSUL"
            })
            
            # Step 2: Collect data for each research question (CENTURION only)
            for i, question in enumerate(questions):
                question_step_num = i + 2
                
                await self._notify_frontend(chat_id, "research_question_started", {
                    "workflow_id": workflow_id,
                    "question_number": question.id,
                    "total_questions": len(questions),
                    "question": question.question,
                    "category": question.category
                })
                
                # CENTURION data collection for this question
                collected_data = await self._collect_question_data(
                    question, chat_id, mission_context, workflow_id, question_step_num
                )
                
                # Store the collected data
                question.answered = True
                question.collected_data = collected_data
                self.active_workflows[workflow_id]["collected_data"].append({
                    "question": question.question,
                    "category": question.category,
                    "data": collected_data
                })
                
                await self._notify_frontend(chat_id, "research_question_completed", {
                    "workflow_id": workflow_id,
                    "question_number": question.id,
                    "question": question.question,
                    "summary": f"Data collected for question {question.id}"
                })
            
            # Step 3: AUGUR analyzes ALL collected data at once
            final_step_num = len(questions) + 2
            
            await self._notify_frontend(chat_id, "workflow_step_started", {
                "workflow_id": workflow_id,
                "step_number": final_step_num,
                "agent_name": "AUGUR",
                "task_type": "analyze_all_data"
            })
            
            analysis_result = await self._analyze_all_data(
                chat_id, mission_context, self.active_workflows[workflow_id]["collected_data"]
            )
            
            await self._notify_frontend(chat_id, "workflow_step_completed", {
                "workflow_id": workflow_id,
                "step_number": final_step_num,
                "agent_name": "AUGUR"
            })
            
            # Step 4: SCRIBE synthesizes final document
            final_step_num = len(questions) + 3
            
            await self._notify_frontend(chat_id, "workflow_step_started", {
                "workflow_id": workflow_id,
                "step_number": final_step_num,
                "agent_name": "SCRIBE",
                "task_type": "synthesize_final_document"
            })
            
            synthesis_result = await self._synthesize_final_document(
                chat_id, mission_context, self.active_workflows[workflow_id]["collected_data"], analysis_result
            )
            
            await self._notify_frontend(chat_id, "workflow_step_completed", {
                "workflow_id": workflow_id,
                "step_number": final_step_num,
                "agent_name": "SCRIBE"
            })
            
            # Workflow completed
            self.active_workflows[workflow_id]["status"] = "completed"
            self.active_workflows[workflow_id]["completed_at"] = datetime.now().isoformat()
            
            await self._notify_frontend(chat_id, "workflow_completed", {
                "workflow_id": workflow_id,
                "message": f"Question-driven research completed - {len(questions)} questions researched",
                "total_questions": len(questions)
            })
            
            return {
                "consul": coordination_result,
                "augur": analysis_result,
                "scribe": synthesis_result,
                "collected_data": self.active_workflows[workflow_id]["collected_data"]
            }
            
        except Exception as e:
            self.active_workflows[workflow_id]["status"] = "failed"
            self.active_workflows[workflow_id]["error"] = str(e)
            await self._notify_frontend(chat_id, "workflow_failed", {
                "workflow_id": workflow_id,
                "error": str(e)
            })
            raise

    async def _collect_question_data(self, question: ResearchQuestion, chat_id: str,
                                   mission_context: Dict[str, Any], workflow_id: str,
                                   step_number: int) -> Dict[str, Any]:
        """Collect data for a specific research question using CENTURION"""
        
        research_focus = mission_context.get("research_focus", "research topic")
        
        await self._notify_frontend(chat_id, "agent_operation", {
            "agent": "CENTURION",
            "operation_type": "searching",
            "title": f"Researching Question {question.id}",
            "details": f"Collecting data for: {question.question}",
            "status": "active",
            "progress": 0,
            "data": {"question_id": question.id, "category": question.category}
        })
        
        centurion_params = {
            "research_query": question.question,
            "question_context": question.context,
            "question_category": question.category,
            "research_focus": research_focus,
            "mission_context": mission_context,
            "question_id": question.id
        }
        
        collected_data = await self._execute_agent_task(
            "consul", "centurion", "collect_question_data", 
            centurion_params, chat_id
        )
        
        return collected_data

    async def _analyze_all_data(self, chat_id: str, mission_context: Dict[str, Any],
                               all_collected_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """AUGUR analyzes ALL collected data at once"""
        
        research_focus = mission_context.get("research_focus", "research topic")
        
        await self._notify_frontend(chat_id, "agent_operation", {
            "agent": "AUGUR",
            "operation_type": "analyzing", 
            "title": "Comprehensive Data Analysis",
            "details": f"Analyzing all collected data for {len(all_collected_data)} questions",
            "status": "active",
            "progress": 0,
            "data": {"total_questions": len(all_collected_data)}
        })
        
        augur_params = {
            "all_collected_data": all_collected_data,
            "research_focus": research_focus,
            "mission_context": mission_context,
            "total_questions": len(all_collected_data)
        }
        
        analysis_result = await self._execute_agent_task(
            "centurion", "augur", "analyze_all_collected_data",
            augur_params, chat_id
        )
        
        return analysis_result

    async def _synthesize_final_document(self, chat_id: str, mission_context: Dict[str, Any],
                                       all_collected_data: List[Dict[str, Any]], 
                                       analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """SCRIBE synthesizes final comprehensive document"""
        
        research_focus = mission_context.get("research_focus", "research topic")
        
        await self._notify_frontend(chat_id, "agent_operation", {
            "agent": "SCRIBE",
            "operation_type": "composing",
            "title": "Document Synthesis",
            "details": f"Creating comprehensive report from analysis of {len(all_collected_data)} questions",
            "status": "active",
            "progress": 0,
            "data": {"total_questions": len(all_collected_data)}
        })
        
        synthesis_params = {
            "research_focus": research_focus,
            "all_collected_data": all_collected_data,
            "analysis_result": analysis_result,
            "mission_context": mission_context,
            "total_questions": len(all_collected_data)
        }
        
        synthesis_result = await self._execute_agent_task(
            "augur", "scribe", "synthesize_comprehensive_report",
            synthesis_params, chat_id
        )
        
        return synthesis_result

    async def _execute_agent_task(self, from_agent: str, to_agent: str,
                                task_type: str, parameters: Dict[str, Any], 
                                chat_id: str) -> Dict[str, Any]:
        """Execute agent task with CONSUL handling clarifications"""
        
        # Send task message
        message = self._generate_task_message(from_agent, to_agent, task_type, parameters)
        task_id = await self.communication_manager.send_agent_task(
            from_agent, to_agent, task_type, parameters, chat_id, message
        )
        
        # Create and execute task
        task = self._create_task(task_id, from_agent, to_agent, task_type, parameters, chat_id)
        agent = self._get_agent(to_agent)
        response = await agent.receive_a2a_task(task)
        
        # Handle response
        if response.status == "completed":
            return response.response_data
            
        elif response.status == "needs_clarification":
            return await self._handle_clarification_with_consul(
                task, response, chat_id
            )
        else:
            raise Exception(f"Agent {to_agent} failed: {response.conversation_message}")

    async def _handle_clarification_with_consul(self, task: A2ATask, response: A2AResponse,
                                              chat_id: str) -> Dict[str, Any]:
        """CONSUL handles clarifications intelligently via A2A"""
        
        questions = response.response_data.get("questions", [])
        agent_name = task.to_agent
        
        # Send clarification request to CONSUL via A2A
        clarification_task = self._create_task(
            f"{task.task_id}_clarification",
            agent_name, "consul", "provide_clarification",
            {
                "original_task": task.parameters,
                "agent_questions": questions,
                "task_type": task.task_type,
                "context": f"Agent {agent_name} needs clarification"
            },
            chat_id
        )
        
        consul = self._get_agent("consul")
        clarification_response = await consul.receive_a2a_task(clarification_task)
        
        if clarification_response.status != "completed":
            raise Exception("CONSUL failed to provide clarification")
        
        clarifications = clarification_response.response_data.get("clarifications", {})
        
        # Send clarifications back to original agent
        await self._send_agent_message(
            "CONSUL", agent_name,
            f"Clarifications provided: {json.dumps(clarifications, indent=2)}",
            chat_id, "clarification_response"
        )
        
        # Update task and re-execute
        updated_params = {
            **task.parameters,
            "clarifications": clarifications,
            "clarification_provided": True
        }
        
        updated_task = self._create_task(
            task.task_id, task.from_agent, task.to_agent,
            task.task_type, updated_params, task.chat_id
        )
        
        agent = self._get_agent(agent_name)
        final_response = await agent.receive_a2a_task(updated_task)
        
        if final_response.status == "completed":
            return final_response.response_data
        else:
            raise Exception(f"Agent {agent_name} failed after clarification")

    # Helper methods
    def _get_agent(self, agent_name: str):
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not registered")
        return self.agents[agent_name]
    
    def _create_task(self, task_id: str, from_agent: str, to_agent: str,
                    task_type: str, parameters: Dict[str, Any], chat_id: str) -> A2ATask:
        return A2ATask(
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            task_type=task_type,
            parameters=parameters,
            conversation_context=self.communication_manager._get_conversation_context(
                chat_id, from_agent, to_agent
            ),
            created_at=datetime.now().isoformat(),
            chat_id=chat_id
        )
    
    async def _notify_frontend(self, chat_id: str, event: str, data: Dict[str, Any]):
        await self.state_manager.update_frontend_state(chat_id, {"event": event, **data})
    
    async def _send_agent_message(self, from_agent: str, to_agent: str, 
                                message: str, chat_id: str, conv_type: str):
        await self._notify_frontend(chat_id, "agent_conversation", {
            "from_agent": from_agent,
            "to_agent": to_agent.upper(),
            "message": message,
            "conversation_type": conv_type
        })
    
    def _generate_task_message(self, from_agent: str, to_agent: str, 
                             task_type: str, parameters: Dict[str, Any]) -> str:
        """Generate task messages"""
        
        if task_type == "collect_question_data":
            question = parameters.get("research_query", "research question")
            question_id = parameters.get("question_id", "")
            return f"CENTURION, collect data for question #{question_id}: {question}"
        
        elif task_type == "analyze_all_collected_data":
            total_questions = parameters.get("total_questions", 0)
            return f"AUGUR, analyze ALL collected data from {total_questions} research questions"
        
        elif task_type == "synthesize_comprehensive_report":
            total_questions = parameters.get("total_questions", 0)
            return f"SCRIBE, create comprehensive report from analysis of {total_questions} questions"
            
        elif task_type == "provide_clarification":
            agent_questions = parameters.get("agent_questions", [])
            return f"CONSUL, please provide clarification for {len(agent_questions)} questions"
        
        return f"{to_agent.upper()}, please work on {task_type}"
    
    async def _execute_consul_coordination(self, consul_agent, chat_id: str, 
                                         mission_context: Dict[str, Any]) -> Dict[str, Any]:
        research_focus = mission_context.get("research_focus", "research topic")
        
        await consul_agent.broadcast_status("coordinating", chat_id, 
            f"Coordinating research mission: {research_focus}")
        
        return {
            "research_query": research_focus,
            "research_focus": research_focus,
            "mission_context": mission_context,
            "coordinator": "consul",
            "workflow_started": True
        }

    def list_active_workflows(self, chat_id: str) -> List[Dict[str, Any]]:
        """List active workflows for a chat"""
        return [
            {
                "workflow_id": wf_id,
                "workflow_type": wf_data.get("workflow_name", "unknown"),
                "status": wf_data.get("status", "unknown"),
                "started_at": wf_data.get("started_at"),
                "chat_id": wf_data.get("chat_id")
            }
            for wf_id, wf_data in self.active_workflows.items()
            if wf_data.get("chat_id") == chat_id and wf_data.get("status") == "active"
        ]