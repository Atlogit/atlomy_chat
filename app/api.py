from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os

from src.logging_config import initialize_logger, get_logger
from src.corpus_manager import CorpusManager
from src.lexical_value_generator import LexicalValueGenerator
from src.playground import LLMAssistant

# Initialize logging first
initialize_logger()
logger = get_logger()

# Initialize components
corpus_manager = CorpusManager()
llm_assistant = LLMAssistant(corpus_manager)
lexical_generator = LexicalValueGenerator(corpus_manager)

app = FastAPI()

# Serve static files from the root static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Models for request/response data
class Query(BaseModel):
    query: str

class LexicalCreate(BaseModel):
    word: str
    searchLemma: bool = False

class LexicalUpdate(BaseModel):
    lemma: str
    translation: str

class TextSearch(BaseModel):
    query: str
    searchLemma: bool = False

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# LLM Assistant endpoints
@app.post("/api/llm/query")
async def llm_query(query: Query):
    try:
        result = llm_assistant.ask_about_data(query.query)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in LLM query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Lexical Value endpoints
@app.post("/api/lexical/create")
async def create_lexical_value(data: LexicalCreate):
    try:
        entry = lexical_generator.create_lexical_entry(data.word, search_lemma=data.searchLemma)
        return entry.__dict__
    except Exception as e:
        logger.error(f"Error creating lexical value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lexical/get/{lemma}")
async def get_lexical_value(lemma: str):
    try:
        entry = lexical_generator.get_lexical_value(lemma)
        if entry:
            return entry.__dict__
        raise HTTPException(status_code=404, detail="Lexical value not found")
    except Exception as e:
        logger.error(f"Error getting lexical value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lexical/list")
async def list_lexical_values():
    try:
        values = lexical_generator.list_lexical_values()
        return {"values": values}
    except Exception as e:
        logger.error(f"Error listing lexical values: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/lexical/update")
async def update_lexical_value(data: LexicalUpdate):
    try:
        entry = lexical_generator.get_lexical_value(data.lemma)
        if not entry:
            raise HTTPException(status_code=404, detail="Lexical value not found")
        entry.translation = data.translation
        lexical_generator.update_lexical_value(entry)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error updating lexical value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/lexical/delete/{lemma}")
async def delete_lexical_value(lemma: str):
    try:
        success = lexical_generator.delete_lexical_value(lemma)
        if success:
            return {"success": True}
        raise HTTPException(status_code=404, detail="Lexical value not found")
    except Exception as e:
        logger.error(f"Error deleting lexical value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Corpus Manager endpoints
@app.get("/api/corpus/list")
async def list_texts():
    try:
        texts = corpus_manager.list_texts()
        return {"texts": texts}
    except Exception as e:
        logger.error(f"Error listing texts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/corpus/search")
async def search_texts(data: TextSearch):
    try:
        results = corpus_manager.search_texts(data.query, search_lemma=data.searchLemma)
        return {"results": results}
    except Exception as e:
        logger.error(f"Error searching texts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/corpus/all")
async def get_all_texts():
    try:
        texts = corpus_manager.get_all_texts()
        return {"texts": texts}
    except Exception as e:
        logger.error(f"Error getting all texts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
