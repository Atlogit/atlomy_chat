"""
API endpoints for lexical value operations.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import time
import logging

from app.core.database import get_db
from app.services.lexical_service import LexicalService
from app.models.lexical_value import LexicalValue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lexical", tags=["lexical"])

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
        task_status[task_id] = {
            "status": "in_progress",
            "message": "Creating lexical value"
        }
        
        lexical_service = LexicalService(db)
        result = await lexical_service.create_lexical_entry(
            lemma=lemma,
            search_lemma=search_lemma,
            task_id=task_id
        )
        
        task_status[task_id] = {
            "status": "completed",
            "success": result["success"],
            "message": result["message"],
            "entry": result.get("entry"),
            "action": result["action"]
        }
        
    except Exception as e:
        logger.error(f"Error in lexical value creation task: {str(e)}")
        task_status[task_id] = {
            "status": "error",
            "message": str(e)
        }

@router.post("/create")
async def create_lexical_value(
    data: LexicalCreateSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new lexical value entry."""
    task_id = f"create_{data.lemma}_{time.time()}"
    background_tasks.add_task(
        create_lexical_value_task,
        data.lemma,
        data.search_lemma,
        task_id,
        db
    )
    return {
        "task_id": task_id,
        "message": "Lexical value creation started"
    }

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a lexical value creation task."""
    if task_id not in task_status:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    return task_status[task_id]

@router.get("/get/{lemma}")
async def get_lexical_value(
    lemma: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a lexical value by its lemma."""
    try:
        lexical_service = LexicalService(db)
        entry = await lexical_service.get_lexical_value(lemma)
        if entry:
            return entry.to_dict()
        raise HTTPException(
            status_code=404,
            detail="Lexical value not found"
        )
    except Exception as e:
        logger.error(f"Error getting lexical value: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/list")
async def list_lexical_values(
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List lexical values with pagination."""
    try:
        lexical_service = LexicalService(db)
        values = await lexical_service.list_lexical_values(offset, limit)
        return {"values": values}
    except Exception as e:
        logger.error(f"Error listing lexical values: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.put("/update/{lemma}")
async def update_lexical_value(
    lemma: str,
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Update an existing lexical value."""
    try:
        lexical_service = LexicalService(db)
        result = await lexical_service.update_lexical_value(lemma, data)
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=result["message"]
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lexical value: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.delete("/delete/{lemma}")
async def delete_lexical_value(
    lemma: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a lexical value."""
    try:
        lexical_service = LexicalService(db)
        success = await lexical_service.delete_lexical_value(lemma)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Lexical value not found"
            )
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lexical value: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
