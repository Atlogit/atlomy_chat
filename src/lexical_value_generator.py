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
    You are an AI assistant specializing in ancient Greek lexicography and philology. You will build a lexcial value based on validatd texts analysis. Analyze the following word and its usage in the given citations:

    Word: {word}

    Citations:
    {citations}

    Based on these citations, provide:
    1. A concise translation of the word.
    2. A short description (4-5 sentences) of its meaning and usage.
    3. A longer, more detailed description (5-10 paragraphs) of its meaning, usage, and any notable connotations or context.
    4. A list of related terms or concepts.
    5. The references used, formatted as a list of citations.

    If no citations are provided, use your knowledge of ancient Greek to provide the best possible analysis.
    Include all citations you recieved, in the appropriate format.

    Present your analysis in a JSON format with the following structure:
    {{
        "lemma": "{word}",
        "translation": "Your translation here",
        "short_description": "Your short description here",
        "long_description": "Your long description here",
        "related_terms": ["term1", "term2", "term3"],
        "references": ["Citation 1", "Citation 2", "Citation 3"]
    }}
    
    examples for lexical terms writing:
    {{
    "lemma": "μετέωρος, -ον",
    "translation": "Raised, high, suspended",
    "short_description": "The term is a composite of the preposition μετά and the verb ἀείρω and literally means \"raised above\". Depending on the context, it may be translated as \"raised\", \"suspended\", \"high\", \"on the surface\", or metaphorically as \"uncertain\" or \"pending\". \n\nWhen referring to anatomical structures, it often means \"unsupported\" (e.g., Gal. AA 4.10, 469 Garofalo = 2.469 K – about a muscle not fixed to or resting on another) or hanging (Hipp. Fract. 7.31-34 – about using a sling to prevent the forearm from hanging).\n\nIn physiology, it can mean \"shallow\", particularly in relation to breathing (Gal. Diff. Resp., 7.946 K) or \"superficial\" (e.g., about pain: Hipp. Aph. 6.7 564 L.). However, when used in the context of the digestive system, it may mean inflated, unsettled (Hipp. Aph. 4.73 528 L., 5.64 556 L.).",
    "long_description": "The term is a composite of the preposition μετά and the verb ἀείρω and literally means \"raised above\". Depending on the context, it may be translated as \"raised\", \"suspended\", \"high\", \"on the surface\", or metaphorically as \"uncertain\" or \"pending\".\n\nWhen referring to anatomical structures, it often means \"unsupported\" (e.g., Gal. AA 4.10, 469 Garofalo = 2.469 K – about a muscle not fixed to or resting on another) or hanging (Hipp. Fract. 7, Jouanna 14,11 = 3.445 L. – about using a sling to prevent the forearm from hanging).\n\nIn physiology, it can mean \"shallow\", particularly in relation to breathing (Gal. Diff. Resp., 7.946 K.) or \"superficial\" (e.g., about pain: Hipp. Aph. 6.7 564 L.). However, when used in the context of the digestive system, it may mean inflated, unsettled (Hipp. Aph. 4.73 528 L., 5.64 556 L.).\n\nIdiomatically, the expression τὰ μετέωρα refers to things in the heaven above, heavenly bodies or to astronomical phenomena.",
    }}
    {{
    "lemma": "ἀρτηρία, -ας, f.",
    "translation": "Artery, Windpipe",
    "short_description": "The term artēria is attested since ancient classical Greek (Soph. Trach., 1054) with the meaning of conduit, passage channel, specifically to refer to the primary bronchi in the lungs and more often to refer to the channel of air passage between the oral cavity, the rhino-pharyngeal tract and the lungs, thus indicating the trachea. The windpipe, also sometimes designated by the singular term bronchos, is described as an air passage channel composed of cartilage and covered on the surface by small blood vessels. The upper cartilages of the trachea form the cartilaginous structure of the larynx that allows the articulation of vowel sounds.",
    "long_description": "In ancient Greek, the term artēria does not necessarily coincide with the blood vessels that the tradition of medical knowledge has over time referred to as arteries to indicate the blood channels that distribute from the heart throughout the body of the living being. Especially in the earliest attestations of the term in the ancient Greek classical period (5th-4th c. BCE) the noun artēria had a polysemous nature being used to refer to certain blood vessels, but also more generically to other tubular conduits allowing the passage of air (Soph. Tr., 1054). The polysemy of the term is partly explained linguistically by the derivation of the noun from an Indo-European root, *h2uer-, that conveys the meaning \"to connect, to join, to link together\" to which other verbs such as hartan would be related and with which it is also possible to link derivatives of the verb arariskō.\n\nAccording to this hypothesis, the term artēria would first indicate a connection, a junction between two different and distinct parts. In the specialized language of anatomy, this term was meant to denote any channel or pathway that allowed the junction between two different anatomical areas or between two different organs and the passage of substances from one to another. In this sense, the term in the plural form, artēriai, could also refer to the two primary bronchi that depart from the trachea into each of the two lungs (Pl. Tim., 78c 5-6). In the singular, the term artēria could refer to the trachea and the two primary bronchi could be designated as \"corridors\" or \"passageways\", ochetoi, of air from the trachea to the two lungs (Pl. Tim., 70d 2).\n\nAlternatively, another etymological hypothesis, explains the original meaning of artēria for the trachea or the bronchi that branch off from it from the suspension function that these anatomical parts would have had vis-à-vis the lungs hanging and suspended from these ducts. This etymological reconstruction links the term artēria to one of the meanings of the Greek verb aeirō expressing the action of lifting and suspending aloft. A similar sense would also be assigned to the original meaning of aortē which equally derived from the same root as aeirō would have indicated the aorta artery, especially the aortic ridge, as the suspension hook of the heart (cfr. e.g. Hom. Il., 11.609 for the term aortērreferring to the belt to which weapons are attached).\n\nAristotle seems to be aware of the polysemy and semantic fluidity of a term such as artēria not yet fixed in an unambiguous meaning in the specialized vocabulary of medicine. Therefore in at least one passage in the Historiaanimalium he refers to the trachea as that artēria which refers to (or is of) the lung (παρὰ τὴν ἀρτηρίαν τείνουσι τὴν τοῦπλεύμονος, Arist. HA, 3.3 Balme, 514a5-6), and in other passages he uses locutions such as \"the so-called\" or \"that which is called\" artēria (Arist. PA, 3.3 Louis, 664a 35-36; Arist. DA, 2.8 Ross, 420b 28-29).\n\nIn the two main biological treatises devoted to the anatomy and physiology of the living beings, that is the Historia animalium and the De partibus animalium, Aristotle uses the term artēria to refer exclusively to the trachea. This anatomical part is considered necessary for the physiology of respiration, anapnoē, and to produce sound, phōnē, by the animals. In the description provided by Aristotle, the duct of the trachea does not receive or transmit any fluid to the lungs, but only air. The entry of liquids into the trachea is considered contrary to the normal physiology of this organ causing pathological conditions in the body of the person who suffers it (Arist. PA, 3.3 Louis, 664b 6-18; cfr. Pl. Tim., 70c 1-d 6 where instead the entry of fluid into the trachea toward the lungs is described as a normal physiological process). Aristotle also refers to the trachea using the term gargareōn, which normally turns out to be, especially in non medical texts, a more generic name also referring to the region of the oropharyngeal wall and the area of the uvula (Aristotle. HA, 1.11 Balme, 492b 11).\n\nThe artēria is described as a firm and solid, internally smooth duct, leion, made of cartilaginous tissue, chondrōdes, and its position in the neck is described as always anterior to that of the esophagus (Arist. HA, 1.16 Balme, 495a 20-24: Arist. PA, 3.3 Louis, 664a 35-664b 2). According to Aristotle, the trachea is necessarily located in an anterior position because from the posterior region of the buccal cavity it descends forward to the anatomical area occupied by the heart and lungs, which hold an advanced position in the chest region (Arist. PA, 3.3 Louis, 665a 9-20). In contrast, if the trachea enters the lungs through the bronchi, there is no direct communication through channels between the heart and trachea. The trachea and the heart are separated from each other but appear to be linked by some ligaments forming a system of cords made of fat, cartilage and sinew that makes the two parts mutually attached, which remain separated by some concavity between them (Arist. HA, 1.16 Balme, 495b 12-16).",
    }}

    make sure your response is formatted for JSON.
    """

    def __init__(self, corpus_manager: CorpusManager, storage_dir: str = 'lexical_values', model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0", temperature: float = 0.5, default_search_lemma: bool = False):
        self.corpus_manager = corpus_manager
        self.storage = LexicalValueStorage(storage_dir)
        self.model_id = model_id
        self.temperature = temperature
        self.default_search_lemma = default_search_lemma
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

    def get_citations(self, word: str, search_lemma: Optional[bool] = None) -> List[Dict[str, str]]:
        try:
            search_lemma = self.default_search_lemma if search_lemma is None else search_lemma
            logger.info(f"Searching for citations of word: {word} (search_lemma: {search_lemma})")
            search_results = self.corpus_manager.search_texts(word, search_lemma=search_lemma)
            
            if not search_results:
                logger.warning(f"No citations found for word: {word}")
                return []

            citations = [item['sentence'] if isinstance(item, dict) and 'sentence' in item else str(item) for item in search_results]
            logger.debug(f"Text list before processing: {citations[:5]}...")  # Log first 5 items

            processed_citations = self.tlg_parser.process_texts(citations)
            logger.info(f"Found {len(processed_citations)} citations for word: {word}")
            return processed_citations
        except Exception as e:
            logger.error(f"Error getting citations for word '{word}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to get citations for word '{word}'") from e

    def generate_lexical_term(self, word: str, citations: List[str]) -> LexicalValue:
        try:
            prompt_template = PromptTemplate(
                input_variables=["word", "citations"],
                template=self.lexical_term_template
            )
            
            citations_text = "\n".join(citations) if citations else "No citations available."
            prompt = prompt_template.format(word=word, citations=citations_text)

            response = self.query_llm(prompt)
            logger.info(f"Generated lexical term for '{word}'")
            
            # Log the raw response for debugging
            logger.debug(f"Raw LLM response for '{word}': {response}")
                        
            # Sanitize response to remove invalid control characters
            sanitized_response = re.sub(r'[\x00-\x1F\x7F]', '', response)
            print("sanitized_response is: ", sanitized_response)
            
            # Extract JSON object from the response
            json_match = re.search(r'\{.*\}', sanitized_response, re.DOTALL)
            if not json_match:
                raise json.JSONDecodeError("No valid JSON object found in the response", sanitized_response, 0)


            lexical_value_dict = json.loads(json_match.group(0))
            print("lexical_value_dict is: ", lexical_value_dict)
            return LexicalValue(**lexical_value_dict)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for '{word}': {str(e)}")
            logger.error(f"Raw response that caused the error: {response}")
            raise LexicalValueGeneratorError(f"Invalid LLM response format for word '{word}'") from e
        except Exception as e:
            logger.error(f"Error generating lexical term for '{word}': {str(e)}")
            raise LexicalValueGeneratorError(f"Failed to generate lexical term for word '{word}'") from e

    def create_lexical_entry(self, word: str, search_lemma: Optional[bool] = None) -> LexicalValue:
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
            # Log the generated lexical value
            logger.debug(f"Generated lexical value: {lexical_value}")

            self.storage.store(lexical_value)
            
            logger.info(f"Created and stored lexical entry for '{word}'")
            return lexical_value
        except Exception as e:
            logger.error(f"Error creating lexical entry for '{word}': {str(e)}")
            logger.error(traceback.format_exc())
            raise LexicalValueGeneratorError(f"Failed to create lexical entry for word '{word}'") from e

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
