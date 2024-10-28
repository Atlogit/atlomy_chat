import torch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
import asyncio
from toolkit.migration.corpus_processor import CorpusProcessor
from toolkit.migration.content_validator import ContentValidator
from toolkit.loader.database import DatabaseLoader
from app.models.text_division import TextDivision
import logging
import os
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
import spacy
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/atlomy")

def normalize_greek_text(text: str) -> str:
    """Normalize Greek text by removing special characters and extra spaces."""
    # Remove line numbers and markers
    text = re.sub(r'^\d+\.\d+\.[t\d]+\.\s*', '', text)
    
    # Remove curly braces but keep content
    text = re.sub(r'\{([^}]*)\}', r'\1', text)
    
    # Remove special characters at end of lines (e.g., κδʹ, μηʹ)
    text = re.sub(r'\s+[κδʹμηʹοβʹϞστʹχ\d,]+$', '', text)
    
    # Normalize multiple spaces to single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def clean_special_content(content: str) -> str:
    """Clean special content while preserving important text.
    
    Args:
        content: Text content to clean
        
    Returns:
        Cleaned text content
    """
    cleaned_lines = []
    
    for line in content.split('\n'):
        # Skip completely empty lines
        if not line.strip():
            continue
            
        # Skip lines that are just numbers or special characters
        if re.match(r'^[\s\d\W]+$', line):
            continue
            
        # Normalize the line
        cleaned_line = normalize_greek_text(line)
        
        # Skip if line became empty after cleaning
        if not cleaned_line:
            continue
            
        cleaned_lines.append(cleaned_line)
    
    cleaned_text = ' '.join(cleaned_lines)  # Join with spaces instead of newlines
    
    # Log sample for debugging
    logger.debug(f"Original content sample: {content[:100]}...")
    logger.debug(f"Cleaned content sample: {cleaned_text[:100]}...")
    
    return cleaned_text

def get_tensor_from_doc(doc: spacy.tokens.Doc) -> Optional[torch.Tensor]:
    """Extract tensor from spaCy doc.
    
    Args:
        doc: spaCy Doc object
        
    Returns:
        Tensor or None if extraction fails
    """
    try:
        # Try getting tensor from doc's tensor attribute
        if hasattr(doc, 'tensor'):
            tensor = torch.from_numpy(doc.tensor)
            if len(tensor.shape) == 2:
                return tensor
            return tensor.reshape(1, -1)
        
        # Try getting from user_hooks
        if hasattr(doc._, 'tensor'):
            tensor_data = doc._.tensor
            if isinstance(tensor_data, np.ndarray):
                tensor = torch.from_numpy(tensor_data)
            else:
                tensor = tensor_data
            return tensor.reshape(1, -1) if len(tensor.shape) == 1 else tensor
        
        # Try getting from vector attribute
        if hasattr(doc, 'vector'):
            return torch.from_numpy(doc.vector).reshape(1, -1)
        
        logger.error("No tensor data found in spaCy doc")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting tensor from doc: {str(e)}")
        return None

def adjust_tensor_size(tensor: torch.Tensor, target_size: int = 514) -> Optional[torch.Tensor]:
    """Adjust tensor size.
    
    Args:
        tensor: Input tensor (expected shape: [1, N])
        target_size: Target size for second dimension
        
    Returns:
        Adjusted tensor or None if adjustment fails
    """
    try:
        if tensor is None:
            return None

        # Log original size
        original_size = tensor.shape[-1]
        logger.debug(f"Original tensor size: {tensor.shape}")

        if original_size < target_size:
            # Pad tensor to match target size
            padding = torch.zeros(1, target_size - original_size, device=tensor.device)
            adjusted = torch.cat([tensor, padding], dim=1)
            logger.debug(f"Padded tensor from {original_size} to {adjusted.shape[-1]}")
            return adjusted
        elif original_size > target_size:
            # Truncate tensor to match target size
            adjusted = tensor[:, :target_size]
            logger.debug(f"Truncated tensor from {original_size} to {adjusted.shape[-1]}")
            return adjusted
        return tensor

    except Exception as e:
        logger.error(f"Error adjusting tensor size: {str(e)}")
        return None

