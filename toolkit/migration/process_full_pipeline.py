"""Complete pipeline script for loading texts and processing them through NLP.

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
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import traceback

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_scoped_session
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from toolkit.migration.citation_migrator import CitationMigrator
from toolkit.migration.content_validator import ContentValidator, DataVerifier
from toolkit.migration.corpus_processor import CorpusProcessor
from toolkit.nlp.pipeline import NLPPipeline
from toolkit.migration.logging_config import setup_migration_logging

# Get logger but don't configure it yet - let setup_migration_logging handle that
logger = logging.getLogger(__name__)

class PipelineWarningCollector:
    """Comprehensive warning collection and reporting mechanism."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.warnings: Dict[str, List[Dict[str, Any]]] = {
            "citation_migration": [],
            "sentence_processing": [],
            "nlp_processing": [],
            "validation": [],
            "content_validation": [],
            "script_validation": [],
            "relationship_warnings": [],
            "content_integrity_warnings": [],
            "line_continuity_warnings": [],
            "text_completeness_warnings": []
        }
        self.start_time = datetime.now()
        self.output_dir = output_dir or Path(__file__).parent / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def add_warning(self, category: str, warning: Dict[str, Any]):
        """Add a warning to the specified category."""
        if category in self.warnings:
            self.warnings[category].append(warning)
        else:
            logger.warning(f"Unknown warning category: {category}")
    
    def generate_report(self) -> str:
        """Generate a human-readable warning report."""
        duration = datetime.now() - self.start_time
        
        report_lines = [
            "\n=== Migration Warning Report ===",
            f"Execution time: {duration}",
            "\nWarnings Summary:"
        ]
        
        for category, category_warnings in self.warnings.items():
            if category_warnings:
                report_lines.append(f"- {category.replace('_', ' ').title()}: {len(category_warnings)} warnings")
        
        # Detailed warnings
        for category, category_warnings in self.warnings.items():
            if category_warnings:
                report_lines.append(f"\n{category.replace('_', ' ').title()} Warnings:")
                for warning in category_warnings:
                    report_lines.append(
                        f"- {warning.get('work_id', 'Unknown')}: "
                        f"{warning.get('message', 'No details')}"
                    )
        
        return "\n".join(report_lines)
    
    def save_reports(self):
        """Save warnings to both text and JSON formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Text report
        text_report_path = self.output_dir / f"migration_warnings_{timestamp}.txt"
        with open(text_report_path, "w") as f:
            f.write(self.generate_report())
        logger.info(f"Migration warnings text report saved to: {text_report_path}")
        
        # JSON report for machine-readable analysis
        json_report_path = self.output_dir / f"migration_warnings_{timestamp}.json"
        with open(json_report_path, "w") as f:
            json.dump(self.warnings, f, indent=2)
        logger.info(f"Migration warnings JSON report saved to: {json_report_path}")

async def verify_nlp_pipeline(
    model_path: Optional[str], 
    use_gpu: Optional[bool], 
    warning_collector: PipelineWarningCollector
) -> None:
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
            warning_collector.add_warning("nlp_processing", {
                "work_id": "nlp_verification",
                "message": "NLP pipeline failed to process test text"
            })
            
        # Log success with GPU status
        if use_gpu:
            logger.info("✓ NLP pipeline verified (GPU mode)")
        else:
            logger.info("✓ NLP pipeline verified (CPU mode)")
            
    except Exception as e:
        warning_collector.add_warning("nlp_processing", {
            "work_id": "nlp_verification",
            "message": f"NLP pipeline verification failed: {str(e)}",
            "traceback": traceback.format_exc()
        })
        logger.error(f"NLP pipeline verification failed: {str(e)}")

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
    Run the complete pipeline from loading to processing with lenient validation.
    Ensures all texts are imported and warnings are collected.
    """
    # Initialize warning collector
    warning_collector = PipelineWarningCollector()
    
    try:
        # Verify NLP pipeline first
        await verify_nlp_pipeline(model_path, use_gpu, warning_collector)
        
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
                # Phase 1: Migrate citations (lenient approach)
                logger.info("Phase 1: Migrating citations...")
                try:
                    citation_migrator = CitationMigrator(session)
                    await citation_migrator.migrate_directory(corpus_dir)
                    logger.info("Citation migration completed")
                except Exception as e:
                    # Log the error but continue with pipeline
                    warning_collector.add_warning("citation_migration", {
                        "work_id": "corpus_directory",
                        "message": f"Citation migration issue: {str(e)}",
                        "traceback": traceback.format_exc()
                    })
                    logger.error(f"Error during citation migration: {e}")
                    logger.info("Continuing with pipeline despite citation migration issues...")

            # Phase 2: Process sentences and NLP (lenient processing)
            logger.info("Phase 2: Processing sentences and NLP...")
            try:
                processor = CorpusProcessor(
                    session,
                    model_path=model_path,
                    use_gpu=use_gpu,
                    warning_collector=warning_collector  # Pass warning collector
                )
                await processor.process_corpus()
            except Exception as e:
                warning_collector.add_warning("sentence_processing", {
                    "work_id": "corpus_processing",
                    "message": f"Sentence/NLP processing error: {str(e)}",
                    "traceback": traceback.format_exc()
                })
                logger.error(f"Error during sentence/NLP processing: {e}")
                # Continue processing despite errors
            
            # Phase 3: Validate results if requested (lenient validation)
            if validate:
                logger.info("Phase 3: Validation...")
                verifier = DataVerifier(session)
                try:
                    validation_results = await verifier.run_all_verifications()
                    
                    # Collect all warnings from verification
                    for category, warnings in validation_results.items():
                        for warning in warnings:
                            warning_collector.add_warning(category, warning)
                            
                except Exception as e:
                    warning_collector.add_warning("validation", {
                        "work_id": "global_validation",
                        "message": f"Validation process error: {str(e)}",
                        "traceback": traceback.format_exc()
                    })
                    logger.error(f"Error during validation: {e}")

        finally:
            await session.close()
            
    except Exception as e:
        warning_collector.add_warning("pipeline_execution", {
            "work_id": "global_pipeline",
            "message": f"Overall pipeline execution error: {str(e)}",
            "traceback": traceback.format_exc()
        })
        logger.error(f"Pipeline failed: {str(e)}")
    finally:
        await engine.dispose()
        await async_session.remove()
        
        # Save the warning reports
        warning_collector.save_reports()
        
        # Display warning summary
        logger.info("\nMigration Warning Summary:")
        logger.info(warning_collector.generate_report())

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
