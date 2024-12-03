"""
Service for managing JSON storage of lexical values.
Handles file creation, updates, and versioning with EC2 deployment support.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONStorageService:
    """Service for managing JSON storage of lexical values with flexible path support."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the JSON storage service.
        
        Args:
            base_dir: Base directory for JSON storage. 
                      If None, uses environment variable or default project structure.
        """
        # Prioritize input base_dir, then environment variable, then default project paths
        if base_dir is None:
            # Check environment variables first
            base_dir = os.environ.get('JSON_STORAGE_BASE_DIR')
            
            # If no env var, use project-relative paths
            if not base_dir:
                # Determine the project root
                project_root = Path(__file__).resolve().parents[2]
                base_dir = project_root / 'lexical_values'
        
        # Convert to absolute path, resolving any relative paths
        base_dir = str(Path(base_dir).resolve())
        
        self.base_dir = Path(base_dir)
        self._ensure_directory_structure()
        
        # Log the resolved absolute path for debugging
        logger.info(f"JSON Storage Base Directory: {self.base_dir}")

    def _ensure_directory_structure(self):
        """Ensure the required directory structure exists with comprehensive logging."""
        try:
            # Create main directories with more permissive permissions for EC2
            dirs_to_create = [
                self.base_dir / "current",
                self.base_dir / "versions", 
                self.base_dir / "backup"
            ]
            
            for directory in dirs_to_create:
                os.makedirs(directory, mode=0o777, exist_ok=True)
                logger.info(f"Ensured directory exists: {directory}")
                
                # Additional permission setting for Docker/EC2 compatibility
                try:
                    os.chmod(directory, 0o777)
                except Exception as perm_error:
                    logger.warning(f"Could not set full permissions for {directory}: {perm_error}")
        
        except Exception as e:
            logger.error(f"Failed to create directory structure: {e}")
            raise

    def _get_file_path(self, lemma: str, version: Optional[str] = None) -> Path:
        """Get the file path for a lexical value.
        
        Args:
            lemma: The lemma to get the path for
            version: Optional version string
            
        Returns:
            Path object for the file
        """
        if version:
            return self.base_dir / "versions" / f"{lemma}_{version}.json"
        return self.base_dir / "current" / f"{lemma}.json"

    def _create_backup(self, lemma: str):
        """Create a backup of the current file.
        
        Args:
            lemma: The lemma to backup
        """
        current_file = self._get_file_path(lemma)
        if current_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.base_dir / "backup" / f"{lemma}_{timestamp}.json"
            
            try:
                shutil.copy2(current_file, backup_file)
                logger.info(f"Created backup: {backup_file}")
            except Exception as e:
                logger.error(f"Failed to create backup for {lemma}: {e}")

    def _compute_content_hash(self, data: Dict[str, Any]) -> str:
        """Compute a hash of the content to detect changes."""
        # Remove metadata and timestamps for consistent hashing
        hashable_data = {k: v for k, v in data.items() if k != 'metadata'}
        return hashlib.md5(json.dumps(hashable_data, sort_keys=True).encode()).hexdigest()

    def _extract_llm_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize LLM configuration.
        
        Args:
            config: Raw LLM configuration dictionary
        
        Returns:
            Normalized LLM configuration
        """
        return {
            "model_id": config.get("modelId", config.get("model_id", "")),
            "temperature": config.get("temperature"),
            "top_p": config.get("topP", config.get("top_p")),
            "top_k": config.get("topK", config.get("top_k")),
            "max_length": config.get("maxLength", config.get("max_length")),
            "stop_sequences": config.get("stopSequences", config.get("stop_sequences", []))
        }

    def save(
        self, 
        lemma: str, 
        data: Dict[str, Any], 
        create_version: bool = False,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save lexical value data with intelligent versioning.
        
        Args:
            lemma: The lexical entry's lemma
            data: The data to save
            create_version: Flag to create a versioned copy
            llm_config: Optional LLM configuration used for generation
        
        Returns:
            The version identifier for this save operation
        """
        try:
            # Sanitize lemma to prevent directory traversal
            safe_lemma = "".join(c for c in lemma if c.isalnum() or c in ['_', '-'])
            
            # Compute content hash to detect meaningful changes
            current_hash = self._compute_content_hash(data)
            
            # Generate version using precise timestamp
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Comprehensive timestamp extraction
            original_created_at = (
                data.get('created_at') or 
                data.get('metadata', {}).get('created_at') or 
                datetime.now().isoformat()
            )
            
            current_time = datetime.now().isoformat()
            
            # Prepare comprehensive metadata
            metadata = {
                "created_at": original_created_at,
                "updated_at": current_time,
                "version": version,
                "content_hash": current_hash,
                "llm_config": self._extract_llm_config(llm_config) if llm_config else {}
            }
            
            # Create a new data dictionary with updated metadata
            updated_data = data.copy()
            
            # Ensure both top-level and metadata have consistent version and timestamps
            updated_data.update({
                "metadata": metadata,
                "version": version,
                "created_at": original_created_at,
                "updated_at": current_time
            })
            
            # Save current version
            current_file = self._get_file_path(safe_lemma)
            current_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=2, default=str)
            
            os.chmod(current_file, 0o666)
            logger.info(f"Saved current version for {safe_lemma}: {version}")
            
            # Optional versioned copy
            if create_version:
                version_file = self._get_file_path(safe_lemma, version)
                version_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(current_file, version_file)
                os.chmod(version_file, 0o666)
                logger.info(f"Created versioned copy: {version_file}")
            
            return version
        
        except Exception as e:
            logger.error(f"Version save failed for {lemma}: {e}")
            raise

    def load(self, lemma: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load lexical value data from JSON.
        
        Args:
            lemma: The lemma to load
            version: Optional specific version to load
            
        Returns:
            The loaded data or None if not found
        """
        try:
            # Sanitize lemma to prevent directory traversal
            safe_lemma = "".join(c for c in lemma if c.isalnum() or c in ['_', '-'])
            
            file_path = self._get_file_path(safe_lemma, version)
            
            # Comprehensive logging for load attempts
            logger.info(f"Attempting to load file: {file_path}")
            logger.info(f"File exists: {file_path.exists()}")
            
            if not file_path.exists():
                logger.warning(f"No file found for lemma: {safe_lemma}, version: {version}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Successfully loaded: {file_path}")
            return data
            
        except FileNotFoundError:
            logger.warning(f"File not found for {lemma} (version: {version})")
            return None
        except json.JSONDecodeError as je:
            logger.error(f"JSON decoding error for {lemma}: {je}")
            return None
        except Exception as e:
            logger.error(f"Error loading JSON for {lemma}: {str(e)}")
            raise

    def list_versions(self, lemma: str) -> List[Dict[str, Any]]:
        """
        List all available versions for a lemma with comprehensive metadata.
        
        Args:
            lemma: The lemma to list versions for
        
        Returns:
            Sorted list of version metadata
        """
        try:
            safe_lemma = "".join(c for c in lemma if c.isalnum() or c in ['_', '-'])
            versions_dir = self.base_dir / "versions"
            
            version_details = []
            for file in sorted(versions_dir.glob(f"{safe_lemma}_*.json"), reverse=True):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Comprehensive metadata extraction
                    metadata = data.get('metadata', {})
                    
                    # Fallback version extraction
                    version = (
                        metadata.get('version') or 
                        data.get('version') or 
                        file.stem.split('_', 1)[1]
                    )
                    
                    # Fallback timestamp extraction
                    created_at = (
                        metadata.get('created_at') or 
                        data.get('created_at') or 
                        datetime.now().isoformat()
                    )
                    
                    updated_at = (
                        metadata.get('updated_at') or 
                        data.get('updated_at') or 
                        created_at
                    )
                    
                    # Extract LLM config with comprehensive fallback
                    llm_config = (
                        metadata.get('llm_config') or 
                        data.get('llm_config') or 
                        {}
                    )
                    
                    version_info = {
                        "version": version,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "model": (
                            llm_config.get('model_id') or 
                            llm_config.get('modelId') or 
                            ''
                        ),
                        "parameters": {
                            k: llm_config.get(k)
                            for k in ['temperature', 'top_p', 'top_k', 'max_length']
                            if llm_config.get(k) is not None
                        }
                    }
                    
                    version_details.append(version_info)
                
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted version file: {file}")
                except Exception as e:
                    logger.error(f"Error processing version file {file}: {e}")
            
            return version_details
        
        except Exception as e:
            logger.error(f"Error listing versions for {lemma}: {e}")
            return []

    def delete(self, lemma: str, delete_versions: bool = False) -> bool:
        """Delete a lexical value's JSON files.
        
        Args:
            lemma: The lemma to delete
            delete_versions: Whether to also delete versioned copies
            
        Returns:
            True if successful, False if file not found
        """
        try:
            # Sanitize lemma to prevent directory traversal
            safe_lemma = "".join(c for c in lemma if c.isalnum() or c in ['_', '-'])
            
            current_file = self._get_file_path(safe_lemma)
            if not current_file.exists():
                return False
                
            # Create final backup before deletion
            self._create_backup(safe_lemma)
            
            # Delete current file
            current_file.unlink()
            logger.info(f"Deleted: {current_file}")
            
            # Delete versions if requested
            if delete_versions:
                for version_file in (self.base_dir / "versions").glob(f"{safe_lemma}_*.json"):
                    version_file.unlink()
                    logger.info(f"Deleted version: {version_file}")
                    
            return True
            
        except Exception as e:
            logger.error(f"Error deleting JSON for {lemma}: {str(e)}")
            raise

    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the JSON storage.
        
        Returns:
            Dictionary with storage information
        """
        try:
            current_count = len(list(self.base_dir.glob("current/*.json")))
            version_count = len(list(self.base_dir.glob("versions/*.json")))
            backup_count = len(list(self.base_dir.glob("backup/*.json")))
            
            return {
                "current_files": current_count,
                "versioned_files": version_count,
                "backup_files": backup_count,
                "base_directory": str(self.base_dir),
                "total_size": sum(f.stat().st_size for f in self.base_dir.rglob("*.json"))
            }
            
        except Exception as e:
            logger.error(f"Error getting storage info: {str(e)}")
            raise
