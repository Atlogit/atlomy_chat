from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import asyncio

from src.logging_config import initialize_logger, get_logger
from src.corpus_manager import CorpusManager
from src.lexical_value_generator import LexicalValueGenerator
from src.playground import LLMAssistant

# Initialize logging first
initialize_logger()
logger = get_logger()

logger.debug("Initializing components...")
# Initialize components
corpus_manager = CorpusManager()
llm_assistant = LLMAssistant(corpus_manager)
lexical_generator = LexicalValueGenerator(corpus_manager)
logger.debug("Components initialized successfully")

app = FastAPI()

logger.debug("Setting up CORS middleware...")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from the Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
logger.debug("CORS middleware set up successfully")

# Serve static files from the root static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Models for request/response data
class Query(BaseModel):
    query: str

class LexicalCreate(BaseModel):
    lemma: str
    searchLemma: bool = False

class LexicalBatchCreate(BaseModel):
    words: List[str]
    searchLemma: bool = False

class LexicalUpdate(BaseModel):
    lemma: str
    translation: str

class LexicalBatchUpdate(BaseModel):
    updates: List[Dict[str, str]]

class TextSearch(BaseModel):
    query: str
    searchLemma: bool = False

# In-memory storage for task status
task_status = {}

@app.get("/")
async def root():
    logger.debug("Serving root endpoint")
    return FileResponse("static/index.html")

# LLM Assistant endpoints
@app.post("/api/llm/query")
async def llm_query(query: Query):
    logger.debug(f"Received LLM query: {query.query}")
    try:
        result = llm_assistant.ask_about_data(query.query)
        logger.debug(f"LLM query result: {result}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in LLM query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Lexical Value endpoints
async def create_lexical_value_task(lemma: str, search_lemma: bool, task_id: str):
    try:
        logger.info(f"Starting lexical value creation task for: {lemma}")
        task_status[task_id] = {"status": "in_progress", "message": "Creating lexical value"}
        
        existing_entry = lexical_generator.get_lexical_value(lemma)
        if existing_entry:
            logger.info(f"Lexical value already exists: {lemma}")
            task_status[task_id] = {
                "status": "completed",
                "success": False,
                "message": "Lexical value already exists",
                "entry": existing_entry.__dict__,
                "action": "update"
            }
            return
        
        logger.info(f"Creating new lexical entry: {lemma}")
        new_entry = lexical_generator.generate_lexical_term(lemma, lexical_generator.get_citations(lemma, search_lemma=search_lemma))
        if new_entry is None:
            logger.error(f"Failed to create lexical entry for '{lemma}'")
            task_status[task_id] = {
                "status": "completed",
                "success": False,
                "message": "Failed to create lexical entry",
                "entry": None,
                "action": "create"
            }
            return
        
        # Store the new entry
        logger.info(f"Storing new lexical entry: {new_entry}")
        lexical_generator.storage.store(new_entry)
        
        logger.info(f"New lexical entry created and stored: {new_entry}")
        task_status[task_id] = {
            "status": "completed",
            "success": True,
            "message": "Lexical value created successfully",
            "entry": new_entry.__dict__,
            "action": "create"
        }
    except Exception as e:
        logger.error(f"Error creating lexical value: {str(e)}")
        task_status[task_id] = {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/lexical/create")
async def create_lexical_value(data: LexicalCreate, background_tasks: BackgroundTasks):
    task_id = f"create_{data.lemma}_{asyncio.get_event_loop().time()}"
    background_tasks.add_task(create_lexical_value_task, data.lemma, data.searchLemma, task_id)
    return {"task_id": task_id, "message": "Lexical value creation started"}

@app.get("/api/lexical/status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_status[task_id]

@app.get("/api/lexical/get/{lemma}")
async def get_lexical_value(lemma: str):
    logger.debug(f"Getting lexical value for lemma: {lemma}")
    try:
        entry = lexical_generator.get_lexical_value(lemma)
        if entry:
            logger.debug(f"Lexical value found for lemma: {lemma}")
            return entry.__dict__
        logger.debug(f"Lexical value not found for lemma: {lemma}")
        raise HTTPException(status_code=404, detail="Lexical value not found")
    except Exception as e:
        logger.error(f"Error getting lexical value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lexical/list")
async def list_lexical_values():
    logger.debug("Listing all lexical values")
    try:
        values = lexical_generator.list_lexical_values()
        logger.debug(f"Found {len(values)} lexical values")
        return {"values": values}
    except Exception as e:
        logger.error(f"Error listing lexical values: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/lexical/update")
async def update_lexical_value(data: LexicalUpdate):
    logger.debug(f"Updating lexical value for lemma: {data.lemma}")
    try:
        entry = lexical_generator.get_lexical_value(data.lemma)
        if not entry:
            logger.debug(f"Lexical value not found for update: {data.lemma}")
            raise HTTPException(status_code=404, detail="Lexical value not found")
        entry.translation = data.translation
        lexical_generator.update_lexical_value(entry)
        logger.debug(f"Lexical value updated for lemma: {data.lemma}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error updating lexical value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/lexical/delete/{lemma}")
async def delete_lexical_value(lemma: str):
    logger.debug(f"Deleting lexical value for lemma: {lemma}")
    try:
        success = lexical_generator.delete_lexical_value(lemma)
        if success:
            logger.debug(f"Lexical value deleted for lemma: {lemma}")
            return {"success": True}
        logger.debug(f"Lexical value not found for deletion: {lemma}")
        raise HTTPException(status_code=404, detail="Lexical value not found")
    except Exception as e:
        logger.error(f"Error deleting lexical value: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Corpus Manager endpoints
@app.get("/api/corpus/list")
async def list_texts():
    logger.debug("Listing all texts in corpus")
    try:
        texts = corpus_manager.list_texts()
        logger.debug(f"Found {len(texts)} texts in corpus")
        return {"texts": texts}
    except Exception as e:
        logger.error(f"Error listing texts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/corpus/search")
async def search_texts(data: TextSearch):
    logger.debug(f"Searching texts with query: {data.query}, search_lemma: {data.searchLemma}")
    try:
        results = corpus_manager.search_texts(data.query, search_lemma=data.searchLemma)
        logger.debug(f"Found {len(results)} results for the search query")
        return {"results": results}
    except Exception as e:
        logger.error(f"Error searching texts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/corpus/all")
async def get_all_texts():
    logger.debug("Getting all texts from corpus")
    try:
        texts = corpus_manager.get_all_texts()
        logger.debug(f"Retrieved {len(texts)} texts from corpus")
        return {"texts": texts}
    except Exception as e:
        logger.error(f"Error getting all texts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.debug("Starting Uvicorn server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
