"""
LLM service for SQL query generation with enhanced error handling and performance.
"""

from typing import Dict, Any, Optional, Tuple, List, Generator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
import logging
import asyncio
import time
import json

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

    async def generate_and_execute_query(
            self,
            question: str,
            max_tokens: Optional[int] = None
        ) -> Tuple[str, str, List[Citation]]:
            """
            Generate and execute a SQL query with enhanced error handling and performance tracking.
            """
            start_time = time.time()
            sql_query = ""
            progress_callback = None

            try:
                # Generate the SQL query
                response = await self.generate_query(question, max_tokens)
                sql_query = response.text.strip()
                logger.info(f"Generated SQL query: {sql_query}")

                # Execute the query with extended timeout
                try:
                    # Use asyncio.wait_for to implement query timeout
                    result = await asyncio.wait_for(
                        self.session.execute(text(sql_query)),
                        timeout=self.QUERY_TIMEOUT
                    )
                    rows = result.mappings().all()

                    total_rows = len(rows)
                    logger.info(f"Query returned {total_rows} rows")

                    # If no results, return empty results instead of raising an error
                    if total_rows == 0:
                        logger.info("Query returned no results")
                        return sql_query, "", []
                    
                    # Detailed progress tracking
                    def track_progress(current, total):
                        progress_data = {
                            'current': current,
                            'total': total,
                            'stage': 'Processing citations',
                            'percentage': round((current / total) * 100, 2) if total > 0 else 0
                        }
                        logger.info(f"Progress: {json.dumps(progress_data)}")
                    
                    # Process results in chunks to prevent memory issues
                    results_id = None
                    first_page = None
                    processed_rows = 0

                    for chunk_start in range(0, total_rows, self.CHUNK_SIZE):
                        chunk_end = min(chunk_start + self.CHUNK_SIZE, total_rows)
                        chunk_rows = rows[chunk_start:chunk_end]
                        
                        # Format citations for this chunk
                        try:
                            chunk_results_id, chunk_first_page = await self.citation_service.format_citations(
                                chunk_rows, 
                                total_results=total_rows
                            )
                            
                            # Use the first chunk's results_id and first page
                            if results_id is None:
                                results_id = chunk_results_id
                                first_page = chunk_first_page
                            
                            # Update processed rows and track progress
                            processed_rows += len(chunk_rows)
                            track_progress(processed_rows, total_rows)
                            
                            logger.info(
                                f"Processed chunk {chunk_start}-{chunk_end} of {total_rows} rows. "
                                f"Results ID: {chunk_results_id}"
                            )
                        
                        except Exception as format_error:
                            logger.error(
                                f"Error formatting citations for chunk {chunk_start}-{chunk_end}: {str(format_error)}", 
                                exc_info=True
                            )
                            # Continue processing other chunks if possible
                            continue
                    
                    # Log overall query performance
                    execution_time = time.time() - start_time
                    logger.info(
                        f"Query processed successfully. "
                        f"Total Rows: {total_rows}, "
                        f"Processed Rows: {processed_rows}, "
                        f"Execution Time: {execution_time:.2f} seconds, "
                        f"Results ID: {results_id}"
                    )

                    # For successful queries with results, ensure we have processed data
                    if total_rows > 0 and (not results_id or not first_page):
                        raise LLMServiceError(
                            "Failed to process query results",
                            {
                                "message": "Could not generate results ID or first page",
                                "error_type": "citation_format_error",
                                "sql_query": sql_query,
                                "row_count": total_rows
                            }
                        )

                    return sql_query, results_id or "", first_page or []
                
                except asyncio.TimeoutError:
                    logger.error(
                        f"Query execution timed out after {self.QUERY_TIMEOUT} seconds"
                    )
                    raise LLMServiceError(
                        "Query execution timed out",
                        {
                            "message": f"Query took longer than {self.QUERY_TIMEOUT} seconds",
                            "error_type": "query_timeout",
                            "sql_query": sql_query
                        }
                    )

                except SQLAlchemyError as db_error:
                    logger.error(
                        f"Database error executing query: {str(db_error)}", 
                        exc_info=True
                    )
                    raise LLMServiceError(
                        "Error executing SQL query",
                        {
                            "message": str(db_error),
                            "error_type": "database_error",
                            "sql_query": sql_query
                        }
                    )

            except Exception as e:
                logger.error(
                    f"Unexpected error in query generation/execution: {str(e)}", 
                    exc_info=True
                )
                raise LLMServiceError(
                    "Unexpected error in query processing",
                    {
                        "message": str(e),
                        "error_type": "unexpected_error",
                        "sql_query": sql_query
                    }
                )

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