async def get_divisions(session: AsyncSession, work_id: int) -> List[TextDivision]:
    """Get all divisions for a work."""
    stmt = select(TextDivision).where(TextDivision.text_id == work_id)
    result = await session.execute(stmt)
    return result.scalars().all()

async def process_division(
    division_id: int,
    processor: CorpusProcessor,
    validator: ContentValidator,
    db_loader: DatabaseLoader,
    target_size: int = 514
) -> Optional[torch.Tensor]:
    """Process a single division with tensor adjustment."""
    try:
        # Get division content
        content = await db_loader.get_division_content(division_id)
        if not content:
            logger.error(f"No content found for division {division_id}")
            return None

        # Clean special content
        cleaned_content = clean_special_content(content)
        if not cleaned_content.strip():
            logger.warning(f"Division {division_id} content empty after cleaning")
            return None

        # Validate content
        try:
            validator.validate(cleaned_content)
        except Exception as e:
            logger.error(f"Content validation failed for division {division_id}: {str(e)}")
            return None

        # Process text with NLP pipeline
        try:
            # Get spaCy doc directly from pipeline
            doc = processor.nlp_pipeline.nlp(cleaned_content)
            
            # Extract tensor from doc
            tensor = get_tensor_from_doc(doc)
            if tensor is not None:
                # Log original shape
                logger.debug(f"Division {division_id} tensor shape: {tensor.shape}")
                
                # Adjust tensor size
                adjusted_tensor = adjust_tensor_size(tensor, target_size)
                if adjusted_tensor is not None:
                    logger.info(f"Division {division_id} processed successfully")
                    logger.debug(f"Adjusted tensor shape: {adjusted_tensor.shape}")
                    return adjusted_tensor
            return None

        except torch.cuda.OutOfMemoryError:
            logger.error(f"CUDA out of memory while processing division {division_id}")
            torch.cuda.empty_cache()
            return None
        except RuntimeError as e:
            if "size of tensor" in str(e):
                logger.error(f"Runtime error processing division {division_id}: {str(e)}")
            else:
                logger.error(f"Runtime error processing division {division_id}: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"Error processing division {division_id}: {str(e)}")
        return None

async def main():
    """Main async function to handle database operations."""
    engine = None
    try:
        # Initialize database connection
        engine = create_async_engine(DATABASE_URL)
        async_session = async_sessionmaker(
            engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as session:
            # Initialize components with session
            processor = CorpusProcessor(session=session)
            validator = ContentValidator()
            db_loader = DatabaseLoader(session=session)

            # Process Work 49
            work_id = 49
            logger.info(f"Processing Work {work_id}")

            # Get work details
            work = await db_loader.get_work(work_id)
            if not work:
                logger.error(f"Work {work_id} not found")
                return

            # Get divisions
            divisions = await get_divisions(session, work_id)
            if not divisions:
                logger.error(f"No divisions found for work {work_id}")
                return

            # Process each division
            processed_tensors = []
            failed_divisions = []
            for division in divisions:
                tensor = await process_division(
                    division.id,
                    processor,
                    validator,
                    db_loader
                )
                if tensor is not None:
                    processed_tensors.append(tensor)
                else:
                    failed_divisions.append(division.id)
                await session.commit()  # Commit after each division

            logger.info(f"Work 49 processing completed. Processed {len(processed_tensors)} divisions successfully")
            if failed_divisions:
                logger.warning(f"Failed to process divisions: {failed_divisions}")

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        if 'session' in locals():
            await session.rollback()
    finally:
        if engine:
            await engine.dispose()

def run():
    """Run the async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Error running main: {str(e)}")

if __name__ == "__main__":
    run()
