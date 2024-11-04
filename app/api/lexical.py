"""
API endpoints for lexical value operations.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel
import time
import logging
import json

from app.core.database import get_db
from app.services.lexical_service import LexicalService
from app.services.llm_service import LLMServiceError
from app.services.llm.bedrock import BedrockClientError
from app.models.lexical_value import LexicalValue

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["lexical"])

# In-memory storage for task status and delete triggers
task_status = {}
delete_triggers = {}

class LexicalCreateSchema(BaseModel):
    """Schema for lexical value creation request."""
    lemma: str
    search_lemma: bool = True  # Default to True since all inputs are lemmas

def format_entry_for_response(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Format entry data to match frontend expectations."""
    if not entry:
        return None
        
    # Create a deep copy to avoid modifying the original
    formatted_entry = json.loads(json.dumps(entry))
    
    # Ensure citations_used exists and is a list of strings
    if 'citations_used' not in formatted_entry:
        formatted_entry['citations_used'] = []
    elif not isinstance(formatted_entry['citations_used'], list):
        # If it's not a list, convert to list of strings
        formatted_entry['citations_used'] = [str(formatted_entry['citations_used'])]
    else:
        # Ensure all items are strings
        formatted_entry['citations_used'] = [str(citation) for citation in formatted_entry['citations_used']]
    
    # Keep references field separate and ensure it has the correct structure
    if 'references' not in formatted_entry:
        formatted_entry['references'] = {'citations': []}
    elif 'citations' not in formatted_entry['references']:
        formatted_entry['references']['citations'] = []
    
    # Format system-generated citations in references
    formatted_references = []
    for citation in formatted_entry['references']['citations']:
        if isinstance(citation, dict):
            # Ensure citation has all required fields
            formatted_citation = citation.copy()
            
            # Ensure sentence structure
            if 'sentence' not in formatted_citation:
                formatted_citation['sentence'] = {
                    'id': '',
                    'text': '',
                    'prev_sentence': None,
                    'next_sentence': None,
                    'tokens': {}
                }
            
            # Ensure context structure
            if 'context' not in formatted_citation:
                formatted_citation['context'] = {
                    'line_id': '',
                    'line_text': formatted_citation.get('sentence', {}).get('text', ''),
                    'line_numbers': []
                }
            elif 'line_numbers' not in formatted_citation['context']:
                formatted_citation['context']['line_numbers'] = []
            
            # Ensure location structure
            if 'location' not in formatted_citation:
                formatted_citation['location'] = {
                    'volume': '',
                    'chapter': '',
                    'section': ''
                }
            
            # Ensure source structure
            if 'source' not in formatted_citation:
                formatted_citation['source'] = {
                    'author': 'Unknown',
                    'work': 'Unknown Work'
                }
            
            formatted_references.append(formatted_citation)
    
    formatted_entry['references']['citations'] = formatted_references
    
    # Remove sentence_contexts since the data is now embedded in citations
    if 'sentence_contexts' in formatted_entry:
        del formatted_entry['sentence_contexts']
    
    return formatted_entry

