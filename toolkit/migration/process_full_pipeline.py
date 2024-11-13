"""
Complete pipeline script for loading texts and processing them through NLP.

This script coordinates the entire process:
1. Verifying NLP pipeline
2. Migrating citations and relationships
3. Processing texts into sentences
4. Running NLP on sentences
5. Validating the results
"""

import asyncio
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import contextvars
import greenlet

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_scoped_session
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from toolkit.migration.citation_migrator import CitationMigrator
from toolkit.migration.content_validator import DataVerifier
from toolkit.migration.corpus_processor import CorpusProcessor
from toolkit.nlp.pipeline import NLPPipeline
from toolkit.migration.logging_config import setup_migration_logging

# Get logger but don't configure it yet - let setup_migration_logging handle that
logger = logging.getLogger(__name__)

class PipelineReport:
    """Tracks and reports issues during pipeline execution."""
    
    def __init__(self):
        self.citation_issues: List[Dict] = []
        self.sentence_issues: List[Dict] = []
        self.nlp_issues: List[Dict] = []
        self.validation_issues: List[Dict] = []
        self.missing_structures: List[Dict] = []  # Track works with missing structures
        self.start_time = datetime.now()
        
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

    def add_missing_structure(self, author_id: str, work_id: str, work_name: str):
        """Track works that didn't find a structure."""
        self.missing_structures.append({
            "author_id": author_id,
            "work_id": work_id,
            "work_name": work_name
        })
    
    def generate_report(self) -> str:
        """Generate a formatted report of all issues."""
        duration = datetime.now() - self.start_time
        
        report = [
            "\n=== Pipeline Execution Report ===",
            f"Execution time: {duration}",
            "\nIssues Summary:",
            f"- Citation migration issues: {len(self.citation_issues)}",
            f"- Sentence processing issues: {len(self.sentence_issues)}",
            f"- NLP processing issues: {len(self.nlp_issues)}",
            f"- Validation issues: {len(self.validation_issues)}",
            f"- Works missing structures: {len(self.missing_structures)}"
        ]
            
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

        if self.missing_structures:
            report.extend([
                "\nWorks Missing Structures:",
                *[f"- {work['author_id']}.{work['work_id']} {work['work_name']}"
                  for work in self.missing_structures]
            ])
            
        return "\n".join(report)
    
    def save_report(self, output_dir: Optional[Path] = None):
        """Save the report to a file."""
        # Use toolkit/migration/reports directory by default
        if output_dir is None:
            output_dir = Path(__file__).parent / "reports"
            
        # Create reports directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"pipeline_report_{timestamp}.txt"
        
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
    use_gpu: Optional[bool] = None,
    debug: bool = False,
    skip_to_corpus: bool = False
):
    """
    Run the complete pipeline from loading to processing.
    """
    # Initialize report tracker
    report = PipelineReport()
    
    try:
        # Verify NLP pipeline first
        await verify_nlp_pipeline(model_path, use_gpu)
        
        # Initialize database connection with proper async context
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            echo=settings.DEBUG,
            pool_pre_ping=True
        )

        # Create session factory with proper async scoping
        session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create scoped session tied to async context
        async_session = async_scoped_session(
            session_factory,
            scopefunc=asyncio.current_task
        )

        try:
            # Create new session for this task
            session = async_session()
            
            if not skip_to_corpus:
                # Phase 1: Migrate citations
                logger.info("Phase 1: Migrating citations...")
                try:
                    citation_migrator = CitationMigrator(session)
                    await citation_migrator.migrate_directory(corpus_dir)
                    logger.info("Citation migration completed")
                except Exception as e:
                    # Log the error but continue with pipeline
                    report.add_citation_issue("corpus_directory", str(e))
                    logger.error(f"Error during citation migration: {e}")
                    logger.info("Continuing with pipeline despite citation migration issues...")

            # Phase 2: Process sentences and NLP
            logger.info("Phase 2: Processing sentences and NLP...")
            try:
                processor = CorpusProcessor(
                    session,
                    model_path=model_path,
                    use_gpu=use_gpu,
                    report=report  # Pass report to processor
                )
                await processor.process_corpus()
            except Exception as e:
                report.add_sentence_issue("corpus_processing", str(e))
                logger.error(f"Error during sentence/NLP processing: {e}")
                raise
            
            # Phase 3: Validate results if requested
            if validate:
                logger.info("Phase 3: Validation...")
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

        finally:
            await session.close()
            
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise
    finally:
        await engine.dispose()
        await async_session.remove()
        
        # Save the execution report
        report.save_report()
        
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
        "--use-gpu",
        action="store_true",
        help="Use GPU for NLP processing"
    )
    parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Force CPU usage even if GPU is available"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--skip-to-corpus",
        action="store_true",
        help="Skip citation migration and start from corpus processing"
    )
    
    args = parser.parse_args()
    
    # Set up logging first, before any code runs
    setup_migration_logging(level="DEBUG" if args.debug else "INFO")
    
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
        use_gpu=use_gpu,
        debug=args.debug,
        skip_to_corpus=args.skip_to_corpus
    ))

if __name__ == "__main__":
    main()
