import json
import re
import os
import argparse
from langchain_aws import ChatBedrock

from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

# Import TLGParser class for reference details conversion
from .index_utils import TLGParser
# Import logger from logging_config
from .logging_config import initialize_logger, get_logger
# Import CorpusManager for centralized text management
from .corpus_manager import CorpusManager, get_corpus_logger
# Import LexicalValueGenerator
from .lexical_value_generator import LexicalValueGenerator, get_lvg_logger

class LLMAssistant:
    # Updated data query template to reflect new CorpusManager methods
    data_query_template = """
    You are an AI assistant that generates Python code based on specific instructions. You are working with a CorpusManager object named "corpus_manager" with the following methods:
    - get_text(text_id): Returns a list of dictionaries representing sentences for the given text_id.
    - get_all_texts(): Returns a dictionary where keys are text_ids and values are lists of sentence dictionaries.
    - search_texts(query, search_lemma=False): Returns a list of sentences matching the given query. If search_lemma is True, it searches for the query in the lemmas instead of the text.

    Each sentence dictionary has the following structure:
    {{
    'text': 'The full text of the sentence',
    'tokens': [
    {{
    'lemma': 'lemma of the word',
    'pos': 'part of speech',
    'tag': 'additional tags',
    'dep': 'dependency label',
    'morph': '{{morphological features}}',
    'category': 'specific categories the word belongs to',
    'text': 'the word itself'
    }},
    # ... more tokens ...
    ]
    }}

    Your task:
    1. Write a Python code snippet that answers the following question: {question}
    2. Store the result in a variable named 'result'.
    3. Do not include any explanations or comments.
    4. Only output the code wrapped in ```python``` markers.

    Question: {question}
    """

    def __init__(self, corpus_manager, model_id="anthropic.claude-3-haiku-20240307-v1:0", temperature=0.5):
        self.model_id = model_id
        self.temperature = temperature
        self.corpus_manager = corpus_manager
        self.llm = ChatBedrock(model_id=self.model_id, temperature=self.temperature)
        logger.info(f"LLMAssistant initialized with model_id: {model_id}")

    def query_llm(self, query):
        logger.info(f"Querying the LLM model with query: {query[:50]}...")
        
        user_prompt = PromptTemplate.from_template(self.data_query_template)
        logger.debug(f"Generated prompt: {user_prompt.format(question=query)[:100]}...")
        human_message = HumanMessage(content=user_prompt.format(question=query))
        answer = self.llm([human_message])
        logger.debug(f"Received answer from LLM: {answer.content[:100]}...")
        return answer.content

    def the_universal_function(self, python_code, variables_dict):
        logger.debug("Executing generated Python code")
        exec(python_code, variables_dict)

    def _extract_code(self, input_string):
        pattern = r'```python(.*?)```'
        match = re.search(pattern, input_string, re.DOTALL) # DOTALL flag allows . to match newline characters
        if match:
            logger.debug("Successfully extracted Python code from LLM response")
            return match.group(1).strip()
        else:
            logger.warning("No valid Python code found in LLM response")
            return None

    def ask_about_data(self, data_query):
        # Use an absolute path or a path relative to the script's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        authors_path = os.path.join(project_root, "assets", "indexes", "tlg_index.py")
        works_path = os.path.join(project_root, "assets", "indexes", "work_numbers.py")
        
        # Initialize the handler with the path to the TLG_INDEX file
        handler = TLGParser(authors_path, works_path)
        logger.info(f"Initialized TLGParser with authors_path: {authors_path} and works_path: {works_path}")

        attempts = 0

        while attempts < 3:
            try:
                logger.info(f"Attempt {attempts + 1} to process data query")
                answer = self.query_llm(data_query)
                logger.info(f"Received answer from LLM: {answer}")
                code_from_answer = self._extract_code(answer)
                logger.debug(f"Extracted Python code: {code_from_answer}")
                if code_from_answer is None:
                    raise ValueError("No valid Python code found in the response")
                
                vars_dict = {"result": None, "corpus_manager": self.corpus_manager}
                logger.debug(f"Executing generated code: {code_from_answer}")
                self.the_universal_function(code_from_answer, vars_dict)
                logger.debug(f"Code execution completed. Result type: {type(vars_dict['result'])}")

                if vars_dict['result'] is None:
                    raise ValueError("The 'result' variable was not set by the generated code")
                elif not isinstance(vars_dict['result'], list):
                    logger.warning(f"Result is not a list. Converting to list. Current type: {type(vars_dict['result'])}")
                    vars_dict['result'] = [vars_dict['result']]
                
                result = vars_dict['result']
                logger.debug(f"Result before processing: {result[:5]}...")  # Log first 5 items
                # Handle both string and dictionary items in the result list
                text_list = [item['text'] if isinstance(item, dict) and 'text' in item else str(item) for item in result]
                logger.debug(f"Text list before processing: {text_list[:5]}...")  # Log first 5 items
                processed_result = handler.process_texts(text_list)
                logger.info("Successfully processed data query")
                logger.debug(f"Processed result: {processed_result[:5]}...")  # Log first 5 items
                return processed_result
            except Exception as e:
                attempts += 1
                logger.error(f"Attempt {attempts} failed with error: {str(e)}")

        logger.error("All attempts failed. Handle the failure accordingly.")
        return None

