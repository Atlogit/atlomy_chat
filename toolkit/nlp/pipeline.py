"""
NLP Pipeline for processing ancient texts using spaCy.

This module provides a configurable pipeline for processing texts with spaCy,
storing results in a format compatible with our PostgreSQL schema.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import spacy
import torch
from tqdm import tqdm

logger = logging.getLogger(__name__)

class NLPPipeline:
    """Handles text processing using spaCy with configuration for ancient texts."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        batch_size: int = 500,
        category_threshold: float = 0.2,
        use_gpu: Optional[bool] = None
    ):
        """
        Initialize the NLP pipeline.

        Args:
            model_path: Path to spaCy model. If None, uses default ancient Greek model
            batch_size: Number of texts to process in each batch
            category_threshold: Threshold for category detection
            use_gpu: Whether to use GPU. If None, automatically detects GPU availability
        """
        self.batch_size = batch_size
        
        # Use provided model path or default to project model
        if not model_path:
            project_root = Path(__file__).parent.parent.parent
            model_path = os.path.join(
                project_root,
                "assets",
                "models",
                "atlomy_full_pipeline_annotation_131024",
                "model-best"
            )
        
        # Configure GPU usage
        if use_gpu is None:
            use_gpu = torch.cuda.is_available()
        
        if use_gpu:
            if not torch.cuda.is_available():
                logger.warning("PyTorch CUDA not available. Falling back to CPU.")
                spacy.require_cpu()
            else:
                try:
                    spacy.require_gpu()
                    logger.info("Using GPU for NLP processing")
                    # Set PyTorch to use GPU
                    torch.set_default_tensor_type('torch.cuda.FloatTensor')
                except Exception as e:
                    logger.warning(f"Failed to initialize GPU: {e}. Falling back to CPU.")
                    spacy.require_cpu()
                    use_gpu = False
        else:
            spacy.require_cpu()
            logger.info("Using CPU for NLP processing")
        
        logger.info(f"Loading spaCy model from: {model_path}")
        try:
            self.nlp = spacy.load(model_path)
            # Configure category detection threshold
            self.nlp.get_pipe("spancat").cfg["threshold"] = category_threshold
            logger.info("Successfully loaded spaCy model and configured pipeline")
            
            # Log device information
            if use_gpu and torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                logger.info(f"Using GPU: {device_name}")
                logger.info(f"CUDA Version: {torch.version.cuda}")
                
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            raise

    def _create_token_dict(self, token: spacy.tokens.Token, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """
        Create a dictionary representation of a token suitable for JSONB storage.

        Args:
            token: spaCy token
            doc: Parent spaCy document

        Returns:
            Dictionary containing token information
        """
        return {
            "text": token.text,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "tag": token.tag_,
            "dep": token.dep_,
            "morph": str(token.morph.to_dict()),
            # Extract categories from spans
            "category": ", ".join(
                span.label_ 
                for span in doc.spans.get("sc", []) 
                if span.start <= token.i < span.end
            )
        }

    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process a single text through the NLP pipeline.

        Args:
            text: Text content to process

        Returns:
            Dictionary containing processed text and token information
        """
        doc = self.nlp(text)
        return {
            "text": text,
            "tokens": [self._create_token_dict(token, doc) for token in doc]
        }

    def process_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Process a batch of texts through the NLP pipeline.

        Args:
            texts: List of text content to process

        Returns:
            List of dictionaries containing processed texts and token information
        """
        logger.info(f"Processing batch of {len(texts)} texts")
        results = []
        
        try:
            # Process texts in batches
            for doc in tqdm(
                self.nlp.pipe(texts, batch_size=self.batch_size),
                total=len(texts),
                desc="Processing texts",
                unit="text"
            ):
                processed = {
                    "text": doc.text,
                    "tokens": [self._create_token_dict(token, doc) for token in doc]
                }
                results.append(processed)
            
            logger.info(f"Successfully processed {len(texts)} texts")
            return results
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            raise

    def extract_categories(self, processed_text: Dict[str, Any]) -> List[str]:
        """
        Extract unique categories from processed text.

        Args:
            processed_text: Dictionary containing processed text and token information

        Returns:
            List of unique categories found in the text
        """
        categories = set()
        for token in processed_text["tokens"]:
            if token["category"]:
                categories.update(token["category"].split(", "))
        return sorted(list(categories))