async def create_lexical_value_task(
    lemma: str,
    search_lemma: bool,
    task_id: str,
    db: AsyncSession
):
    """Background task for lexical value creation."""
    try:
        logger.info(f"Starting lexical value creation task for: {lemma}")
        logger.debug(f"Task parameters - lemma: {lemma}, search_lemma: {search_lemma}, task_id: {task_id}")
        
        task_status[task_id] = {
            "status": "in_progress",
            "message": "Creating lexical value",
            "start_time": time.time()
        }
        
        lexical_service = LexicalService(db)
        logger.debug(f"Initialized LexicalService for task {task_id}")
        
        result = await lexical_service.create_lexical_entry(
            lemma=lemma,
            search_lemma=search_lemma,
            task_id=task_id
        )
        logger.debug(f"Create lexical entry result for {lemma}: {json.dumps(result, indent=2)}")
        
        end_time = time.time()
        duration = end_time - task_status[task_id]["start_time"]
        
        # Format entry for frontend
        formatted_entry = format_entry_for_response(result.get("entry"))
        
        task_status[task_id] = {
            "status": "completed",
            "success": result["success"],
            "message": result["message"],
            "entry": formatted_entry,
            "action": result["action"],
            "duration": f"{duration:.2f}s"
        }
        logger.info(f"Completed lexical value creation for {lemma} in {duration:.2f}s")
        
    except (LLMServiceError, BedrockClientError) as e:
        logger.error(f"LLM error in lexical value creation for {lemma}: {str(e)}")
        end_time = time.time()
        duration = end_time - task_status[task_id]["start_time"]
        task_status[task_id] = {
            "status": "error",
            "message": str(e),
            "duration": f"{duration:.2f}s",
            "error_details": {
                "type": "llm_error",
                "message": str(e),
                "detail": getattr(e, 'detail', {}),
                "task_id": task_id,
                "lemma": lemma
            }
        }
    except Exception as e:
        logger.error(f"Error in lexical value creation task for {lemma}: {str(e)}", exc_info=True)
        end_time = time.time()
        duration = end_time - task_status[task_id]["start_time"]
        task_status[task_id] = {
            "status": "error",
            "message": str(e),
            "duration": f"{duration:.2f}s",
            "error_details": {
                "type": type(e).__name__,
                "message": str(e),
                "task_id": task_id,
                "lemma": lemma
            }
        }

@router.post("/create")
async def create_lexical_value(
    data: LexicalCreateSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new lexical value entry."""
    logger.info(f"Received request to create lexical value for: {data.lemma}")
    logger.debug(f"Create request parameters: {data.dict()}")
    
    task_id = f"create_{data.lemma}_{time.time()}"
    logger.debug(f"Generated task_id: {task_id}")
    
    background_tasks.add_task(
        create_lexical_value_task,
        data.lemma,
        data.search_lemma,
        task_id,
        db
    )
    logger.info(f"Added lexical value creation task to background tasks: {task_id}")
    
    return {
        "task_id": task_id,
        "message": "Lexical value creation started"
    }

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a lexical value creation task."""
    logger.debug(f"Checking status for task: {task_id}")
    
    if task_id not in task_status:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Task not found",
                "task_id": task_id
            }
        )
    
    status = task_status[task_id]
    
    # Format entry if present
    if "entry" in status:
        status["entry"] = format_entry_for_response(status["entry"])
    
    logger.debug(f"Task status for {task_id}: {json.dumps(status, indent=2)}")
    return status

@router.get("/get/{lemma}")
async def get_lexical_value(
    lemma: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a lexical value by its lemma."""
    try:
        logger.info(f"Getting lexical value for: {lemma}")
        lexical_service = LexicalService(db)
        entry = await lexical_service.get_lexical_value(lemma)
        
        if entry:
            logger.debug(f"Found lexical value for {lemma}")
            return format_entry_for_response(entry.to_dict())
            
        logger.warning(f"Lexical value not found for: {lemma}")
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Lexical value not found",
                "lemma": lemma
            }
        )
    except Exception as e:
        logger.error(f"Error getting lexical value for {lemma}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "type": type(e).__name__,
                "lemma": lemma
            }
        )

@router.get("/versions/{lemma}")
async def get_lexical_versions(
    lemma: str,
    db: AsyncSession = Depends(get_db)
):
    """Get available versions of a lexical value."""
    try:
        logger.info(f"Getting versions for lexical value: {lemma}")
        lexical_service = LexicalService(db)
        versions = await lexical_service.get_json_versions(lemma)
        
        if versions:
            logger.debug(f"Found {len(versions)} versions for {lemma}")
            return {"versions": versions}
            
        logger.warning(f"No versions found for: {lemma}")
        return {"versions": []}
        
    except Exception as e:
        logger.error(f"Error getting versions for {lemma}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "type": type(e).__name__,
                "lemma": lemma
            }
        )

@router.get("/list")
async def list_lexical_values(
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List lexical values with pagination."""
    try:
        logger.info(f"Listing lexical values - offset: {offset}, limit: {limit}")
        lexical_service = LexicalService(db)
        values = await lexical_service.list_lexical_values(offset, limit)
        formatted_values = [format_entry_for_response(v) for v in values]
        logger.debug(f"Found {len(values)} lexical values")
        return {"values": formatted_values}
    except Exception as e:
        logger.error(f"Error listing lexical values: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "type": type(e).__name__,
                "offset": offset,
                "limit": limit
            }
        )

