import json
import os
import re
from typing import List, Dict, Optional
from pathlib import Path
from src.lexical_value import LexicalValue
from src.corpus_manager import CorpusManager
from src.lexical_value_storage import LexicalValueStorage
from src.logging_config import initialize_logger, get_logger
from src.index_utils import TLGParser
from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
import traceback

# Initialize logger at module level
initialize_logger()
logger = get_logger()

class LexicalValueGeneratorError(Exception):
    """Custom exception for LexicalValueGenerator errors."""
    pass

class LexicalValueGenerator:
    lexical_term_template = """
    You are an AI assistant specializing in ancient Greek lexicography and philology. You will build a lexcial value based on validatd texts analysis on a PhD level. Analyze the following word or lemma and its usage in the given citations.
    
    Word to analyze (lemma): 
    {word}
    
    Citations:
    {citations}
    
    Task: Based on these citations, provide:
    1. A concise translation of the word.
    2. A short description (up to 2000 words) of its meaning and usage. This is a summary of the long description.
    3. A longer, more detailed description.
    4. A list of related terms or concepts.
    5. A list of citations you used in the short or long descriptions
    
    Formatting Instructions:
    Ensure your response is a valid JSON object.
    Properly escape all special characters (e.g., quotes, backslashes) to avoid JSON formatting errors.
    Ensure no truncation occurs.
    Double-check that your JSON is well-formed and escaped correctly according to the JSON specification.
    
    Example JSON Format:

    {{
    "lemma": "{word}",
    "translation": "Your translation here",
    "short_description": "Your short description here",
    "long_description": "Your long description here, ensuring that all special characters are properly escaped.",
    "related_terms": ["term1", "term2", "term3"],
    "citations_used": ["Citation 1", "Citation 2", "Citation 3"],
    }}

    Detailed Long Description:
    The description should include information derived from text analysis, covering meaning, usage, notable connotations, context, and any contradictions or variations in usage across different authors or texts. If no citations are provided, use your expertise in ancient Greek to provide the best possible analysis.

    If citations are provided, make sure to:
    * Reference them in the text to support your claims.
    * Cite them in the accustomed abbreviations. use the full citation in the citations_used section.
    * Make sure to close citations_used list with the brackets.
    
    References
    If citations are provided, you must use them in your analysis. Do not make up citations, don't use extrenal resources, only use what you are given by the user. Use the referencs to support your analysis, and cite them in the description when they prove a claim you make. When citing, do so in the accustomed abbreviations. Provide the full citations you used in the citations_used section. If no citations are provided, use your knowledge of ancient Greek to provide the best possible analysis.
    
    examples for finalized lexcial value:
    {{
    "lemma": "μετέωρος, -ον",
    "translation": "Raised, high, suspended",
    "short_description": "The term is a composite of the preposition μετά and the verb ἀείρω and literally means \"raised above\". Depending on the context, it may be translated as \"raised\", \"suspended\", \"high\", \"on the surface\", or metaphorically as \"uncertain\" or \"pending\". \n\nWhen referring to anatomical structures, it often means \"unsupported\" (e.g., Gal. AA 4.10, 469 Garofalo = 2.469 K – about a muscle not fixed to or resting on another) or hanging (Hipp. Fract. 7.31-34 – about using a sling to prevent the forearm from hanging).\n\nIn physiology, it can mean \"shallow\", particularly in relation to breathing (Gal. Diff. Resp., 7.946 K) or \"superficial\" (e.g., about pain: Hipp. Aph. 6.7 564 L.). However, when used in the context of the digestive system, it may mean inflated, unsettled (Hipp. Aph. 4.73 528 L., 5.64 556 L.).",
    "long_description": "The term is a composite of the preposition μετά and the verb ἀείρω and literally means \"raised above\". Depending on the context, it may be translated as \"raised\", \"suspended\", \"high\", \"on the surface\", or metaphorically as \"uncertain\" or \"pending\".\n\nWhen referring to anatomical structures, it often means \"unsupported\" (e.g., Gal. AA 4.10, 469 Garofalo = 2.469 K – about a muscle not fixed to or resting on another) or hanging (Hipp. Fract. 7, Jouanna 14,11 = 3.445 L. – about using a sling to prevent the forearm from hanging).\n\nIn physiology, it can mean \"shallow\", particularly in relation to breathing (Gal. Diff. Resp., 7.946 K.) or \"superficial\" (e.g., about pain: Hipp. Aph. 6.7 564 L.). However, when used in the context of the digestive system, it may mean inflated, unsettled (Hipp. Aph. 4.73 528 L., 5.64 556 L.).\n\nIdiomatically, the expression τὰ μετέωρα refers to things in the heaven above, heavenly bodies or to astronomical phenomena.",
    }}

    """

    def __init__(self, corpus_manager: CorpusManager, storage_dir: str = 'lexical_values', model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0", region: str = "us-east-1", temperature: float = 0.5, max_tokens: int = 8092, default_search_lemma: bool = False):
        self.corpus_manager = corpus_manager
        self.storage = LexicalValueStorage(storage_dir)
        self.model_id = model_id
        self.region = region
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.default_search_lemma = default_search_lemma
        try:
            self.llm = ChatBedrock(model_id=self.model_id, temperature=self.temperature, region=self.region)
            logger.info(f"LexicalValueGenerator initialized with model_id: {model_id}, region: {region}, temperature: {temperature}")
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
            logger.info(f"Querying the LLM model with prompt: {prompt}")
            logger.debug(f"length of prompt: {len(prompt)}")
            human_message = HumanMessage(content=prompt)
            # Use the `invoke` method instead of `__call__`
            answer = self.llm.invoke([human_message])
            logger.debug(f"Received answer from LLM: {answer.content[:100]}...")
            return answer.content
        except Exception as e:
            logger.error(f"Error querying LLM: {str(e)}")
            raise LexicalValueGeneratorError("Failed to query LLM") from e

    def get_citations(self, word: str, search_lemma: Optional[bool] = None) -> List[Dict[str, str]]:
        try:
            search_lemma = self.default_search_lemma if search_lemma is None else search_lemma
            logger.info(f"Searching for citations of word: {word} (search_lemma: {search_lemma})")
            search_results = self.corpus_manager.search_texts(word, search_lemma=search_lemma)
            
            if not search_results:
                logger.warning(f"No citations found for word: {word}")
                return []
            citations = []
            citations = [item['sentence'] if isinstance(item, dict) and 'sentence' in item else str(item) for item in search_results]
            logger.debug(f"Text list before processing: {citations[:5]}...")  # Log first 5 items

            processed_citations = self.tlg_parser.process_texts(citations)
            logger.info(f"Found {len(processed_citations)} citations for word: {word}")
            return processed_citations
        except Exception as e:
            logger.error(f"Error getting citations for word '{word}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to get citations for word '{word}'") from e

    def generate_lexical_term(self, word: str, citations: List[str]) -> Optional[LexicalValue]:        
        try:
            prompt_template = PromptTemplate(
                input_variables=["word", "citations"],
                template=self.lexical_term_template
            )
            
            citations_text = "\n".join(citations) if citations else "No citations available."
            prompt = prompt_template.format(word=word, citations=citations_text)

            logger.info(f"Generating lexical term for '{word}'")
            response = self.query_llm(prompt)
            logger.info(f"Received response from LLM for '{word}'")
            
            # Log the raw response for debugging
            logger.info(f"Full raw LLM response for '{word}': {response}")

            # Sanitize response to remove invalid control characters
            sanitized_response = re.sub(r'[\x00-\x1F\x7F]', '', response)
            logger.debug(f"Sanitized response: {sanitized_response}")
            
            # Try to find JSON object in the response
            json_match = re.search(r'\{.*\}', sanitized_response, re.DOTALL)
            if not json_match:
                logger.warning(f"No valid JSON object found in the response for '{word}'")
                logger.info(f"Full sanitized response: {sanitized_response}")
                return None

            json_str = json_match.group(0)
            logger.debug(f"Extracted JSON string: {json_str}")

            try:
                lexical_value_dict = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON for '{word}': {str(e)}")
                logger.debug(f"JSON string that caused the error: {json_str}")
                return None
            
            # Add citations to the dictionary
            lexical_value_dict['references'] = citations

            logger.info(f"Successfully parsed JSON for '{word}'")
            logger.debug(f"Parsed lexical value dict: {lexical_value_dict}")

            # Ensure all required fields are present
            required_fields = ['lemma', 'translation', 'short_description', 'long_description', 'related_terms', 'citations_used', 'references']
            missing_fields = [field for field in required_fields if field not in lexical_value_dict]
            if missing_fields:
                logger.warning(f"Missing required fields for '{word}': {', '.join(missing_fields)}")
                return None

            return LexicalValue(**lexical_value_dict)
        except Exception as e:
            logger.error(f"Error generating lexical term for '{word}': {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def create_lexical_entry(self, word: str, search_lemma: Optional[bool] = None) -> Optional[LexicalValue]:
            try:
                logger.info(f"Creating lexical entry for word: {word}")
                # Log the search_lemma value
                logger.debug(f"search_lemma: {search_lemma}")
            
                citations = self.get_citations(word, search_lemma)
                
                # Log the retrieved citations
                logger.debug(f"Citations retrieved: {citations}")

                if not citations:
                    logger.warning(f"No citations found for word '{word}'. Proceeding with empty citations.")
                
                lexical_value = self.generate_lexical_term(word, citations)
                
                if lexical_value is None:
                    logger.warning(f"Failed to generate lexical term for '{word}'. Creating a minimal entry.")
                    lexical_value = LexicalValue(
                        lemma=word,
                        translation="",
                        short_description="No description available.",
                        long_description="No detailed description available.",
                        related_terms=[],
                        citations_used=[],
                        references=citations
                    )
                
                logger.debug(f"Generated lexical value: {lexical_value}")

                logger.info(f"Storing lexical value for '{word}'")
                self.storage.store(lexical_value)
                
                logger.info(f"Created and stored lexical entry for '{word}'")
                return lexical_value
            except Exception as e:
                logger.error(f"Error creating lexical entry for '{word}': {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return None
        
    def get_lexical_value(self, lemma: str) -> Optional[LexicalValue]:
        try:
            logger.info(f"Retrieving lexical value for lemma: {lemma}")
            lexical_value = self.storage.retrieve(lemma)
            if lexical_value is None:
                logger.warning(f"No lexical value found for lemma: {lemma}")
            return lexical_value
        except Exception as e:
            logger.error(f"Error retrieving lexical value for '{lemma}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to retrieve lexical value for lemma '{lemma}'") from e

    def list_lexical_values(self) -> List[str]:
        try:
            logger.info("Listing all lexical values")
            values = self.storage.list_all()
            logger.info(f"Found {len(values)} lexical values")
            return values
        except Exception as e:
            logger.error(f"Error listing lexical values: {str(e)}")
            raise LexicalValueGeneratorError("Failed to list lexical values") from e

    def update_lexical_value(self, lexical_value: LexicalValue) -> None:
        try:
            logger.info(f"Updating lexical value for lemma: {lexical_value.lemma}")
            self.storage.update(lexical_value)
            logger.info(f"Updated lexical value for '{lexical_value.lemma}'")
        except Exception as e:
            logger.error(f"Error updating lexical value for '{lexical_value.lemma}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to update lexical value for lemma '{lexical_value.lemma}'") from e

    def delete_lexical_value(self, lemma: str) -> bool:
        try:
            logger.info(f"Deleting lexical value for lemma: {lemma}")
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
    from .logging_config import initialize_logger
    initialize_logger()
    logger = logger
    
    try:
        corpus_manager = CorpusManager()
        generator = LexicalValueGenerator(corpus_manager)
        
        # Example: Create lexical entry searching by word
        word_entry = generator.create_lexical_entry("φλέψ", search_lemma=False)
        print("Word entry:")
        print(json.dumps(word_entry.__dict__, indent=2, ensure_ascii=False))
        
        # Example: Create lexical entry searching by lemma
        lemma_entry = generator.create_lexical_entry("φλέψ", search_lemma=True)
        print("\nLemma entry:")
        print(json.dumps(lemma_entry.__dict__, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error in example usage: {str(e)}")
        print(f"An error occurred: {str(e)}")
