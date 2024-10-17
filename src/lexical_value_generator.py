import json
import os
from typing import List, Dict, Optional
from pathlib import Path
from .lexical_value import LexicalValue
from .corpus_manager import CorpusManager
from .lexical_value_storage import LexicalValueStorage
from .logging_config import logger
from .index_utils import TLGParser
from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

class LexicalValueGeneratorError(Exception):
    """Custom exception for LexicalValueGenerator errors."""
    pass

class LexicalValueGenerator:
    lexical_term_template = """
    You are an AI assistant specializing in ancient Greek lexicography. Analyze the following word and its usage in the given citations:

    Word: {word}

    Citations:
    {citations}

    Based on these citations, provide:
    1. A concise translation of the word.
    2. A short description (2-3 sentences) of its meaning and usage.
    3. A longer, more detailed description (1-2 paragraphs) of its meaning, usage, and any notable connotations or context.
    4. A list of related terms or concepts.
    5. The references used, formatted as a list of citations.

    Present your analysis in a JSON format with the following structure:
    {{
        "lemma": "{word}",
        "translation": "Your translation here",
        "short_description": "Your short description here",
        "long_description": "Your long description here",
        "related_terms": ["term1", "term2", "term3"],
        "references": ["Citation 1", "Citation 2", "Citation 3"]
    }}
    """

    def __init__(self, corpus_manager: CorpusManager, storage_dir: str = 'lexical_values', model_id: str = "anthropic.claude-3-haiku-20240307-v1:0", temperature: float = 0.5):
        self.corpus_manager = corpus_manager
        self.storage = LexicalValueStorage(storage_dir)
        self.model_id = model_id
        self.temperature = temperature
        try:
            self.llm = ChatBedrock(model_id=self.model_id, temperature=self.temperature)
            logger.info(f"LexicalValueGenerator initialized with model_id: {model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize ChatBedrock: {str(e)}")
            raise LexicalValueGeneratorError("Failed to initialize ChatBedrock") from e

        # Initialize TLGParser
        try:
            script_dir = Path(__file__).resolve().parent
            project_root = script_dir.parent
            authors_path = project_root / "assets" / "indexes" / "tlg_index.py"
            works_path = project_root / "assets" / "indexes" / "work_numbers.py"
            self.tlg_parser = TLGParser(str(authors_path), str(works_path))
            logger.info(f"Initialized TLGParser with authors_path: {authors_path} and works_path: {works_path}")
        except Exception as e:
            logger.error(f"Failed to initialize TLGParser: {str(e)}")
            raise LexicalValueGeneratorError("Failed to initialize TLGParser") from e

    def query_llm(self, prompt: str) -> str:
        try:
            logger.info(f"Querying the LLM model with prompt: {prompt[:50]}...")
            human_message = HumanMessage(content=prompt)
            answer = self.llm([human_message])
            logger.debug(f"Received answer from LLM: {answer.content[:100]}...")
            return answer.content
        except Exception as e:
            logger.error(f"Error querying LLM: {str(e)}")
            raise LexicalValueGeneratorError("Failed to query LLM") from e

    def get_citations(self, word: str) -> List[Dict[str, str]]:
        try:
            query = f"Find sentences containing the word '{word}'"
            result = self.corpus_manager.search_texts(query)
            processed_result = self.tlg_parser.process_texts(result)
            logger.info(f"Found {len(processed_result)} citations for word: {word}")
            return processed_result
        except Exception as e:
            logger.error(f"Error getting citations for word '{word}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to get citations for word '{word}'") from e

    def generate_lexical_term(self, word: str, citations: List[str]) -> LexicalValue:
        try:
            prompt_template = PromptTemplate(
                input_variables=["word", "citations"],
                template=self.lexical_term_template
            )
            
            citations_text = "\n".join(citations)
            prompt = prompt_template.format(word=word, citations=citations_text)

            response = self.query_llm(prompt)
            logger.info(f"Generated lexical term for '{word}'")

            lexical_value_dict = json.loads(response)
            return LexicalValue(**lexical_value_dict)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for '{word}': {str(e)}")
            raise LexicalValueGeneratorError(f"Invalid LLM response format for word '{word}'") from e
        except Exception as e:
            logger.error(f"Error generating lexical term for '{word}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to generate lexical term for word '{word}'") from e

    def create_lexical_entry(self, word: str) -> LexicalValue:
        try:
            citations = self.get_citations(word)
            lexical_value = self.generate_lexical_term(word, citations)
            self.storage.store(lexical_value)
            logger.info(f"Created and stored lexical entry for '{word}'")
            return lexical_value
        except Exception as e:
            logger.error(f"Error creating lexical entry for '{word}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to create lexical entry for word '{word}'") from e

    def get_lexical_value(self, lemma: str) -> Optional[LexicalValue]:
        try:
            return self.storage.retrieve(lemma)
        except Exception as e:
            logger.error(f"Error retrieving lexical value for '{lemma}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to retrieve lexical value for lemma '{lemma}'") from e

    def list_lexical_values(self) -> List[str]:
        try:
            return self.storage.list_all()
        except Exception as e:
            logger.error(f"Error listing lexical values: {str(e)}")
            raise LexicalValueGeneratorError("Failed to list lexical values") from e

    def update_lexical_value(self, lexical_value: LexicalValue) -> None:
        try:
            self.storage.update(lexical_value)
            logger.info(f"Updated lexical value for '{lexical_value.lemma}'")
        except Exception as e:
            logger.error(f"Error updating lexical value for '{lexical_value.lemma}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to update lexical value for lemma '{lexical_value.lemma}'") from e

    def delete_lexical_value(self, lemma: str) -> bool:
        try:
            result = self.storage.delete(lemma)
            if result:
                logger.info(f"Deleted lexical value for '{lemma}'")
            else:
                logger.warning(f"Lexical value for '{lemma}' not found or could not be deleted")
            return result
        except Exception as e:
            logger.error(f"Error deleting lexical value for '{lemma}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to delete lexical value for lemma '{lemma}'") from e

# Example usage
if __name__ == "__main__":
    try:
        corpus_manager = CorpusManager()
        generator = LexicalValueGenerator(corpus_manager)
        lexical_entry = generator.create_lexical_entry("ἀρτηρία")
        print(json.dumps(lexical_entry.__dict__, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error in example usage: {str(e)}")
        print(f"An error occurred: {str(e)}")
