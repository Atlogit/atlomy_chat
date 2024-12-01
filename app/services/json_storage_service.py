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
                
                # Prefer lexical_values in project root, fallback to amta/lexical_values
                potential_paths = [
                    project_root / 'lexical_values',
                    project_root / 'amta' / 'lexical_values',
                    Path.home() / 'amta' / 'lexical_values'
                ]
                
                # Use the first existing path, or create the first preferred path
                base_dir = next((str(p) for p in potential_paths if p.exists()), str(potential_paths[0]))
        
        self.base_dir = Path(base_dir)
        self._ensure_directory_structure()

    # Rest of the class remains the same as in the previous implementation
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

    # Remaining methods from the previous implementation stay the same
    # (load, save, list_versions, delete, get_storage_info methods)
    
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

    def save(self, lemma: str, data: Dict[str, Any], create_version: bool = False) -> None:
        """Save lexical value data to JSON with improved version control.
        
        Args:
            lemma: The lemma to save
            data: The data to save
            create_version: Whether to create a versioned copy (default: False)
        """
        try:
            # Sanitize lemma to prevent directory traversal
            safe_lemma = "".join(c for c in lemma if c.isalnum() or c in ['_', '-'])
            
            # Compute content hash
            current_hash = self._compute_content_hash(data)
            
            # Check if current file exists and has the same content
            current_file = self._get_file_path(safe_lemma)
            
            # Ensure parent directory exists
            current_file.parent.mkdir(parents=True, exist_ok=True)
            
            if current_file.exists():
                with open(current_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_hash = self._compute_content_hash(existing_data)
                    
                    # If content is identical, skip saving
                    if current_hash == existing_hash:
                        logger.info(f"No changes detected for {safe_lemma}. Skipping save.")
                        return

            # Create backup of existing file
            self._create_backup(safe_lemma)
            
            # Add metadata
            data["metadata"] = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": data.get("metadata", {}).get("version", "1.0"),
                "content_hash": current_hash,
                "storage_location": str(self.base_dir)
            }
            
            # Save current version with proper JSON serialization
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # Set file permissions for broader access
            os.chmod(current_file, 0o666)
            
            logger.info(f"Saved current version: {current_file}")
            
            # Create versioned copy if requested and content has changed
            if create_version:
                version = datetime.now().strftime("%Y%m%d_%H%M%S")
                version_file = self._get_file_path(safe_lemma, version)
                
                # Ensure version directory exists
                version_file.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(current_file, version_file)
                os.chmod(version_file, 0o666)
                logger.info(f"Created version: {version_file}")
                
        except Exception as e:
            logger.error(f"Error saving JSON for {lemma}: {str(e)}")
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

    def list_versions(self, lemma: str) -> list:
        """List all available versions for a lemma.
        
        Args:
            lemma: The lemma to list versions for
            
        Returns:
            List of version strings
        """
        try:
            # Sanitize lemma to prevent directory traversal
            safe_lemma = "".join(c for c in lemma if c.isalnum() or c in ['_', '-'])
            
            versions_dir = self.base_dir / "versions"
            versions = []
            for file in versions_dir.glob(f"{safe_lemma}_*.json"):
                version = file.stem.replace(f"{safe_lemma}_", "")
                versions.append(version)
            return sorted(versions)
            
        except Exception as e:
            logger.error(f"Error listing versions for {lemma}: {str(e)}")
            raise

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
