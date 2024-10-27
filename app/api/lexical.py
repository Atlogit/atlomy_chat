"""
API routes for lexical operations.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.dependencies import LexicalServiceDep

router = APIRouter()

# Request/Response Models
class LemmaCreate(BaseModel):
    lemma: str
    language_code: Optional[str] = None
    categories: Optional[List[str]] = None
    translations: Optional[Dict[str, Any]] = None

class LemmaBatchCreate(BaseModel):
    lemmas: List[LemmaCreate]

class LemmaUpdate(BaseModel):
    lemma: str
    translations: Optional[Dict[str, Any]] = None
    categories: Optional[List[str]] = None
    language_code: Optional[str] = None

class LemmaResponse(BaseModel):
    id: int
    lemma: str
    language_code: Optional[str]
    categories: List[str]
    translations: Optional[Dict[str, Any]]
    analyses: List[Dict[str, Any]]

class CreateResponse(BaseModel):
    success: bool
    message: str
    entry: Optional[Dict[str, Any]]
    action: str

# Routes
@router.post("/create", response_model=CreateResponse)
async def create_lexical_value(
    data: LemmaCreate,
    lexical_service: LexicalServiceDep
) -> Dict:
    """Create a new lexical value."""
    try:
        return await lexical_service.create_lemma(
            lemma=data.lemma,
            language_code=data.language_code,
            categories=data.categories,
            translations=data.translations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-create", response_model=List[CreateResponse])
async def batch_create_lexical_values(
    data: LemmaBatchCreate,
    lexical_service: LexicalServiceDep
) -> List[Dict]:
    """Create multiple lexical values in a batch."""
    try:
        results = []
        for lemma_data in data.lemmas:
            result = await lexical_service.create_lemma(
                lemma=lemma_data.lemma,
                language_code=lemma_data.language_code,
                categories=lemma_data.categories,
                translations=lemma_data.translations
            )
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get/{lemma}", response_model=LemmaResponse)
async def get_lexical_value(
    lemma: str,
    lexical_service: LexicalServiceDep
) -> Dict:
    """Get a lexical value by its lemma."""
    result = await lexical_service.get_lemma_by_text(lemma)
    if not result:
        raise HTTPException(status_code=404, detail="Lemma not found")
    return result

@router.get("/list", response_model=List[LemmaResponse])
async def list_lexical_values(
    lexical_service: LexicalServiceDep,
    language_code: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict]:
    """List all lexical values with optional filtering."""
    try:
        return await lexical_service.list_lemmas(
            language_code=language_code,
            category=category
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update", response_model=CreateResponse)
async def update_lexical_value(
    data: LemmaUpdate,
    lexical_service: LexicalServiceDep
) -> Dict:
    """Update an existing lexical value."""
    try:
        return await lexical_service.update_lemma(
            lemma=data.lemma,
            translations=data.translations,
            categories=data.categories,
            language_code=data.language_code
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{lemma}")
async def delete_lexical_value(
    lemma: str,
    lexical_service: LexicalServiceDep
) -> Dict:
    """Delete a lexical value."""
    success = await lexical_service.delete_lemma(lemma)
    if not success:
        raise HTTPException(status_code=404, detail="Lemma not found")
    return {"success": True, "message": "Lemma deleted successfully"}
