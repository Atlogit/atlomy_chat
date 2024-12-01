"""
LLM service for SQL query generation with enhanced error handling and connection management.
"""

from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy import text
from sqlalchemy.exc import (
    SQLAlchemyError, 
    DatabaseError, 
    OperationalError, 
    InterfaceError, 
    PendingRollbackError
)
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
import logging
import asyncio
import time
import json
import re
import uuid

from app.services.llm.base_service import BaseLLMService, LLMServiceError
from app.services.llm.prompts import (
    QUERY_TEMPLATE,
    LEMMA_QUERY_TEMPLATE,
    CATEGORY_QUERY_TEMPLATE
)
from app.models.citations import Citation
from app.services.citation_service import CitationService

# Configure logging
logger = logging.getLogger(__name__)

class QueryType:
    """Enum-like class for query types."""
    NATURAL_LANGUAGE = "natural_language"
    LEMMA = "lemma"
    CATEGORY = "category"

class QueryLLMService(BaseLLMService):
    """
    Enhanced service for SQL query generation with robust connection management.
    """

    def __init__(self, session, citation_service: CitationService):
        """Initialize with database session and citation service."""
        super().__init__(session)
        self.citation_service = citation_service
        self.CHUNK_SIZE = 10000  # Process results in chunks
        self.QUERY_TIMEOUT = 900  # 15 minutes maximum query execution time
        self.MAX_RETRIES = 3  # Maximum connection retry attempts
        self.RETRY_DELAY = 2  # Base delay between retries

    async def _safe_execute_query(
        self, 
        query: str, 
        trace_id: str, 
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Safely execute a database query with comprehensive error handling.
        
        Args:
            query: SQL query to execute
            trace_id: Unique trace identifier for logging
            max_retries: Maximum number of retry attempts
        
        Returns:
            List of query results as dictionaries
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                # Create a new session for each attempt to ensure clean state
                async with AsyncSession(self.session.bind, expire_on_commit=False) as db_session:
                    logger.info(f"[{trace_id}] Executing query (Attempt {attempt + 1})")
                    
                    try:
                        # Rollback any pending transactions
                        await db_session.rollback()
                    except Exception as rollback_error:
                        logger.warning(
                            f"[{trace_id}] Error during pre-query rollback: {str(rollback_error)}"
                        )
                    
                    # Execute query with timeout
                    result = await asyncio.wait_for(
                        db_session.execute(text(query)),
                        timeout=self.QUERY_TIMEOUT
                    )
                    
                    # Commit transaction
                    await db_session.commit()
                    
                    # Convert results to list of dictionaries
                    rows = result.mappings().all()
                    
                    logger.info(f"[{trace_id}] Query successful. Rows: {len(rows)}")
                    return rows
            
            except (
                InterfaceError, 
                OperationalError, 
                PendingRollbackError
            ) as connection_error:
                logger.warning(
                    f"[{trace_id}] Connection error on attempt {attempt + 1}: {str(connection_error)}"
                )
                last_error = connection_error
                
                # Exponential backoff
                await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))
            
            except asyncio.TimeoutError:
                logger.error(
                    f"[{trace_id}] Query timeout on attempt {attempt + 1}. "
                    f"Timeout: {self.QUERY_TIMEOUT} seconds"
                )
                if attempt == max_retries - 1:
                    raise LLMServiceError(
                        "Query execution timed out",
                        {
                            "trace_id": trace_id,
                            "message": f"Query took longer than {self.QUERY_TIMEOUT} seconds",
                            "error_type": "query_timeout"
                        }
                    )
            
            except (SQLAlchemyError, DatabaseError) as db_error:
                logger.error(
                    f"[{trace_id}] Database error on attempt {attempt + 1}: {str(db_error)}", 
                    exc_info=True
                )
                last_error = db_error
                
                # Exponential backoff
                await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))
        
        # If all retries fail
        logger.error(
            f"[{trace_id}] Failed to execute query after {max_retries} attempts. "
            f"Last error: {str(last_error)}"
        )
        raise LLMServiceError(
            "Persistent database connection error",
            {
                "trace_id": trace_id,
                "message": "Could not establish a stable database connection",
                "error_type": "connection_failure",
                "last_error": str(last_error)
            }
        )

    async def generate_and_execute_query(
        self,
        question: str, 
        query_type: str = QueryType.NATURAL_LANGUAGE,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate and execute a SQL query with enhanced error handling and consistent return structure.
        
        Returns a dictionary with comprehensive query result information.
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Standardized result structure
        result_template = {
            "sql": "",
            "results": [],
            "results_id": "",
            "total_results": 0,
            "usage": {},
            "model": "",
            "raw_response": None,
            "error": None
        }

        try:
            # Determine query generation method based on type
            if query_type == QueryType.LEMMA:
                response = await self.generate_lemma_query(question, max_tokens)
            elif query_type == QueryType.CATEGORY:
                response = await self.generate_category_query(question, max_tokens)
            else:
                response = await self.generate_query(question, max_tokens)
            
            sql_query = response.text.strip()
            result_template["sql"] = sql_query
            
            logger.info(f"[{trace_id}] Generated {query_type} query: {sql_query}")

            # Execute query with safe execution
            try:
                rows = await self._safe_execute_query(sql_query, trace_id)
                total_rows = len(rows)
                result_template["total_results"] = total_rows

                # Handle no results scenario
                if total_rows == 0:
                    if query_type == QueryType.NATURAL_LANGUAGE:
                        no_results_metadata = await self._analyze_no_results(question, sql_query)
                        result_template["error"] = "No results found"
                        result_template["raw_response"] = no_results_metadata
                    return result_template

                # Process results in chunks
                results_id = None
                first_page = None
                processed_rows = 0

                for chunk_start in range(0, total_rows, self.CHUNK_SIZE):
                    chunk_end = min(chunk_start + self.CHUNK_SIZE, total_rows)
                    chunk_rows = rows[chunk_start:chunk_end]
                    
                    try:
                        chunk_results_id, chunk_first_page = await self.citation_service.format_citations(
                            chunk_rows, 
                            total_results=total_rows
                        )
                        
                        logger.info(
                            f"[{trace_id}] Citation chunk {chunk_start}-{chunk_end}: "
                            f"Results ID: {chunk_results_id}, "
                            f"First Page Length: {len(chunk_first_page)}"
                        )
                        
                        # Use first chunk's results
                        if results_id is None:
                            results_id = chunk_results_id
                            first_page = chunk_first_page
                        
                        processed_rows += len(chunk_rows)
                    
                    except Exception as format_error:
                        logger.error(
                            f"[{trace_id}] Citation formatting error for chunk {chunk_start}-{chunk_end}: "
                            f"{str(format_error)}", 
                            exc_info=True
                        )
                        continue
                
                # Log performance metrics
                execution_time = time.time() - start_time
                logger.info(
                    f"[{trace_id}] Query processed. "
                    f"Total Rows: {total_rows}, "
                    f"Processed Rows: {processed_rows}, "
                    f"Execution Time: {execution_time:.2f}s, "
                    f"Results ID: {results_id}"
                )

                # Validate results
                if total_rows > 0 and (not results_id or not first_page):
                    logger.error(
                        f"[{trace_id}] Failed to process query results. "
                        f"Results ID: {results_id}, First Page: {first_page}"
                    )
                    result_template["error"] = "Failed to process query results"
                    return result_template

                # Populate result template
                result_template["results_id"] = results_id or ""
                result_template["results"] = first_page or []
                result_template["usage"] = {
                    "total_rows": total_rows,
                    "processed_rows": processed_rows,
                    "execution_time": execution_time
                }
                
                return result_template
            
            except Exception as query_error:
                logger.error(
                    f"[{trace_id}] Query execution error: {str(query_error)}", 
                    exc_info=True
                )
                result_template["error"] = str(query_error)
                return result_template

        except Exception as e:
            logger.error(
                f"[{trace_id}] Unexpected error in query processing: {str(e)}", 
                exc_info=True
            )
            result_template["error"] = str(e)
            return result_template

    async def generate_query(
        self,
        question: str,
        max_tokens: Optional[int] = None
    ):
        """Generate a SQL query based on a natural language question."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": QUERY_TEMPLATE.format(question=question)}
                ]
            }
        ]
        response = await self.client.generate(
            messages=messages,
            max_tokens=max_tokens,
            system_prompt="You are an expert SQL query generator. Generate precise and efficient SQL queries based on the given natural language question."
        )
        return response

    async def generate_lemma_query(
        self,
        lemma: str,
        max_tokens: Optional[int] = None
    ):
        """Generate a SQL query for lemma search."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": LEMMA_QUERY_TEMPLATE.format(lemma=lemma)}
                ]
            }
        ]
        response = await self.client.generate(
            messages=messages,
            max_tokens=max_tokens,
            system_prompt="You are an expert SQL query generator. Generate precise queries to search for lemmas in the database."
        )
        return response

    async def generate_category_query(
        self,
        category: str,
        max_tokens: Optional[int] = None
    ):
        """Generate a SQL query for category search."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": CATEGORY_QUERY_TEMPLATE.format(category=category)}
                ]
            }
        ]
        response = await self.client.generate(
            messages=messages,
            max_tokens=max_tokens,
            system_prompt="You are an expert SQL query generator. Generate precise queries to search for categories in the database."
        )
        return response


    async def _analyze_no_results(self, question: str, sql_query: str) -> Dict[str, Any]:
        """
        Analyze the SQL query to explain what was being searched for when no results were found.
        """
        no_results_metadata = {
            "original_question": question,
            "generated_query": sql_query,
            "search_description": f"Searching based on: {question}",
            "search_criteria": {}
        }

        try:
            # Extract the WHERE clause to show what was being searched
            where_match = re.search(r'WHERE\s+(.+?)(?:\n|$)', sql_query, re.DOTALL | re.IGNORECASE)
            
            if where_match:
                where_clause = where_match.group(1).strip()
                
                # Clean up the WHERE clause to make it more readable
                where_clause = re.sub(r'\s+', ' ', where_clause)  # Normalize whitespace
                where_clause = re.sub(r'\s*AND\s*', ' and ', where_clause)  # Standardize AND
                
                no_results_metadata['search_description'] = f"Searching with conditions: {where_clause}"
                
                # Try to extract any specific conditions
                conditions = re.findall(r'(\w+)\s*(?:ILIKE|=|>|<|>=|<=)\s*[\'"]?([^\'"\s]+)[\'"]?', where_clause)
                no_results_metadata['search_criteria'] = dict(conditions)
        except Exception as e:
            logger.error(f"Error analyzing no results metadata: {str(e)}")

        return no_results_metadata