def interactive_test(oracle, lexical_generator):
    logger = get_logger()
    logger.info("Starting interactive test")
    while True:
        mode = input("Choose mode (1: LLMAssistant, 2: LexicalValueGenerator, 3: CorpusManager, 'escape' to exit): ")

        if mode.lower() == 'escape':
            logger.info("User chose to exit the interactive test")
            break

        if mode == '1':
            user_question = input("Ask me a question (Press 'Escape' to exit): ")
            if user_question.lower() == 'escape':
                logger.info("User chose to exit the interactive test")
                break
            answer = oracle.ask_about_data(user_question)
            print("Answer:\n" + '\n'.join(answer), '\n', f"Answer contains {len(answer)}", "items" if len(answer) > 1 else "item")
            logger.info(f"Processed user question: {user_question[:50]}... Answer length: {len(answer)}")
        elif mode == '2':
            word = input("Enter a word to generate a lexical entry for: ")
            try:
                lexical_entry = lexical_generator.create_lexical_entry(word)
                print(f"Lexical entry for '{word}':")
                print(json.dumps(lexical_entry.__dict__, indent=2, ensure_ascii=False))
                logger.info(f"Generated lexical entry for word: {word}")
            except Exception as e:
                print(f"Error generating lexical entry: {str(e)}")
                logger.error(f"Error generating lexical entry for word '{word}': {str(e)}")
        elif mode == '3':
            corpus_action = input("Choose action (1: List texts, 2: Search texts, 3: Get all texts): ")
            if corpus_action == '1':
                texts = oracle.corpus_manager.list_texts()
                print("Available texts:", texts)
            elif corpus_action == '2':
                query = input("Enter search query: ")
                search_lemma = input("Search in lemmas? (y/n): ").lower() == 'y'
                results = oracle.corpus_manager.search_texts(query, search_lemma)
                print(f"Found {len(results)} results:")
                for result in results[:5]:  # Print first 5 results
                    print(f"Text: {result['text_id']}, Sentence: {result['sentence'][:50]}...")
            elif corpus_action == '3':
                all_texts = oracle.corpus_manager.get_all_texts()
                print(f"Total number of texts: {len(all_texts)}")
                for text_id, sentences in all_texts.items():
                    print(f"Text: {text_id}, Number of sentences: {len(sentences)}")
            else:
                print("Invalid action. Please choose 1, 2, or 3.")
        else:
            print("Invalid mode. Please choose 1, 2, or 3.")
    
    logger.info("Exiting the interactive test")

def demonstrate_lexical_value_generator(lexical_generator):
    logger = get_logger()
    logger.info("Demonstrating LexicalValueGenerator")
    sample_words = ["λόγος", "ἀρετή", "ψυχή"]
    for word in sample_words:
        try:
            lexical_entry = lexical_generator.create_lexical_entry(word)
            print(f"Lexical entry for '{word}':")
            print(json.dumps(lexical_entry.__dict__, indent=2, ensure_ascii=False))
            logger.info(f"Generated lexical entry for word: {word}")
        except Exception as e:
            print(f"Error generating lexical entry for '{word}': {str(e)}")
            logger.error(f"Error generating lexical entry for word '{word}': {str(e)}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the playground script with various options.")
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level')
    args = parser.parse_args()
    
    # Set up logging with the specified log level
    initialize_logger(log_level=args.log_level)
    
    logger = get_logger()
    logger.info("Starting the playground")

    # Initialize CorpusManager
    logger.info("Initializing CorpusManager")
    corpus_manager = CorpusManager()
    
    # Create LLMAssistant instance with CorpusManager
    logger.info("Creating LLMAssistant instance")
    oracle = LLMAssistant(corpus_manager)

    # Create LexicalValueGenerator instance
    logger.info("Creating LexicalValueGenerator instance")
    lexical_generator = LexicalValueGenerator(corpus_manager)

    # Demonstrate LexicalValueGenerator
    #demonstrate_lexical_value_generator(lexical_generator)

    # Run interactive test
    interactive_test(oracle, lexical_generator)

    logger.info("Playground execution completed")
