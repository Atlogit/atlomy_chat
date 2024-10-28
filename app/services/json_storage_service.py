"""
Service for managing JSON storage of lexical values.
Handles file creation, updates, and versioning.
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
    """Service for managing JSON storage of lexical values."""
    
    def __init__(self, base_dir: str = "lexical_values"):
        """Initialize the JSON storage service.
        
        Args:
            base_dir: Base directory for JSON storage
        """
        self.base_dir = Path(base_dir)
        self._ensure_directory_structure()

    def _ensure_directory_structure(self):
        """Ensure the required directory structure exists."""
        # Create main directories
        (self.base_dir / "current").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "versions").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "backup").mkdir(parents=True, exist_ok=True)

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
            # Create backup of existing file
            self._create_backup(lemma)
            
            # Add metadata
            data["metadata"] = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": data.get("metadata", {}).get("version", "1.0")
            }
            
            # Save current version
            current_file = self._get_file_path(lemma)
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved current version: {current_file}")
            
            # Create versioned copy if requested
            if create_version:
                version = datetime.now().strftime("%Y%m%d_%H%M%S")
                version_file = self._get_file_path(lemma, version)
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
            file_path = self._get_file_path(lemma, version)
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
            versions_dir = self.base_dir / "versions"
            versions = []
            for file in versions_dir.glob(f"{lemma}_*.json"):
                version = file.stem.replace(f"{lemma}_", "")
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
            current_file = self._get_file_path(lemma)
            if not current_file.exists():
                return False
                
            # Create final backup before deletion
            self._create_backup(lemma)
            
            # Delete current file
            current_file.unlink()
            logger.info(f"Deleted: {current_file}")
            
            # Delete versions if requested
            if delete_versions:
                for version_file in (self.base_dir / "versions").glob(f"{lemma}_*.json"):
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
