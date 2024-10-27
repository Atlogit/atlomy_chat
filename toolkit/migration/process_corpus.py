"""
CLI script for processing the entire corpus through the NLP pipeline.

This script coordinates the processing of all texts in the corpus,
splitting them into sentences and running NLP analysis.
"""

import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional
from tqdm import tqdm

from app.core.database import async_session
from toolkit.migration.corpus_processor import CorpusProcessor
from toolkit.migration.parallel_processor import ParallelProcessor
from toolkit.migration.logging_config import setup_migration_logging, get_migration_logger

async def process_corpus(
    model_path: Optional[str] = None, 
    batch_size: int = 100,
    parallel: bool = False,
    max_workers: Optional[int] = None
) -> None:
    """Process all texts in the corpus through the NLP pipeline.
    
    Args:
        model_path: Optional path to spaCy model
        batch_size: Size of batches for processing
        parallel: Whether to use parallel processing
        max_workers: Maximum number of worker processes for parallel processing
    """
    logger = get_migration_logger('process_corpus')
    logger.info(f"Starting corpus processing (parallel={parallel})")
    
    try:
        async with async_session() as session:
            if parallel:
                processor = ParallelProcessor(session, model_path, max_workers)
                await processor.process_corpus_parallel(batch_size)
                
                # Get final status
                status = await processor.get_processing_status()
                logger.info(f"Processing completed: {status['completion_percentage']:.2f}% of divisions processed")
                
            else:
                processor = CorpusProcessor(session, model_path)
                await processor.process_corpus()
                logger.info("Sequential processing completed successfully")
            
    except Exception as e:
        logger.error(f"Error during corpus processing: {str(e)}")
        raise

def main():
    """Main entry point for corpus processing."""
    parser = argparse.ArgumentParser(description="Process corpus texts through NLP pipeline")
    parser.add_argument(
        '--model-path',
        help='Path to spaCy model',
        default=None
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        help='Batch size for processing',
        default=100
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Enable parallel processing'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        help='Maximum number of worker processes for parallel processing',
        default=None
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set the logging level'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_migration_logging(level=args.log_level)
    logger = get_migration_logger('process_corpus')
    
    try:
        asyncio.run(process_corpus(
            args.model_path,
            args.batch_size,
            args.parallel,
            args.max_workers
        ))
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
