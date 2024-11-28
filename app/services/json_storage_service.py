"""
Service for managing JSON storage of lexical values.
Handles file creation, updates, and versioning with EC2 deployment support.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONStorageService:
    """Service for managing JSON storage of lexical values with EC2 support."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the JSON storage service.
        
        Args:
            base_dir: Base directory for JSON storage. 
                      If None, uses environment variable or default.
        """
        # Prioritize input base_dir, then environment variable, then default
        if base_dir is None:
            base_dir = os.environ.get(
                'JSON_STORAGE_BASE_DIR', 
                "/mnt/data/lexical_values"  # EC2-friendly default path
            )
        
        self.base_dir = Path(base_dir)
        self._ensure_directory_structure()

    def _ensure_directory_structure(self):
        """Ensure the required directory structure exists."""
        # Create main directories with more permissive permissions for EC2
        os.makedirs(self.base_dir / "current", mode=0o755, exist_ok=True)
        os.makedirs(self.base_dir / "versions", mode=0o755, exist_ok=True)
        os.makedirs(self.base_dir / "backup", mode=0o755, exist_ok=True)

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
            shutil.copy2(current_file, backup_file)
            logger.info(f"Created backup: {backup_file}")

    def save(self, lemma: str, data: Dict[str, Any], create_version: bool = True) -> None:
        """Save lexical value data to JSON.
        
        Args:
            lemma: The lemma to save
            data: The data to save
            create_version: Whether to create a versioned copy
        """
        try:
            # Sanitize lemma to prevent directory traversal
            safe_lemma = "".join(c for c in lemma if c.isalnum() or c in ['_', '-'])
            
            # Create backup of existing file
            self._create_backup(safe_lemma)
            
            # Add metadata
            data["metadata"] = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": data.get("metadata", {}).get("version", "1.0"),
                "storage_location": str(self.base_dir)
            }
            
            # Save current version with proper JSON serialization
            current_file = self._get_file_path(safe_lemma)
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"Saved current version: {current_file}")
            
            # Create versioned copy if requested
            if create_version:
                version = datetime.now().strftime("%Y%m%d_%H%M%S")
                version_file = self._get_file_path(safe_lemma, version)
                shutil.copy2(current_file, version_file)
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
            if not file_path.exists():
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded: {file_path}")
            return data
            
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
