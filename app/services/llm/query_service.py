"""
LLM service for SQL query generation with enhanced error handling and performance.
"""

from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession
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

class QueryLLMService(BaseLLMService):
    """
    Enhanced service for SQL query generation with improved error handling and performance.
    """

    def __init__(self, session, citation_service: CitationService):
        """Initialize with database session and citation service."""
        super().__init__(session)
        self.citation_service = citation_service
        self.CHUNK_SIZE = 10000  # Process results in chunks
        self.QUERY_TIMEOUT = 900  # 15 minutes maximum query execution time
        self.PROGRESS_UPDATE_INTERVAL = 1000  # Update progress every 1000 rows

    async def _safe_execute_query(
        self, 
        query: str, 
        trace_id: str, 
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Safely execute a database query with retry mechanism.
        
        Args:
            query: SQL query to execute
            trace_id: Unique trace identifier for logging
            max_retries: Maximum number of retry attempts
        
        Returns:
            List of query results as dictionaries
        """
        for attempt in range(max_retries):
            try:
                # Use a new session to avoid connection state issues
                async with AsyncSession(self.session.bind, expire_on_commit=False) as db_session:
                    logger.info(f"[{trace_id}] Executing query (Attempt {attempt + 1})")
                    
                    # Execute with timeout
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
            
            except asyncio.TimeoutError:
                logger.warning(
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
                if attempt == max_retries - 1:
                    raise LLMServiceError(
                        "Error executing SQL query",
                        {
                            "trace_id": trace_id,
                            "message": str(db_error),
                            "error_type": "database_error"
                        }
                    )
                
                # Wait before retry with exponential backoff
                await asyncio.sleep(2 ** attempt)

    async def generate_and_execute_query(
            self,
            question: str,
            max_tokens: Optional[int] = None
        ) -> Tuple[str, str, List[Citation], Dict[str, Any]]:
            """
            Generate and execute a SQL query with enhanced error handling and performance tracking.
            """
            trace_id = str(uuid.uuid4())
            start_time = time.time()
            sql_query = ""
            no_results_metadata = {}

            try:
                # Log query generation start
                logger.info(f"[{trace_id}] Generating query for: {question}")

                # Generate SQL query
                response = await self.generate_query(question, max_tokens)
                sql_query = response.text.strip()
                logger.info(f"[{trace_id}] Generated SQL query: {sql_query}")

                # Execute query safely
                try:
                    rows = await self._safe_execute_query(sql_query, trace_id)
                    total_rows = len(rows)

                    # Handle no results scenario
                    if total_rows == 0:
                        no_results_metadata = await self._analyze_no_results(question, sql_query)
                        logger.warning(f"[{trace_id}] No results found. Metadata: {no_results_metadata}")
                        return sql_query, "", [], no_results_metadata

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
                        raise LLMServiceError(
                            "Failed to process query results",
                            {
                                "trace_id": trace_id,
                                "message": "Could not generate results ID or first page",
                                "error_type": "citation_format_error",
                                "row_count": total_rows
                            }
                        )

                    return sql_query, results_id or "", first_page or [], {}
                
                except Exception as query_error:
                    logger.error(
                        f"[{trace_id}] Query execution error: {str(query_error)}", 
                        exc_info=True
                    )
                    raise

            except Exception as e:
                logger.error(
                    f"[{trace_id}] Unexpected error in query processing: {str(e)}", 
                    exc_info=True
                )
                raise LLMServiceError(
                    "Unexpected error in query processing",
                    {
                        "trace_id": trace_id,
                        "message": str(e),
                        "error_type": "unexpected_error"
                    }
                )

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

    # Existing methods remain unchanged
    async def generate_query(
        self,
        question: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a SQL query based on a natural language question."""
        prompt = QUERY_TEMPLATE.format(question=question)
        response = await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
        return response

    async def generate_lemma_query(
        self,
        lemma: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a SQL query for lemma search."""
        prompt = LEMMA_QUERY_TEMPLATE.format(lemma=lemma)
        response = await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
        return response

    async def generate_category_query(
        self,
        category: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a SQL query for category search."""
        prompt = CATEGORY_QUERY_TEMPLATE.format(category=category)
        response = await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
        return response
