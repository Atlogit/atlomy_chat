import os
import json
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Set
from pathlib import Path
from filelock import FileLock
from src.lexical_value import LexicalValue
from src.corpus_manager import CorpusManager
from src.lexical_value_storage import LexicalValueStorage
from src.logging_config import get_logger
from src.lexical_value_generator import LexicalValueGenerator, LexicalValueGeneratorError

logger = get_logger()

class ThreadSafeLexicalStorage(LexicalValueStorage):
    """Thread-safe version of LexicalValueStorage"""
    
    def __init__(self, storage_dir: str):
        super().__init__(storage_dir)
        self.locks = {}
        self.locks_lock = threading.Lock()
        
    def _get_lock(self, lemma: str) -> FileLock:
        """Get or create a FileLock for a given lemma"""
        with self.locks_lock:
            if lemma not in self.locks:
                lock_path = os.path.join(self.storage_dir, f"{lemma}.lock")
                self.locks[lemma] = FileLock(lock_path)
            return self.locks[lemma]
    
    def store(self, lexical_value: LexicalValue) -> None:
        lock = self._get_lock(lexical_value.lemma)
        with lock:
            super().store(lexical_value)
    
    def retrieve(self, lemma: str) -> Optional[LexicalValue]:
        lock = self._get_lock(lemma)
        with lock:
            return super().retrieve(lemma)
    
    def update(self, lexical_value: LexicalValue) -> None:
        lock = self._get_lock(lexical_value.lemma)
        with lock:
            super().update(lexical_value)
    
    def delete(self, lemma: str) -> bool:
        lock = self._get_lock(lemma)
        with lock:
            return super().delete(lemma)

class ParallelLexicalGenerator(LexicalValueGenerator):
    """Parallel implementation of LexicalValueGenerator"""
    
    def __init__(self, corpus_manager: CorpusManager, storage_dir: str = 'lexical_values',
                 model_id: str = "anthropic.claude-3-sonnet-20240620-v1:0",
                 temperature: float = 0.5, default_search_lemma: bool = False,
                 max_workers: int = 4):
        # Initialize with thread-safe storage
        super().__init__(corpus_manager, storage_dir, model_id, temperature, default_search_lemma)
        self.storage = ThreadSafeLexicalStorage(storage_dir)
        self.max_workers = max_workers
        self.citation_queue = queue.Queue()
        self.processing_lock = threading.Lock()
    
    def process_citations_batch(self, citations: List[str]) -> List[Dict[str, str]]:
        """Process a batch of citations in parallel"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.tlg_parser.process_text, citation) 
                      for citation in citations]
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error processing citation: {str(e)}")
            return results

    def get_citations(self, word: str, search_lemma: Optional[bool] = None) -> List[Dict[str, str]]:
        """Get citations using parallel processing"""
        try:
            search_lemma = self.default_search_lemma if search_lemma is None else search_lemma
            logger.info(f"Searching for citations of word: {word} (search_lemma: {search_lemma})")
            
            # Get raw search results
            search_results = self.corpus_manager.search_texts(word, search_lemma=search_lemma)
            if not search_results:
                logger.warning(f"No citations found for word: {word}")
                return []
            
            # Extract citations
            citations = [item['sentence'] if isinstance(item, dict) and 'sentence' in item 
                        else str(item) for item in search_results]
            
            # Process citations in parallel batches
            batch_size = max(1, len(citations) // self.max_workers)
            batches = [citations[i:i + batch_size] for i in range(0, len(citations), batch_size)]
            
            processed_citations = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self.process_citations_batch, batch) 
                          for batch in batches]
                for future in as_completed(futures):
                    try:
                        results = future.result()
                        processed_citations.extend(results)
                    except Exception as e:
                        logger.error(f"Error processing citation batch: {str(e)}")
            
            logger.info(f"Found {len(processed_citations)} citations for word: {word}")
            return processed_citations
            
        except Exception as e:
            logger.error(f"Error getting citations for word '{word}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to get citations for word '{word}'") from e

    def create_lexical_entries_batch(self, words: List[str], 
                                   search_lemma: Optional[bool] = None) -> Dict[str, LexicalValue]:
        """Create multiple lexical entries in parallel"""
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_word = {
                executor.submit(self.create_lexical_entry, word, search_lemma): word 
                for word in words
            }
            for future in as_completed(future_to_word):
                word = future_to_word[future]
                try:
                    lexical_value = future.result()
                    results[word] = lexical_value
                except Exception as e:
                    logger.error(f"Error creating lexical entry for '{word}': {str(e)}")
                    results[word] = None
        return results

    def update_lexical_values_batch(self, lexical_values: List[LexicalValue]) -> Dict[str, bool]:
        """Update multiple lexical values in parallel"""
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_lemma = {
                executor.submit(self.update_lexical_value, lv): lv.lemma 
                for lv in lexical_values
            }
            for future in as_completed(future_to_lemma):
                lemma = future_to_lemma[future]
                try:
                    future.result()
                    results[lemma] = True
                except Exception as e:
                    logger.error(f"Error updating lexical value for '{lemma}': {str(e)}")
                    results[lemma] = False
        return results

if __name__ == "__main__":
    # Example usage
    try:
        corpus_manager = CorpusManager()
        generator = ParallelLexicalGenerator(corpus_manager)
        
        # Example: Create multiple lexical entries in parallel
        words = ["φλέψ", "ἀρτηρία", "νεῦρον"]
        results = generator.create_lexical_entries_batch(words)
        
        for word, value in results.items():
            if value:
                print(f"\nLexical entry for {word}:")
                print(json.dumps(value.__dict__, indent=2, ensure_ascii=False))
            else:
                print(f"\nFailed to create lexical entry for {word}")
                
    except Exception as e:
        logger.error(f"Error in example usage: {str(e)}")
        print(f"An error occurred: {str(e)}")
