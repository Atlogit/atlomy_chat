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
from app.services.llm.bedrock import BedrockClient, BedrockClientError
from app.models.lexical_value import LexicalValue

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["lexical"])

# In-memory storage for task status and delete triggers
task_status = {}
delete_triggers = {}

class LLMConfigSchema(BaseModel):
    """Schema for LLM configuration."""
    modelId: Optional[str] = None
    temperature: Optional[float] = None
    topP: Optional[float] = None
    topK: Optional[int] = None
    maxLength: Optional[int] = None
    stopSequences: Optional[List[str]] = None

class LexicalCreateSchema(BaseModel):
    """Schema for lexical value creation request."""
    lemma: str
    search_lemma: bool = True  # Default to True since all inputs are lemmas
    llmConfig: Optional[LLMConfigSchema] = None

class LexicalUpdateSchema(BaseModel):
    """Schema for lexical value update request."""
    lemma: str
    llmConfig: Optional[LLMConfigSchema] = None

class LexicalListSchema(BaseModel):
    """Schema for lexical value list request."""
    offset: int = 0
    limit: int = 100

def convert_snake_to_camel_case(snake_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert snake_case keys to camelCase while preserving values."""
    key_mapping = {
        'model_id': 'modelId',
        'top_p': 'topP',
        'top_k': 'topK',
        'max_length': 'maxLength',
        'stop_sequences': 'stopSequences'
    }
    
    return {
        key_mapping.get(k, k): v 
        for k, v in snake_dict.items()
    }

@router.get("/models")
async def list_models():
    """List available LLM models."""
    try:
        logger.debug("Listing available LLM models")
        client = BedrockClient()
        models = await client.list_models()
        
        # Format models for response while keeping all available models
        formatted_models = []
        for model in models:
            model_id = model.get('modelId', '')
            formatted_models.append({
                'id': model_id,
                'name': model.get('modelName', model_id),
                'provider': model.get('providerName', 'Unknown'),
                'description': model.get('modelDescription', ''),
                'inputModalities': model.get('inputModalities', []),
                'outputModalities': model.get('outputModalities', []),
                'customizationsSupported': model.get('customizationsSupported', [])
            })
        
        logger.debug(f"Found {len(formatted_models)} available models")
        return {
            "models": formatted_models
        }
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "type": type(e).__name__
            }
        )

def format_entry_for_response(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Format entry data to match frontend expectations."""
    if not entry:
        return None
        
    # Create a deep copy to avoid modifying the original
    formatted_entry = json.loads(json.dumps(entry))
    
    # Robust metadata extraction
    original_metadata = formatted_entry.get('metadata', {})
    
    # Prioritize version extraction
    version_paths = [
        original_metadata.get('version'),
        formatted_entry.get('version'),
        original_metadata.get('version_id'),
        '1.0'  # Fallback
    ]
    version = next((v for v in version_paths if v), '1.0')
    
    # Multiple paths for LLM config extraction
    llm_config_paths = [
        original_metadata.get('llm_config', {}),
        original_metadata.get('parameters', {}),
        entry.get('parameters', {}),
        entry.get('llm_config', {})
    ]
    
    # Find the first non-empty LLM config
    llm_config = next((config for config in llm_config_paths if config), {})
    
    # Normalize keys to camelCase
    normalized_config = {
        'modelId': (
            llm_config.get('model_id') or 
            llm_config.get('modelId') or 
            llm_config.get('model') or 
            ''
        ),
        'temperature': (
            llm_config.get('temperature') or 
            llm_config.get('temp') or 
            None
        ),
        'topP': (
            llm_config.get('top_p') or 
            llm_config.get('topP') or 
            None
        ),
        'topK': (
            llm_config.get('top_k') or 
            llm_config.get('topK') or 
            None
        ),
        'maxLength': (
            llm_config.get('max_length') or 
            llm_config.get('maxLength') or 
            None
        ),
        'stopSequences': (
            llm_config.get('stop_sequences') or 
            llm_config.get('stopSequences') or 
            []
        )
    }
    
    # Update metadata with robust LLM config and version
    formatted_entry['metadata'] = {
        'version': version,
        'llm_config': normalized_config
    }
    
    # Enhanced logging for diagnostic purposes
    logger.debug(f"Original Entry Metadata: {json.dumps(original_metadata, indent=2)}")
    logger.debug(f"Extracted Metadata: {json.dumps(formatted_entry['metadata'], indent=2)}")
    
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

    # Robust metadata extraction and normalization
    original_metadata = formatted_entry.get('metadata', {})
    
    # Multiple paths for LLM config extraction
    llm_config_paths = [
        original_metadata.get('llm_config', {}),
        original_metadata.get('parameters', {}),
        entry.get('parameters', {}),
        entry.get('llm_config', {})
    ]
    
    # Find the first non-empty LLM config
    llm_config = next((config for config in llm_config_paths if config), {})
    
    # Normalize keys to camelCase
    normalized_config = {
        'modelId': (
            llm_config.get('model_id') or 
            llm_config.get('modelId') or 
            llm_config.get('model') or 
            ''
        ),
        'temperature': (
            llm_config.get('temperature') or 
            llm_config.get('temp') or 
            None
        ),
        'topP': (
            llm_config.get('top_p') or 
            llm_config.get('topP') or 
            None
        ),
        'topK': (
            llm_config.get('top_k') or 
            llm_config.get('topK') or 
            None
        ),
        'maxLength': (
            llm_config.get('max_length') or 
            llm_config.get('maxLength') or 
            None
        ),
        'stopSequences': (
            llm_config.get('stop_sequences') or 
            llm_config.get('stopSequences') or 
            []
        )
    }
    
    # Update metadata with robust LLM config
    formatted_entry['metadata'] = {
        'version': original_metadata.get('version', '1.0'),
        'llm_config': normalized_config
    }
    
    # Enhanced logging for diagnostic purposes
    logger.debug(f"Original Entry Metadata: {json.dumps(original_metadata, indent=2)}")
    logger.debug(f"Extracted Metadata: {json.dumps(formatted_entry['metadata'], indent=2)}")
    
    return formatted_entry

async def create_lexical_value_task(
    lemma: str,
    search_lemma: bool,
    task_id: str,
    db: AsyncSession,
    llm_config: Optional[Dict[str, Any]] = None
):
    """Background task for lexical value creation."""
    try:
        logger.info(f"Starting lexical value creation task for: {lemma}")
        logger.debug(f"Task parameters - lemma: {lemma}, search_lemma: {search_lemma}, task_id: {task_id}")
        logger.debug(f"LLM config: {llm_config}")
        
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
            task_id=task_id,
            llm_config=llm_config
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
        db,
        data.llmConfig.dict() if data.llmConfig else None
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
    version: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get a lexical value by its lemma."""
    try:
        logger.info(f"Getting lexical value for: {lemma} (version: {version})")
        lexical_service = LexicalService(db)
        entry = await lexical_service.get_lexical_value(lemma, version)
        
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
        
        # Log the entire version data structure
        logger.debug(f"Full Version Data Structure: {json.dumps(versions, indent=2)}")
        
        if versions:
            # Ensure consistent format for all versions
            formatted_versions = []
            for version in versions:
                # Log the entire version item
                logger.debug(f"Full Version Item: {json.dumps(version, indent=2)}")
                
                # More robust metadata extraction
                metadata = version.get('metadata', version)  # Fallback to entire version if no metadata
                logger.debug(f"Extracted Metadata: {json.dumps(metadata, indent=2)}")
                
                # Prioritize extracting LLM config from multiple possible locations
                llm_config = (
                    metadata.get('llm_config') or 
                    metadata.get('parameters') or 
                    version.get('parameters') or 
                    {}
                )
                logger.debug(f"Extracted LLM Config: {json.dumps(llm_config, indent=2)}")
                
                # Handle legacy versions that might not have the new metadata structure
                formatted_version = {
                    'version': version.get('version', ''),
                    'created_at': metadata.get('created_at', version.get('created_at', '')),
                    'updated_at': metadata.get('updated_at', version.get('updated_at', '')),
                    'model': (
                        llm_config.get('model_id') or 
                        llm_config.get('model') or 
                        metadata.get('model') or 
                        version.get('model', '')
                    ),
                    'parameters': {
                        'temperature': llm_config.get('temperature'),
                        'top_p': llm_config.get('top_p'),
                        'top_k': llm_config.get('top_k'),
                        'max_length': llm_config.get('max_length'),
                        'stop_sequences': llm_config.get('stop_sequences', [])
                    }
                }
                
                logger.info(f"Formatted Version: {json.dumps(formatted_version, indent=2)}")
                formatted_versions.append(formatted_version)
            
            logger.debug(f"Found {len(formatted_versions)} versions for {lemma}")
            return {"versions": formatted_versions}
            
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
@router.post("/list")
async def list_lexical_values(
    data: Optional[LexicalListSchema] = None,
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List lexical values with pagination. Supports both GET and POST methods."""
    try:
        # Use data from POST body if provided, otherwise use query parameters
        effective_offset = data.offset if data else offset
        effective_limit = data.limit if data else limit

        logger.info(f"Listing lexical values - offset: {effective_offset}, limit: {effective_limit}")
        lexical_service = LexicalService(db)
        result = await lexical_service.list_lexical_values(effective_offset, effective_limit)
        
        # Format values for response
        formatted_values = []
        if "results" in result:
            formatted_values = [format_entry_for_response(v) for v in result["results"]]
        
        logger.debug(f"Found {len(formatted_values)} lexical values")
        
        # Return with pagination metadata
        return {
            "values": formatted_values,
            "pagination": result.get("pagination", {})
        }
    except Exception as e:
        logger.error(f"Error listing lexical values: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "type": type(e).__name__,
                "offset": effective_offset,
                "limit": effective_limit
            }
        )

@router.put("/update/{lemma}")
async def update_lexical_value(
    lemma: str,
    data: LexicalUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing lexical value."""
    try:
        logger.info(f"Updating lexical value for: {lemma}")
        logger.debug(f"Update data: {json.dumps(data.dict(), indent=2)}")
        
        lexical_service = LexicalService(db)
        result = await lexical_service.update_lexical_value(
            lemma=lemma,
            data={},  # Empty data since we're regenerating with new LLM config
            llm_config=data.llmConfig.dict() if data.llmConfig else None
        )
        
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
