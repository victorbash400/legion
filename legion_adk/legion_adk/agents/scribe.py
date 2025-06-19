# agents/adk_scribe.py - SCRIBE creates Google Docs/Sheets/Slides from AUGUR's content with hardcoded credentials

import os
import uuid
import json
import datetime
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from services.state_manager import StateManager
from services.adk_communication import A2ATask, A2AResponse
from agents.base_adk_agent import BaseADKAgent

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

class ScribeADKAgent(BaseADKAgent):
    """SCRIBE - Creates Google Docs/Sheets/Slides from ready-made content"""

    def __init__(self, state_manager: StateManager, api_key: Optional[str] = None):
        super().__init__("scribe", state_manager, api_key)
        self._init_google_services()
        print("SCRIBE: Ready to create Google documents from provided content")

    def _init_google_services(self):
        """Initialize Google services using hardcoded credentials"""
        
        # Hardcoded Google service account credentials - KEEP TRIPLE QUOTES!
        creds_info = {
            "type": "service_account",
            "project_id": "ascendant-woods-462020-n0",
            "private_key_id": "40a18cfbc249aa5e84ac4c7ba3d0dc72f1de275c",
            "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCohfNMZrMcRvHQ
5eJ81fJ+iTJiab9XaA5Itdp6svuCrDsoc0NIjpxxF5hG9FLzBTHWK6dk7k9z457r
uYeqswFf0xJ6UJm2lZk89qLTXRGm0bBCYPSCgGx++0qvszBTS6A+5tqQCw7KzOoZ
Li17wIF/kCHrIID/+ND6uPOM28t1gSah9QphDPSJ+tufc/gVIQpz67ILoCi3GFyA
+iOF3kqkgjTaF8WhvfQ3gzowcY0+rxuTb1rJsTgRZzGNEjc5477j19klHLnggqi3
Z5CWX7tcvOT9ObmmEJRaEwCF3Go61PAeS1dFvciSwyykspKRYwVc+yEveRi3rSYN
xWvP6gpjAgMBAAECggEAKuV92tLBgM8mOpBpqHElOsRdiON2Cx+3kxaHOHhawRZq
MI+2br+uXrMs1dLXUnjeCLAv+ecXXl5wU3x0ZiUOkn+90li1594IlZYKOFcWaSoy
/ZKEaruZ4nDAwBySjoFPlvNYaxYFe+XRKPuyJDAKRpg/qgQqEf4Z49g0VoSUM6J0
EZ402tjhN4c5Yx6BUk28t7cRz2uaaymWXwJU73yCTb+UtqoJHATjJGQNEdcVoUrY
DpYEL2m1Ki3Mnh8BHIGv4GIBNd2nGwXtBhWWpthfE1dsjHvKHXEamEwZmgRenznO
BcjnMhlsO9PqH0bk9frWhgq/RxVaotrslscL1ap84QKBgQDmDI7e890+8NdPK0os
p3lE7jRkNjzHipwTlYcPuFwh8ihLyYy9P6nmahhTBrg9em5qjDOgJvUvg/K54cOL
0PniRYwE6AWk9QlUxUZV8m/NSC2ZJYawoH6vPDVnyIgruaoaFZsvO0jsF61e4xuL
c8FYQF4KBkwv3u67fv3bWvFeewKBgQC7iKCJwb8J9q47Dc7RRy6tSMP00eX5uxRO
7RiZUJIfNX+3L853TWRjGxxe/Dx/DozZB0NMTruYSKjwKo+n40Ty9fwBiqpq//XQ
H+G/SJU01EiViPBo2m3kmqXM8cggXxfJu5tc8CTncwLOacPlP9NEMZ40sFzqcH2a
kHFHxJSzOQKBgQCH1NJnAkaYa0w2CrF5PEl2Uc/Ne9jXWRhe1+MvfQOpZ3ozhYX8
GCMRUYObQlR2uFuJvc6duWL780TWTF9Rpspkt/u8yeLLS4N+8hxdkxBAfWWvD2E/
2QP0I/DEnrsIVlABptBCSxb7j99mL2KMLIT0vszHzoAdo9wCCTGK21+5EQKBgDp5
gK1Tp1DhBTTOumVRD8HihY+J/26eIdf2YAw2Lkni8Z7aHkPe8uVgJ7mKZwarL8ng
VOCvUBlM1riEXOTZnb8walLEvRy+ERTDTC3L4RJm+vb9ixD2wvtcKUS9Q0ysugsi
H3CcRLWSjBZ2rimGfEawPgdp0p8bUl7mmRvqtP8pAoGAbFGOi5fDBReQPgXNT6VW
KruclhQFLwdtMrcybkWPFbCFQjr2HqmEOoZION8k9JKMezkeF2ZSEXSA9+mYFlcr
rFGGFPzHu4UEqUUzoELXimXG7mqO69HfobFWHC8s3xL+J8kklT5c84C6wqRgb6J4
Z2J6fHfOCt4n4xkjwr46j/g=
-----END PRIVATE KEY-----""",
            "client_email": "scribe-doc-generator@ascendant-woods-462020-n0.iam.gserviceaccount.com",
            "client_id": "100006225373116583872",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/scribe-doc-generator%40ascendant-woods-462020-n0.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        
        try:
            print("SCRIBE: Initializing Google services with hardcoded credentials")
            print(f"SCRIBE DEBUG: Project ID: {creds_info.get('project_id')}")
            print(f"SCRIBE DEBUG: Client email: {creds_info.get('client_email')}")
            
            # Debug key format
            print(f"SCRIBE DEBUG: Key starts with: {creds_info['private_key'][:50]}")
            print(f"SCRIBE DEBUG: Key ends with: {creds_info['private_key'][-50:]}")
            print(f"SCRIBE DEBUG: Total key length: {len(creds_info['private_key'])}")
            print(f"SCRIBE DEBUG: Line count in key: {len(creds_info['private_key'].splitlines())}")
            
            # Check system time
            current_time = datetime.utcnow()
            unix_time = time.time()
            print(f"⏰ SCRIBE DEBUG: Container UTC time: {current_time.isoformat()}Z")
            print(f"⏰ SCRIBE DEBUG: Unix timestamp: {unix_time}")
            
            # Create credentials from service account info
            credentials = service_account.Credentials.from_service_account_info(
                creds_info,
                scopes=[
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/presentations'
                ]
            )
            
            print("SCRIBE: Credentials object created successfully")
            
            # Force token refresh to handle potential clock skew
            try:
                credentials.refresh(Request())
                print("✅ SCRIBE: Successfully refreshed credentials - JWT signed with current time")
                
                # Check if token was generated
                if hasattr(credentials, 'token'):
                    print(f"SCRIBE DEBUG: Token generated, expires at: {credentials.expiry}")
                else:
                    print("SCRIBE WARNING: No token attribute found after refresh")
                    
            except Exception as refresh_error:
                print(f"❌ SCRIBE ERROR during token refresh: {refresh_error}")
                print(f"SCRIBE ERROR Type: {type(refresh_error).__name__}")
                
                # Try to extract more details from the error
                if hasattr(refresh_error, 'response'):
                    print(f"SCRIBE ERROR Response: {refresh_error.response}")
                if hasattr(refresh_error, 'content'):
                    print(f"SCRIBE ERROR Content: {refresh_error.content}")
                    
                raise
            
            # Initialize Google API services
            print("SCRIBE: Building Google API service clients...")
            
            self.docs_service = build('docs', 'v1', credentials=credentials)
            print("✅ SCRIBE: Docs service initialized")
            
            self.drive_service = build('drive', 'v3', credentials=credentials)
            print("✅ SCRIBE: Drive service initialized")
            
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            print("✅ SCRIBE: Sheets service initialized")
            
            self.slides_service = build('slides', 'v1', credentials=credentials)
            print("✅ SCRIBE: Slides service initialized")
            
            print("🎉 SCRIBE: All Google services initialized successfully!")
            
            # Test the credentials with a simple API call
            try:
                about = self.drive_service.about().get(fields="user").execute()
                print(f"✅ SCRIBE: Test API call successful. Service account: {about.get('user', {}).get('emailAddress', 'Unknown')}")
            except Exception as test_error:
                print(f"⚠️ SCRIBE WARNING: Test API call failed: {test_error}")
                # Don't raise here - the credentials might still work for other operations
            
        except Exception as e:
            print(f"❌ SCRIBE CRITICAL ERROR: Failed to initialize Google services: {e}")
            print(f"SCRIBE ERROR: Error type: {type(e).__name__}")
            print(f"⏰ SCRIBE ERROR: Container UTC time at failure: {datetime.utcnow().isoformat()}Z")
            
            import traceback
            print("SCRIBE ERROR: Full traceback:")
            print(traceback.format_exc())
            
            # Additional debugging for common issues
            if "invalid_grant" in str(e):
                print("\n🔍 SCRIBE DEBUG: Invalid grant error detected. Common causes:")
                print("  1. Clock skew between container and Google servers")
                print("  2. Corrupted private key during copy/paste")
                print("  3. Service account has been deleted or key rotated")
                print("  4. Incorrect project ID or client email")
                
            raise

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
        try:
            self.drive_service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            print(f"SCRIBE: Successfully shared document {file_id}")
        except Exception as e:
            print(f"SCRIBE WARNING: Could not share document {file_id}: {e}")
            # Don't fail if sharing doesn't work

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
            error_msg = str(e)
            print(f"SCRIBE ERROR in receive_a2a_task: {error_msg}")
            
            # Add more context for JWT errors
            if "invalid_grant" in error_msg or "JWT" in error_msg:
                error_msg = f"Authentication failed: {error_msg}. Check system time and credentials."
            
            await self.state_manager.add_agent_conversation(
                chat_id=task.chat_id, from_agent="SCRIBE",
                to_agent=task.from_agent.upper(), message=f"Error: {error_msg}",
                conversation_type="task_error"
            )
            
            return A2AResponse(
                task_id=task.task_id, status="error",
                response_data={"error": error_msg}, 
                conversation_message=f"Failed: {error_msg}",
                artifacts=[], 
                created_at=datetime.now().isoformat()
            )
