"""
Complete pipeline script for loading texts and processing them through NLP.

This script coordinates the entire process:
1. Verifying NLP pipeline
2. Loading texts into database
3. Migrating citations and relationships
4. Processing texts into sentences
5. Running NLP on sentences
6. Validating the results
"""

import asyncio
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from toolkit.loader.database import DatabaseLoader
from toolkit.loader.parallel_loader import ParallelDatabaseLoader
from toolkit.migration.parallel_processor import ParallelProcessor
from toolkit.migration.citation_migrator import CitationMigrator
from toolkit.migration.content_validator import DataVerifier
from toolkit.migration.corpus_processor import CorpusProcessor
from toolkit.nlp.pipeline import NLPPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineReport:
    """Tracks and reports issues during pipeline execution."""
    
    def __init__(self):
        self.loading_issues: List[Dict] = []
        self.citation_issues: List[Dict] = []
        self.sentence_issues: List[Dict] = []
        self.nlp_issues: List[Dict] = []
        self.validation_issues: List[Dict] = []
        self.start_time = datetime.now()
        
    def add_loading_issue(self, text_title: str, error: str):
        self.loading_issues.append({
            "text": text_title,
            "error": str(error),
            "stage": "loading"
        })
        
    def add_citation_issue(self, text_title: str, error: str):
        self.citation_issues.append({
            "text": text_title,
            "error": str(error),
            "stage": "citation_migration"
        })
        
    def add_sentence_issue(self, text_title: str, error: str):
        self.sentence_issues.append({
            "text": text_title,
            "error": str(error),
            "stage": "sentence_processing"
        })
        
    def add_nlp_issue(self, text_title: str, error: str):
        self.nlp_issues.append({
            "text": text_title,
            "error": str(error),
            "stage": "nlp_processing"
        })
        
    def add_validation_issue(self, text_title: str, error: str):
        self.validation_issues.append({
            "text": text_title,
            "error": str(error),
            "stage": "validation"
        })
    
    def generate_report(self) -> str:
        """Generate a formatted report of all issues."""
        duration = datetime.now() - self.start_time
        
        report = [
            "\n=== Pipeline Execution Report ===",
            f"Execution time: {duration}",
            "\nIssues Summary:",
            f"- Loading issues: {len(self.loading_issues)}",
            f"- Citation migration issues: {len(self.citation_issues)}",
            f"- Sentence processing issues: {len(self.sentence_issues)}",
            f"- NLP processing issues: {len(self.nlp_issues)}",
            f"- Validation issues: {len(self.validation_issues)}"
        ]
        
        if self.loading_issues:
            report.extend([
                "\nLoading Issues:",
                *[f"- {issue['text']}: {issue['error']}" 
                  for issue in self.loading_issues]
            ])
            
        if self.citation_issues:
            report.extend([
                "\nCitation Migration Issues:",
                *[f"- {issue['text']}: {issue['error']}" 
                  for issue in self.citation_issues]
            ])
            
        if self.sentence_issues:
            report.extend([
                "\nSentence Processing Issues:",
                *[f"- {issue['text']}: {issue['error']}" 
                  for issue in self.sentence_issues]
            ])
            
        if self.nlp_issues:
            report.extend([
                "\nNLP Processing Issues:",
                *[f"- {issue['text']}: {issue['error']}" 
                  for issue in self.nlp_issues]
            ])
            
        if self.validation_issues:
            report.extend([
                "\nValidation Issues:",
                *[f"- {issue['text']}: {issue['error']}" 
                  for issue in self.validation_issues]
            ])
            
        return "\n".join(report)
    
    def save_report(self, output_dir: Path):
        """Save the report to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"pipeline_report_{timestamp}.txt"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, "w") as f:
            f.write(self.generate_report())
        
        logger.info(f"Pipeline report saved to: {report_path}")

async def verify_nlp_pipeline(model_path: Optional[str], use_gpu: Optional[bool]) -> None:
    """Verify that the NLP pipeline works with the given settings."""
    logger.info("Verifying NLP pipeline...")
    try:
        # Initialize pipeline with specified settings
        nlp = NLPPipeline(model_path=model_path, use_gpu=use_gpu)
        
        # Test process with a sample text
        test_text = "This is a test sentence to verify the NLP pipeline."
        result = nlp.process_text(test_text)
        
        # Check if processing worked
        if not result or not result.get("tokens"):
            raise ValueError("NLP pipeline failed to process test text")
            
        # Log success with GPU status
        if use_gpu:
            logger.info("✓ NLP pipeline verified (GPU mode)")
        else:
            logger.info("✓ NLP pipeline verified (CPU mode)")
            
    except Exception as e:
        logger.error(f"NLP pipeline verification failed: {str(e)}")
        raise

async def run_pipeline(
    corpus_dir: Path,
    model_path: Optional[str] = None,
    batch_size: int = 1000,
    max_workers: Optional[int] = None,
    validate: bool = True,
    parallel_loading: bool = False,
    loading_batch_size: int = 5,
    use_gpu: Optional[bool] = None
):
    """
    Run the complete pipeline from loading to processing.
    
    Args:
        corpus_dir: Directory containing corpus texts
        model_path: Optional path to spaCy model
        batch_size: Size of batches for NLP processing
        max_workers: Maximum number of worker processes
        validate: Whether to run validation after processing
        parallel_loading: Whether to use parallel loading for texts
        loading_batch_size: Batch size for parallel loading
        use_gpu: Whether to use GPU for NLP processing (None for auto-detect)
    """
    # Initialize report tracker
    report = PipelineReport()
    
    try:
        # Verify NLP pipeline first
        await verify_nlp_pipeline(model_path, use_gpu)
        
        # Initialize database connection
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            echo=settings.DEBUG
        )
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Phase 1: Load texts into database
            logger.info("Phase 1: Loading texts...")
            try:
                if parallel_loading:
                    logger.info(f"Using parallel loading with {max_workers} workers")
                    loader = ParallelDatabaseLoader(
                        session,
                        max_workers=max_workers or 4,
                        batch_size=loading_batch_size
                    )
                    await loader.load_corpus_directory_parallel(corpus_dir)
                else:
                    logger.info("Using standard sequential loading")
                    loader = DatabaseLoader(session)
                    await loader.load_corpus_directory(corpus_dir)
                
                await session.commit()
                logger.info("Text loading completed")
            except Exception as e:
                report.add_loading_issue("corpus_directory", str(e))
                logger.error(f"Error during text loading: {e}")
                raise

            # Phase 2: Migrate citations
            logger.info("Phase 2: Migrating citations...")
            try:
                citation_migrator = CitationMigrator(session)
                await citation_migrator.migrate_directory(corpus_dir)
                logger.info("Citation migration completed")
            except Exception as e:
                report.add_citation_issue("corpus_directory", str(e))
                logger.error(f"Error during citation migration: {e}")
                raise

            # Phase 3: Process sentences and NLP
            logger.info("Phase 3: Processing sentences and NLP...")
            try:
                processor = ParallelProcessor(
                    session,
                    model_path=model_path,
                    max_workers=max_workers,
                    use_gpu=use_gpu
                )
                await processor.process_corpus_parallel(batch_size=batch_size)
            except Exception as e:
                report.add_sentence_issue("corpus_processing", str(e))
                logger.error(f"Error during sentence/NLP processing: {e}")
                raise
            
            # Phase 4: Validate results if requested
            if validate:
                logger.info("Phase 4: Validation...")
                verifier = DataVerifier(session)
                try:
                    validation_results = await verifier.run_all_verifications()
                    
                    # Log validation results
                    logger.info("Validation Results:")
                    
                    if validation_results["relationship_errors"]:
                        for error in validation_results["relationship_errors"]:
                            report.add_validation_issue("relationships", error)
                            
                    if validation_results["content_integrity_issues"]:
                        for issue in validation_results["content_integrity_issues"]:
                            report.add_validation_issue("content_integrity", 
                                f"{issue['type']} in {issue['entity']}: {issue.get('reference_code', issue.get('id', 'Unknown'))}")
                            
                    if validation_results["line_continuity_issues"]:
                        for issue in validation_results["line_continuity_issues"]:
                            report.add_validation_issue("line_continuity", 
                                f"Division {issue['division_id']}: Expected line {issue['expected']}, found {issue['found']}")
                            
                    if validation_results["incomplete_texts"]:
                        for issue in validation_results["incomplete_texts"]:
                            report.add_validation_issue("incomplete_text", 
                                f"Text {issue['text_id']}: {issue['issue']}")
                        
                except Exception as e:
                    report.add_validation_issue("validation_process", str(e))
                    logger.error(f"Error during validation: {e}")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise
    finally:
        await engine.dispose()
        
        # Save the execution report
        report.save_report(corpus_dir / "pipeline_reports")
        
        # Display report summary
        logger.info("\nPipeline Execution Summary:")
        logger.info(report.generate_report())

def main():
    parser = argparse.ArgumentParser(description="Run the complete corpus processing pipeline")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        required=True,
        help="Directory containing corpus texts"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to spaCy model (optional)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for NLP processing"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of worker processes"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation phase"
    )
    parser.add_argument(
        "--parallel-loading",
        action="store_true",
        help="Use parallel loading for texts"
    )
    parser.add_argument(
        "--loading-batch-size",
        type=int,
        default=5,
        help="Batch size for parallel loading"
    )
    parser.add_argument(
        "--use-gpu",
        action="store_true",
        help="Use GPU for NLP processing"
    )
    parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Force CPU usage even if GPU is available"
    )
    
    args = parser.parse_args()
    
    # Determine GPU usage
    use_gpu = None  # Auto-detect by default
    if args.use_gpu:
        use_gpu = True
    elif args.no_gpu:
        use_gpu = False
    
    asyncio.run(run_pipeline(
        corpus_dir=args.corpus_dir,
        model_path=args.model_path,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        validate=not args.no_validate,
        parallel_loading=args.parallel_loading,
        loading_batch_size=args.loading_batch_size,
        use_gpu=use_gpu
    ))

if __name__ == "__main__":
    main()
