"""
API endpoints for lexical value operations.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
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

# In-memory storage for task status
task_status = {}

class LexicalCreateSchema(BaseModel):
    """Schema for lexical value creation request."""
    lemma: str
    search_lemma: bool = False

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
        
        task_status[task_id] = {
            "status": "completed",
            "success": result["success"],
            "message": result["message"],
            "entry": result.get("entry"),
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
            return entry.to_dict()
            
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
        logger.debug(f"Found {len(values)} lexical values")
        return {"values": values}
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

@router.delete("/delete/{lemma}")
async def delete_lexical_value(
    lemma: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a lexical value."""
    try:
        logger.info(f"Deleting lexical value for: {lemma}")
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
            
        logger.info(f"Successfully deleted lexical value for {lemma}")
        return {"success": True}
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