@router.put("/update/{lemma}")
async def update_lexical_value(
    lemma: str,
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Update an existing lexical value."""
    try:
        logger.info(f"Updating lexical value for: {lemma}")
        logger.debug(f"Update data: {json.dumps(data, indent=2)}")
        
        lexical_service = LexicalService(db)
        result = await lexical_service.update_lexical_value(lemma, data)
        
        if not result["success"]:
            logger.warning(f"Failed to update lexical value for {lemma}: {result['message']}")
            raise HTTPException(
                status_code=404,
                detail={
                    "message": result["message"],
                    "lemma": lemma
                }
            )
        
        # Format entry for frontend
        if "entry" in result:
            result["entry"] = format_entry_for_response(result["entry"])
            
        logger.info(f"Successfully updated lexical value for {lemma}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lexical value for {lemma}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "type": type(e).__name__,
                "lemma": lemma
            }
        )

@router.post("/delete/{lemma}/trigger")
async def trigger_delete_lexical_value(
    lemma: str,
    db: AsyncSession = Depends(get_db)
):
    """Trigger deletion of a lexical value."""
    try:
        logger.info(f"Triggering deletion for lexical value: {lemma}")
        
        # Check if lexical value exists
        lexical_service = LexicalService(db)
        entry = await lexical_service.get_lexical_value(lemma)
        
        if not entry:
            logger.warning(f"Lexical value not found for deletion trigger: {lemma}")
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Lexical value not found",
                    "lemma": lemma
                }
            )
        
        # Store trigger in memory with timestamp
        trigger_id = f"delete_{lemma}_{time.time()}"
        delete_triggers[trigger_id] = {
            "lemma": lemma,
            "timestamp": time.time(),
            "entry": entry.to_dict()
        }
        
        logger.info(f"Created delete trigger {trigger_id} for {lemma}")
        return {
            "trigger_id": trigger_id,
            "message": "Delete trigger created",
            "entry": format_entry_for_response(entry.to_dict())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating delete trigger for {lemma}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "type": type(e).__name__,
                "lemma": lemma
            }
        )

@router.delete("/delete/{lemma}")
async def delete_lexical_value(
    lemma: str,
    trigger_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a lexical value (requires prior trigger)."""
    try:
        logger.info(f"Deleting lexical value for: {lemma}")
        
        # Verify trigger exists and is valid
        if trigger_id not in delete_triggers:
            logger.warning(f"Delete trigger not found: {trigger_id}")
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Delete trigger not found",
                    "trigger_id": trigger_id,
                    "lemma": lemma
                }
            )
        
        trigger = delete_triggers[trigger_id]
        
        # Verify trigger matches lemma
        if trigger["lemma"] != lemma:
            logger.warning(f"Delete trigger lemma mismatch: {trigger['lemma']} != {lemma}")
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Delete trigger lemma mismatch",
                    "trigger_lemma": trigger["lemma"],
                    "request_lemma": lemma
                }
            )
        
        # Verify trigger hasn't expired (30 minute timeout)
        if time.time() - trigger["timestamp"] > 1800:
            logger.warning(f"Delete trigger expired: {trigger_id}")
            del delete_triggers[trigger_id]
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Delete trigger expired",
                    "trigger_id": trigger_id,
                    "lemma": lemma
                }
            )
        
        # Perform deletion
        lexical_service = LexicalService(db)
        success = await lexical_service.delete_lexical_value(lemma)
        
        if not success:
            logger.warning(f"Lexical value not found for deletion: {lemma}")
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Lexical value not found",
                    "lemma": lemma
                }
            )
        
        # Clean up trigger
        del delete_triggers[trigger_id]
            
        logger.info(f"Successfully deleted lexical value for {lemma}")
        return {
            "success": True,
            "message": "Lexical value deleted successfully",
            "lemma": lemma
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lexical value for {lemma}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "type": type(e).__name__,
                "lemma": lemma
            }
        )
