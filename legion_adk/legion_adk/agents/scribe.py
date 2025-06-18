# agents/adk_scribe.py - SCRIBE creates Google Docs/Sheets/Slides from AUGUR's content with fixed Google Slides implementation

import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from services.state_manager import StateManager
from services.adk_communication import A2ATask, A2AResponse
from agents.base_adk_agent import BaseADKAgent

from google.oauth2 import service_account
from googleapiclient.discovery import build

class ScribeADKAgent(BaseADKAgent):
    """SCRIBE - Creates Google Docs/Sheets/Slides from ready-made content"""

    def __init__(self, state_manager: StateManager, api_key: Optional[str] = None):
        super().__init__("scribe", state_manager, api_key)
        self._init_google_services()
        print("SCRIBE: Ready to create Google documents from provided content")

    def _init_google_services(self):
        """Initialize Google services"""
        creds_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'credentials', 'google_docs_cred.json')
        
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=[
                'https://www.googleapis.com/auth/documents',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/presentations'
            ]
        )
        
        self.docs_service = build('docs', 'v1', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)
        self.sheets_service = build('sheets', 'v4', credentials=credentials)
        self.slides_service = build('slides', 'v1', credentials=credentials)

    def _get_agent_personality(self) -> str:
        return """a document creation specialist who takes formatted content and creates beautiful Google Docs, Sheets, and Slides."""

    async def _execute_agent_task(self, task: A2ATask) -> Dict[str, Any]:
        """Execute SCRIBE task - create Google files from AUGUR's content"""
        chat_id = task.chat_id
        
        # Get deliverables from AUGUR
        deliverables_data = self._extract_deliverables(task.parameters)
        
        if not deliverables_data:
            raise ValueError("No deliverables found in task parameters")
        
        print(f"SCRIBE: Creating {len(deliverables_data)} deliverable(s)")
        
        # Track operation
        operation_id = await self.state_manager.add_agent_operation(
            chat_id=chat_id, agent="SCRIBE", operation_type="document_creation",
            title=f"Creating {len(deliverables_data)} Google file(s)", 
            details="Creating documents from provided content",
            status="active", progress=0
        )
        
        try:
            # Create each deliverable
            created_deliverables = []
            
            for i, deliverable in enumerate(deliverables_data):
                # Update progress
                progress = int((i / len(deliverables_data)) * 90)
                format_type = deliverable.get("format", "unknown")
                
                await self.state_manager.update_agent_operation(
                    chat_id=chat_id, operation_id=operation_id, 
                    details=f"Creating {format_type} ({i+1}/{len(deliverables_data)})",
                    progress=progress
                )
                
                print(f"SCRIBE: Creating {format_type} deliverable")
                
                # Create based on format
                if format_type == "docs":
                    result = await self._create_google_doc(deliverable)
                elif format_type == "sheets":
                    result = await self._create_google_sheet(deliverable)
                elif format_type == "slides":
                    result = await self._create_google_slides(deliverable)
                else:
                    print(f"SCRIBE: Unknown format {format_type}, skipping")
                    continue
                
                created_deliverables.append(result)
                
                # Update frontend
                await self.state_manager.update_frontend_state(
                    chat_id, {"event": "deliverable_update", "deliverable": result}
                )
            
            await self.state_manager.update_agent_operation(
                chat_id=chat_id, operation_id=operation_id, status="completed", progress=100,
                details=f"Created {len(created_deliverables)} file(s) successfully"
            )
            
            return {
                "status": "completed",
                "deliverables": created_deliverables,
                "primary_deliverable": created_deliverables[0] if created_deliverables else None,
                "summary": f"Created {len(created_deliverables)} Google file(s)"
            }
            
        except Exception as e:
            await self.state_manager.update_agent_operation(
                chat_id=chat_id, operation_id=operation_id, status="error", details=str(e)
            )
            raise

    def _extract_deliverables(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract deliverables from AUGUR's response"""
        
        # Check direct deliverables
        if "deliverables" in parameters:
            return parameters["deliverables"]
        
        # Check in analysis_result
        if "analysis_result" in parameters:
            analysis = parameters["analysis_result"]
            if "deliverables" in analysis:
                return analysis["deliverables"]
            
            # Check in analysis_results.deliverables
            if "analysis_results" in analysis:
                results = analysis["analysis_results"]
                if "deliverables" in results:
                    return results["deliverables"]
        
        # Check in analysis_results directly
        if "analysis_results" in parameters:
            results = parameters["analysis_results"]
            if "deliverables" in results:
                return results["deliverables"]
        
        return []

    async def _create_google_doc(self, deliverable: Dict[str, Any]) -> Dict[str, Any]:
        """Create Google Doc from provided content"""
        
        title = deliverable.get("title", f"Document_{datetime.now().strftime('%Y%m%d_%H%M')}")
        content = deliverable.get("content", {})
        
        # Create document
        document = self.docs_service.documents().create(body={'title': title}).execute()
        doc_id = document.get('documentId')
        
        # Add content
        requests = []
        current_index = 1
        
        sections = content.get("sections", [])
        
        for section in sections:
            section_title = section.get("title", "")
            section_content = section.get("content", "")
            formatting = section.get("formatting", "normal")
            
            # Add title if exists
            if section_title:
                # Insert title text
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': f"{section_title}\n\n"
                    }
                })
                
                # Format title
                title_end = current_index + len(section_title)
                if formatting == "heading1":
                    requests.append({
                        'updateTextStyle': {
                            'range': {
                                'startIndex': current_index,
                                'endIndex': title_end
                            },
                            'textStyle': {
                                'bold': True,
                                'fontSize': {'magnitude': 16, 'unit': 'PT'}
                            },
                            'fields': 'bold,fontSize'
                        }
                    })
                
                current_index += len(section_title) + 2
            
            # Add content
            if section_content:
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': f"{section_content}\n\n"
                    }
                })
                current_index += len(section_content) + 2
        
        # Execute all requests
        if requests:
            self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
        
        # Share document
        self._share_document(doc_id)
        
        return {
            "title": title,
            "url": f"https://docs.google.com/document/d/{doc_id}/edit",
            "type": "google_doc",
            "format": "google_docs",
            "created": datetime.now().isoformat(),
            "generated_by": "SCRIBE"
        }

    async def _create_google_sheet(self, deliverable: Dict[str, Any]) -> Dict[str, Any]:
        """Create Google Sheet from provided content"""
        
        title = deliverable.get("title", f"Spreadsheet_{datetime.now().strftime('%Y%m%d_%H%M')}")
        content = deliverable.get("content", {})
        
        # Create spreadsheet
        spreadsheet = self.sheets_service.spreadsheets().create(
            body={'properties': {'title': title}}
        ).execute()
        sheet_id = spreadsheet.get('spreadsheetId')
        
        # Add worksheets
        worksheets = content.get("worksheets", [])
        
        for i, worksheet in enumerate(worksheets):
            worksheet_name = worksheet.get("name", f"Sheet{i+1}")
            data_rows = worksheet.get("data", [])
            
            if i == 0:
                # Rename default sheet
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={
                        'requests': [{
                            'updateSheetProperties': {
                                'properties': {
                                    'sheetId': 0,
                                    'title': worksheet_name
                                },
                                'fields': 'title'
                            }
                        }]
                    }
                ).execute()
            else:
                # Add new sheet
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={
                        'requests': [{
                            'addSheet': {
                                'properties': {'title': worksheet_name}
                            }
                        }]
                    }
                ).execute()
            
            # Add data
            if data_rows:
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=sheet_id,
                    range=f"{worksheet_name}!A1",
                    valueInputOption='RAW',
                    body={'values': data_rows}
                ).execute()
                
                # Format header row
                self._format_sheet_header(sheet_id, worksheet_name, len(data_rows[0]) if data_rows else 0)
        
        # Share document
        self._share_document(sheet_id)
        
        return {
            "title": title,
            "url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
            "type": "google_sheet",
            "format": "google_sheets",
            "created": datetime.now().isoformat(),
            "generated_by": "SCRIBE"
        }

    async def _create_google_slides(self, deliverable: Dict[str, Any]) -> Dict[str, Any]:
        """Create Google Slides from provided content - FIXED VERSION"""
        
        title = deliverable.get("title", f"Presentation_{datetime.now().strftime('%Y%m%d_%H%M')}")
        content = deliverable.get("content", {})
        
        try:
            # Create presentation
            presentation = self.slides_service.presentations().create(
                body={'title': title}
            ).execute()
            presentation_id = presentation.get('presentationId')
            
            # Get slides content
            slides = content.get("slides", [])
            
            if not slides:
                print("SCRIBE: No slides content found, creating basic presentation")
                # Share and return basic presentation
                self._share_document(presentation_id)
                return {
                    "title": title,
                    "url": f"https://docs.google.com/presentation/d/{presentation_id}/edit",
                    "type": "google_slides",
                    "format": "google_slides",
                    "created": datetime.now().isoformat(),
                    "generated_by": "SCRIBE"
                }
            
            # Get the current presentation structure
            current_presentation = self.slides_service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            # Update title slide if exists
            if slides and current_presentation.get('slides'):
                first_slide = slides[0]
                await self._update_title_slide_fixed(
                    presentation_id, 
                    current_presentation['slides'][0],
                    first_slide.get("title", title),
                    first_slide.get("subtitle", "") or first_slide.get("content", "")
                )
            
            # Create content slides (skip first slide as it's the title slide)
            for i, slide_data in enumerate(slides[1:], 1):
                try:
                    await self._create_content_slide_fixed(
                        presentation_id,
                        slide_data.get("title", f"Slide {i+1}"),
                        slide_data.get("content", ""),
                        slide_data.get("notes", "")
                    )
                except Exception as slide_error:
                    print(f"SCRIBE: Error creating slide {i+1}: {slide_error}")
                    # Continue with other slides
                    continue
            
            # Share document
            self._share_document(presentation_id)
            
            return {
                "title": title,
                "url": f"https://docs.google.com/presentation/d/{presentation_id}/edit",
                "type": "google_slides",
                "format": "google_slides",
                "created": datetime.now().isoformat(),
                "generated_by": "SCRIBE"
            }
            
        except Exception as e:
            print(f"SCRIBE: Critical error creating slides: {e}")
            raise

    async def _update_title_slide_fixed(self, presentation_id: str, slide_obj: dict, title: str, subtitle: str):
        """Update the title slide - FIXED VERSION"""
        
        try:
            requests = []
            
            for element in slide_obj.get('pageElements', []):
                if element.get('shape') and element['shape'].get('placeholder'):
                    placeholder_type = element['shape']['placeholder']['type']
                    object_id = element['objectId']
                    
                    if placeholder_type in ['CENTERED_TITLE', 'TITLE'] and title:
                        # Clear existing text first
                        requests.append({
                            'deleteText': {
                                'objectId': object_id,
                                'textRange': {'type': 'ALL'}
                            }
                        })
                        # Insert new text
                        requests.append({
                            'insertText': {
                                'objectId': object_id,
                                'text': title,
                                'insertionIndex': 0
                            }
                        })
                    elif placeholder_type in ['BODY', 'SUBTITLE'] and subtitle:
                        # Clear existing text first
                        requests.append({
                            'deleteText': {
                                'objectId': object_id,
                                'textRange': {'type': 'ALL'}
                            }
                        })
                        # Insert new text
                        requests.append({
                            'insertText': {
                                'objectId': object_id,
                                'text': subtitle,
                                'insertionIndex': 0
                            }
                        })
            
            if requests:
                self.slides_service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': requests}
                ).execute()
                
        except Exception as e:
            print(f"SCRIBE: Error updating title slide: {e}")
            # Don't raise - continue with presentation creation

    async def _create_content_slide_fixed(self, presentation_id: str, title: str, content: str, notes: str = ""):
        """Create a content slide - FIXED VERSION"""
        
        try:
            slide_id = f"slide_{uuid.uuid4().hex[:8]}"
            
            # Create the slide
            create_requests = [{
                'createSlide': {
                    'objectId': slide_id,
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_AND_BODY'
                    }
                }
            }]
            
            self.slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': create_requests}
            ).execute()
            
            # Get the updated presentation to find the new slide
            updated_presentation = self.slides_service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            # Find our slide
            target_slide = None
            for slide in updated_presentation['slides']:
                if slide['objectId'] == slide_id:
                    target_slide = slide
                    break
            
            if not target_slide:
                print(f"SCRIBE: Could not find created slide {slide_id}")
                return
            
            # Add content to slide
            content_requests = []
            
            for element in target_slide.get('pageElements', []):
                if element.get('shape') and element['shape'].get('placeholder'):
                    placeholder_type = element['shape']['placeholder']['type']
                    object_id = element['objectId']
                    
                    if placeholder_type in ['CENTERED_TITLE', 'TITLE'] and title:
                        content_requests.append({
                            'insertText': {
                                'objectId': object_id,
                                'text': title,
                                'insertionIndex': 0
                            }
                        })
                    elif placeholder_type in ['BODY', 'SUBTITLE'] and content:
                        content_requests.append({
                            'insertText': {
                                'objectId': object_id,
                                'text': content,
                                'insertionIndex': 0
                            }
                        })
            
            # Execute content requests
            if content_requests:
                self.slides_service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': content_requests}
                ).execute()
            
            # Handle speaker notes separately and safely
            if notes and notes.strip():
                await self._add_speaker_notes_safe(presentation_id, slide_id, notes)
                
        except Exception as e:
            print(f"SCRIBE: Error creating content slide: {e}")
            # Don't raise - let the presentation continue

    async def _add_speaker_notes_safe(self, presentation_id: str, slide_id: str, notes: str):
        """Safely add speaker notes - FIXED VERSION"""
        
        try:
            # Get the current presentation structure to find notes page
            presentation = self.slides_service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            # Find the slide and its notes page
            target_slide = None
            for slide in presentation['slides']:
                if slide['objectId'] == slide_id:
                    target_slide = slide
                    break
            
            if not target_slide:
                print(f"SCRIBE: Could not find slide {slide_id} for notes")
                return
            
            # Look for notes page in slide properties
            notes_object_id = None
            slide_properties = target_slide.get('slideProperties', {})
            notes_page = slide_properties.get('notesPage')
            
            if notes_page:
                # Find the notes text box
                for element in notes_page.get('pageElements', []):
                    if (element.get('shape') and 
                        element['shape'].get('placeholder') and 
                        element['shape']['placeholder'].get('type') == 'BODY'):
                        notes_object_id = element['objectId']
                        break
            
            if notes_object_id:
                notes_request = [{
                    'insertText': {
                        'objectId': notes_object_id,
                        'text': notes,
                        'insertionIndex': 0
                    }
                }]
                
                self.slides_service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': notes_request}
                ).execute()
                
                print(f"SCRIBE: Successfully added speaker notes to slide {slide_id}")
            else:
                print(f"SCRIBE: Could not find notes object for slide {slide_id}")
                
        except Exception as e:
            print(f"SCRIBE: Error adding speaker notes: {e}")
            # Don't raise - notes are optional

    def _format_sheet_header(self, sheet_id: str, worksheet_name: str, num_columns: int):
        """Format the header row of a worksheet"""
        if num_columns == 0:
            return
            
        # Get sheet ID
        spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        worksheet_id = 0
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == worksheet_name:
                worksheet_id = sheet['properties']['sheetId']
                break
        
        # Format header
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={
                'requests': [{
                    'repeatCell': {
                        'range': {
                            'sheetId': worksheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': num_columns
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {'bold': True},
                                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                            }
                        },
                        'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                    }
                }]
            }
        ).execute()

    def _share_document(self, file_id: str):
        """Make document publicly viewable"""
        self.drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

    async def receive_a2a_task(self, task: A2ATask) -> A2AResponse:
        """Handle A2A tasks"""
        try:
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id, from_agent=task.from_agent.upper(),
                to_agent="SCRIBE", message=f"Starting {task.task_type}",
                conversation_type="task_assignment"
            )
            
            result = await self._execute_agent_task(task)
            
            deliverables = result.get("deliverables", [])
            deliverable_count = len(deliverables)
            
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id, from_agent="SCRIBE", 
                to_agent=task.from_agent.upper(),
                message=f"Created {deliverable_count} Google file(s): {', '.join([d['format'] for d in deliverables])}",
                conversation_type="task_completion"
            )
            
            return A2AResponse(
                task_id=task.task_id, status="completed",
                response_data=result, 
                conversation_message=result.get('summary', f'{deliverable_count} file(s) created'),
                artifacts=deliverables,
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id, from_agent="SCRIBE",
                to_agent=task.from_agent.upper(), message=f"Error: {str(e)}",
                conversation_type="task_error"
            )
            
            return A2AResponse(
                task_id=task.task_id, status="error",
                response_data={"error": str(e)}, conversation_message=f"Failed: {str(e)}",
                artifacts=[], created_at=datetime.now().isoformat()
            )