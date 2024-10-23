import os
import json
from lexical_value_storage import LexicalValueStorage
from logging_config import get_logger, initialize_logger
import re
from typing import List, Dict, Any
import unicodedata

# Initialize logger at module level
initialize_logger()
logger = get_logger()

class CorpusManager:
    def __init__(self, corpus_dir: str = None):
        if corpus_dir is None:
            # Use the default path relative to the project root
            self.corpus_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'texts', 'annotated')
        else:
            self.corpus_dir = corpus_dir
        self.processed_texts: Dict[str, Any] = {}
        logger.info(f"CorpusManager initialized with corpus directory: {self.corpus_dir}")
        # Load all texts during initialization
        #self.get_all_texts()

    def import_text(self, file_path: str) -> None:
        """
        Import a text file into the corpus.
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            file_name = os.path.basename(file_path)
            output_path = os.path.join(self.corpus_dir, f"{os.path.splitext(file_name)[0]}_tagged.jsonl")

            # Import the parsers here
            from data_parsing.tlg_parser import create_data as tlg_create_data
            from data_parsing.text_parsing import create_data as text_create_data

            # Determine which parser to use based on the file name
            if file_name.startswith('TLG'):
                tlg_create_data(file_path, self)
            else:
                text_create_data(file_path, self)

            # Load the processed data
            self.processed_texts[file_name] = self._load_jsonl(output_path)
            logger.info(f"Successfully imported text: {file_name}")
        except Exception as e:
            logger.error(f"Error importing text {file_path}: {str(e)}")
            raise

    def _load_jsonl(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load processed data from a JSONL file.
        """
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data.append(json.loads(line))
            logger.debug(f"Successfully loaded JSONL file: {file_path}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON in file {file_path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error loading JSONL file {file_path}: {str(e)}")
            raise

    def get_text(self, file_name: str) -> List[Dict[str, Any]]:
        """
        Retrieve a processed text from the corpus.
        """
        try:
            if file_name not in self.processed_texts:
                jsonl_path = os.path.join(self.corpus_dir, f"{os.path.splitext(file_name)[0]}_tagged.jsonl")
                if os.path.exists(jsonl_path):
                    self.processed_texts[file_name] = self._load_jsonl(jsonl_path)
                else:
                    raise FileNotFoundError(f"Processed text not found: {file_name}")
            logger.info(f"Retrieved text: {file_name}")
            return self.processed_texts[file_name]
        except Exception as e:
            logger.error(f"Error retrieving text {file_name}: {str(e)}")
            raise

    def get_all_texts(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve all processed texts from the corpus.
        """
        try:
            for file_name in os.listdir(self.corpus_dir):
                if file_name.endswith('_tagged.jsonl'):
                    text_id = file_name.replace('_tagged.jsonl', '')
                    if text_id not in self.processed_texts:
                        self.processed_texts[text_id] = self._load_jsonl(os.path.join(self.corpus_dir, file_name))
            logger.info(f"Retrieved all texts: {len(self.processed_texts)} texts loaded")
            return self.processed_texts
        except Exception as e:
            logger.error(f"Error retrieving all texts: {str(e)}")
            raise

    def list_texts(self) -> List[str]:
        """
        List all processed texts in the corpus.
        """
        texts = list(self.processed_texts.keys())
        logger.info(f"Listed {len(texts)} texts in the corpus")
        return texts

    def add_text(self, text_id: str, tagged_data: List[Dict[str, Any]]) -> None:
        """
        Add a processed text to the corpus. If the text already exists, update it.
        """
        try:
            if self.text_exists(text_id):
                self.update_text(text_id, tagged_data)
            else:
                self.processed_texts[text_id] = tagged_data
                output_path = os.path.join(self.corpus_dir, f"{text_id}_tagged.jsonl")
                self._save_jsonl(output_path, tagged_data)
                logger.info(f"Added new text: {text_id}")
        except Exception as e:
            logger.error(f"Error adding text {text_id}: {str(e)}")
            raise

    def update_text(self, text_id: str, tagged_data: List[Dict[str, Any]]) -> None:
        """
        Update an existing processed text in the corpus.
        """
        try:
            if not self.text_exists(text_id):
                raise FileNotFoundError(f"Text not found in corpus: {text_id}")
            
            self.processed_texts[text_id] = tagged_data
            output_path = os.path.join(self.corpus_dir, f"{text_id}_tagged.jsonl")
            self._save_jsonl(output_path, tagged_data)
            logger.info(f"Updated existing text: {text_id}")
        except Exception as e:
            logger.error(f"Error updating text {text_id}: {str(e)}")
            raise

    def remove_text(self, text_id: str) -> None:
        """
        Remove a processed text from the corpus.
        """
        try:
            if not self.text_exists(text_id):
                raise FileNotFoundError(f"Text not found in corpus: {text_id}")
            
            # Remove from in-memory dictionary
            if text_id in self.processed_texts:
                del self.processed_texts[text_id]
            
            # Remove the JSONL file
            output_path = os.path.join(self.corpus_dir, f"{text_id}_tagged.jsonl")
            os.remove(output_path)
            logger.info(f"Removed text from corpus: {text_id}")
        except OSError as e:
            logger.error(f"Error removing file for text {text_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error removing text {text_id}: {str(e)}")
            raise

    def _save_jsonl(self, file_path: str, data: List[Dict[str, Any]]) -> None:
        """
        Save processed data to a JSONL file.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for item in data:
                    json.dump(item, f, ensure_ascii=False)
                    f.write('\n')
            logger.debug(f"Successfully saved JSONL file: {file_path}")
        except Exception as e:
            logger.error(f"Error saving JSONL file {file_path}: {str(e)}")
            raise

    def save_texts(self) -> None:
        """
        Save all processed texts to JSONL files.
        """
        try:
            for text_id, data in self.processed_texts.items():
                output_path = os.path.join(self.corpus_dir, f"{text_id}_tagged.jsonl")
                self._save_jsonl(output_path, data)
            logger.info(f"Saved all {len(self.processed_texts)} texts to JSONL files")
        except Exception as e:
            logger.error(f"Error saving all texts: {str(e)}")
            raise

    def text_exists(self, text_id: str) -> bool:
        """
        Check if a processed text file already exists in the corpus directory.
        """
        output_path = os.path.join(self.corpus_dir, f"{text_id}_tagged.jsonl")
        exists = os.path.exists(output_path)
        logger.debug(f"Checked existence of text {text_id}: {'exists' if exists else 'does not exist'}")
        return exists

    def search_texts(self, word: str = None, search_lemma: bool = False) -> List[Dict[str, Any]]:
        """
        Search across multiple texts in the corpus and return a list of sentences matching the given query.
        If search_lemma is True, search for the query in the lemmas instead of the text.
        """
        try:
            results = []
            logger.debug(f"Searching texts with query: {word}")
            
            if not self.processed_texts:
                logger.warning("No texts loaded in the corpus. Loading all available texts.")
                self.get_all_texts()
            
            normalized_word = unicodedata.normalize('NFD', word.lower())
            
            for text_id, sentences in self.processed_texts.items():
                logger.debug(f"Searching in text: {text_id}")
                for sentence in sentences:
                    if search_lemma:
                        if any(unicodedata.normalize('NFD', token.get('lemma', '').lower()) == normalized_word for token in sentence.get('tokens', [])):
                            results.append({
                                'text_id': text_id,
                                'sentence': sentence['text'],
                                'tokens': sentence['tokens']
                            })
                    else:
                        normalized_sentence = unicodedata.normalize('NFD', sentence['text'].lower())
                        if normalized_word in normalized_sentence:
                            results.append({
                                'text_id': text_id,
                                'sentence': sentence['text'],
                                'tokens': sentence['tokens']
                            })
            logger.info(f"Found {len(results)} matches for query: {word}")
            print("type resulkts is: ", type(results))
            return results
        except Exception as e:
            logger.error(f"Error searching texts with query '{word}': {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    initialize_logger()
    logger = get_logger()
    
    try:
        corpus_manager = CorpusManager()
        corpus_manager.import_text(os.path.join("..", "assets", "texts", "original", "TLG_sample.txt"))
        corpus_manager.import_text(os.path.join("..", "assets", "texts", "original", "other_text_file.txt"))
        print(corpus_manager.list_texts())
        text_data = corpus_manager.get_text("TLG_sample.txt")
        print(f"Number of sentences in TLG_sample.txt: {len(text_data)}")

        # Example of updating a text
        updated_data = [{"text": "Updated sentence", "tokens": []}]
        corpus_manager.update_text("TLG_sample.txt", updated_data)
        print("Text updated successfully")

        # Example of removing a text
        corpus_manager.remove_text("other_text_file.txt")
        print("Text removed successfully")

        print("Remaining texts:", corpus_manager.list_texts())

        # Example of searching texts
        search_results = corpus_manager.search_texts("example")
        print(f"Search results: {len(search_results)} matches found")
        for result in search_results[:5]:  # Print first 5 results
            print(f"Text: {result['text_id']}, Sentence: {result['sentence'][:50]}...")

        # Example of searching for a lemma
        lemma_search_results = corpus_manager.search_texts("λόγος", search_lemma=True)
        print(f"Lemma search results: {len(lemma_search_results)} matches found")
        for result in lemma_search_results[:5]:  # Print first 5 results
            print(f"Text: {result['text_id']}, Sentence: {result['sentence'][:50]}...")

        # Example of getting all texts
        all_texts = corpus_manager.get_all_texts()
        print(f"Total number of texts: {len(all_texts)}")
        for text_id, sentences in all_texts.items():
            print(f"Text: {text_id}, Number of sentences: {len(sentences)}")

    except Exception as e:
        logger.error(f"An error occurred in the main execution: {str(e)}")
