import json
import os
from typing import List, Dict, Optional
from .lexical_value import LexicalValue
from .logging_config import get_logger

def get_lvg_logger():
    return get_logger()

class LexicalValueStorageError(Exception):
    """Custom exception for LexicalValueStorage errors."""
    pass

class LexicalValueStorage:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        try:
            os.makedirs(storage_dir, exist_ok=True)
        except OSError as e:
            get_lvg_logger().error(f"Failed to create storage directory: {str(e)}")
            raise LexicalValueStorageError("Failed to create storage directory") from e

    def _get_file_path(self, lemma: str) -> str:
        return os.path.join(self.storage_dir, f"{lemma}.json")

    def store(self, lexical_value: LexicalValue) -> None:
        file_path = self._get_file_path(lexical_value.lemma)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(lexical_value.__dict__, f, ensure_ascii=False, indent=2)
            get_lvg_logger().info(f"Stored lexical value for lemma: {lexical_value.lemma}")
        except IOError as e:
            get_lvg_logger().error(f"Failed to store lexical value for lemma {lexical_value.lemma}: {str(e)}")
            raise LexicalValueStorageError(f"Failed to store lexical value for lemma {lexical_value.lemma}") from e

    def retrieve(self, lemma: str) -> Optional[LexicalValue]:
        file_path = self._get_file_path(lemma)
        if not os.path.exists(file_path):
            get_lvg_logger().warning(f"Lexical value for lemma {lemma} not found")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            get_lvg_logger().info(f"Retrieved lexical value for lemma: {lemma}")
            return LexicalValue(**data)
        except (IOError, json.JSONDecodeError) as e:
            get_lvg_logger().error(f"Failed to retrieve lexical value for lemma {lemma}: {str(e)}")
            raise LexicalValueStorageError(f"Failed to retrieve lexical value for lemma {lemma}") from e

    def list_all(self) -> List[str]:
        try:
            lemmas = [os.path.splitext(f)[0] for f in os.listdir(self.storage_dir) if f.endswith('.json')]
            get_lvg_logger().info(f"Listed {len(lemmas)} lexical values")
            return lemmas
        except OSError as e:
            get_lvg_logger().error(f"Failed to list lexical values: {str(e)}")
            raise LexicalValueStorageError("Failed to list lexical values") from e

    def update(self, lexical_value: LexicalValue) -> None:
        try:
            self.store(lexical_value)  # For now, updating is the same as storing
            get_lvg_logger().info(f"Updated lexical value for lemma: {lexical_value.lemma}")
        except LexicalValueStorageError as e:
            get_lvg_logger().error(f"Failed to update lexical value for lemma {lexical_value.lemma}: {str(e)}")
            raise LexicalValueStorageError(f"Failed to update lexical value for lemma {lexical_value.lemma}") from e

    def delete(self, lemma: str) -> bool:
        file_path = self._get_file_path(lemma)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                get_lvg_logger().info(f"Deleted lexical value for lemma {lemma}")
                return True
            else:
                get_lvg_logger().warning(f"Lexical value for lemma {lemma} not found for deletion")
                return False
        except OSError as e:
            get_lvg_logger().error(f"Failed to delete lexical value for lemma {lemma}: {str(e)}")
            raise LexicalValueStorageError(f"Failed to delete lexical value for lemma {lemma}") from e

    def get_version_history(self, lemma: str) -> List[LexicalValue]:
        # This method should be implemented to retrieve version history
        # For now, we'll return a list with the current version only
        current_value = self.retrieve(lemma)
        if current_value:
            get_lvg_logger().info(f"Retrieved version history for lemma: {lemma}")
        else:
            get_lvg_logger().warning(f"No version history found for lemma: {lemma}")
        return [current_value] if current_value else []
