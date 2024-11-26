"""
NLP Pipeline for processing ancient texts using spaCy.

This module provides a configurable pipeline for processing texts with spaCy,
storing results in a format compatible with our PostgreSQL schema.
"""

import os
import sys
import ctypes
import warnings
import torch
from typing import List, Dict, Any, Optional
from pathlib import Path
import spacy
from tqdm import tqdm

# Import migration logging configuration
from toolkit.migration.logging_config import get_migration_logger

# Use migration logger
logger = get_migration_logger('nlp.pipeline')

def _configure_cuda_libraries():
    """
    Comprehensive CUDA library configuration and detection.
    
    Attempts to resolve CUDA library loading issues by:
    1. Adding potential library paths
    2. Explicitly loading key CUDA runtime libraries
    3. Configuring environment for GPU computing
    """
    # Suppress specific warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    
    # Potential CUDA library paths
    cuda_lib_paths = [
        '/root/anaconda3/envs/amta/lib/python3.11/site-packages/nvidia/cuda_nvrtc/lib',
        '/usr/local/cuda/lib64',
        '/opt/cuda/lib64',
        f'{os.environ.get("CONDA_PREFIX", "")}/lib',
        f'{os.environ.get("CONDA_PREFIX", "")}/lib64'
    ]
    
    # Update LD_LIBRARY_PATH
    current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
    new_ld_path = ':'.join(filter(os.path.exists, cuda_lib_paths))
    
    if new_ld_path:
        os.environ['LD_LIBRARY_PATH'] = f"{new_ld_path}:{current_ld_path}"
        logger.info(f"Updated LD_LIBRARY_PATH: {os.environ['LD_LIBRARY_PATH']}")
    
    # Attempt to load NVRTC library
    nvrtc_lib_path = '/root/anaconda3/envs/amta/lib/python3.11/site-packages/nvidia/cuda_nvrtc/lib/libnvrtc.so.12'
    
    try:
        # Explicitly load library
        ctypes.CDLL(nvrtc_lib_path, mode=ctypes.RTLD_GLOBAL)
        logger.info(f"Successfully loaded {nvrtc_lib_path}")
    except Exception as e:
        logger.warning(f"Could not load {nvrtc_lib_path}: {e}")
        return False
    
    return True

class NLPPipeline:
    """Handles text processing using spaCy with configuration for ancient texts."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        batch_size: int = 1000,
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
        # Configure CUDA libraries before any GPU operations
        cuda_config_success = _configure_cuda_libraries()
        
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
        
        # Comprehensive GPU detection
        self.gpu_available = self._check_gpu_availability()
        
        # Determine GPU usage
        if use_gpu is None:
            use_gpu = self.gpu_available
        
        # Configure spaCy and PyTorch for processing
        if use_gpu and self.gpu_available and cuda_config_success:
            try:
                spacy.require_gpu()
                torch.set_default_tensor_type('torch.cuda.FloatTensor')
                logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
                logger.info(f"CUDA Version: {torch.version.cuda}")
            except Exception as e:
                logger.warning(f"GPU initialization failed. Falling back to CPU: {e}")
                use_gpu = False
                spacy.require_cpu()
        else:
            spacy.require_cpu()
            logger.info("Using CPU for NLP processing")
        
        logger.info(f"Loading spaCy model from: {model_path}")
        try:
            self.nlp = spacy.load(model_path)
            # Configure category detection threshold
            self.nlp.get_pipe("spancat").cfg["threshold"] = category_threshold
            logger.info("Successfully loaded spaCy model and configured pipeline")
            
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            raise

    def _check_gpu_availability(self) -> bool:
        """
        Comprehensive check for GPU availability.
        
        Returns:
            Boolean indicating whether a usable GPU is available
        """
        try:
            # Check PyTorch CUDA availability
            if not torch.cuda.is_available():
                logger.warning("PyTorch reports no CUDA devices available.")
                return False
            
            # Additional checks for CUDA libraries and device initialization
            try:
                torch.zeros(1).cuda()
            except RuntimeError as cuda_error:
                logger.warning(f"CUDA device initialization failed: {cuda_error}")
                return False
            
            return True
        
        except Exception as e:
            logger.warning(f"Unexpected error checking GPU availability: {e}")
            return False

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
