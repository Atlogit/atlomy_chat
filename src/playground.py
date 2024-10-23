import json
import re
import os
import argparse
from langchain_aws import ChatBedrock

from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

# Import TLGParser class for reference details conversion
from index_utils import TLGParser
# Import logger from logging_config
from logging_config import initialize_logger, get_logger
# Import CorpusManager for centralized text management
from corpus_manager import CorpusManager
# Import LexicalValueGenerator
from lexical_value_generator import LexicalValueGenerator, LexicalValueGeneratorError
# Import LexicalValue
from lexical_value import LexicalValue

# Initialize logger at module level
initialize_logger()
logger = get_logger()

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

    def __init__(self, corpus_manager, model_id="anthropic.claude-3-5-sonnet-20240620-v1:0", temperature=0.5):
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
            lexical_value_test(lexical_generator)
        elif mode == '3':
            corpus_manager_test(oracle.corpus_manager)
        else:
            print("Invalid mode. Please choose 1, 2, or 3.")
    
    logger.info("Exiting the interactive test")

def lexical_value_test(lexical_generator):
    while True:
        action = input("Choose action (1: Create, 2: Get, 3: List, 4: Update, 5: Delete, 'back' to return): ")
        if action.lower() == 'back':
            break

        try:
            if action == '1':
                word = input("Enter a word to generate a lexical entry for: ")
                search_lemma = input("Search by lemma? (y/n): ").lower() == 'y'
                lexical_entry = lexical_generator.create_lexical_entry(word, search_lemma=search_lemma)
                print(f"Lexical entry for '{word}' (search_lemma={search_lemma}):")
                print(json.dumps(lexical_entry.__dict__, indent=2, ensure_ascii=False))
                logger.info(f"Generated lexical entry for word: {word}, search_lemma={search_lemma}")
            elif action == '2':
                lemma = input("Enter a lemma to retrieve: ")
                lexical_value = lexical_generator.get_lexical_value(lemma)
                if lexical_value:
                    print(f"Lexical value for '{lemma}':")
                    print(json.dumps(lexical_value.__dict__, indent=2, ensure_ascii=False))
                else:
                    print(f"No lexical value found for '{lemma}'")
                logger.info(f"Retrieved lexical value for lemma: {lemma}")
            elif action == '3':
                values = lexical_generator.list_lexical_values()
                print("Available lexical values:", values)
                logger.info(f"Listed {len(values)} lexical values")
            elif action == '4':
                lemma = input("Enter the lemma of the lexical value to update: ")
                lexical_value = lexical_generator.get_lexical_value(lemma)
                if lexical_value:
                    print(f"Current lexical value for '{lemma}':")
                    print(json.dumps(lexical_value.__dict__, indent=2, ensure_ascii=False))
                    new_translation = input("Enter new translation (or press Enter to keep current): ")
                    if new_translation:
                        lexical_value.translation = new_translation
                    lexical_generator.update_lexical_value(lexical_value)
                    print(f"Updated lexical value for '{lemma}'")
                else:
                    print(f"No lexical value found for '{lemma}'")
                logger.info(f"Updated lexical value for lemma: {lemma}")
            elif action == '5':
                lemma = input("Enter the lemma of the lexical value to delete: ")
                result = lexical_generator.delete_lexical_value(lemma)
                if result:
                    print(f"Deleted lexical value for '{lemma}'")
                else:
                    print(f"No lexical value found for '{lemma}' or deletion failed")
                logger.info(f"Attempted to delete lexical value for lemma: {lemma}")
            else:
                print("Invalid action. Please choose 1, 2, 3, 4, or 5.")
        except LexicalValueGeneratorError as e:
            print(f"Error: {str(e)}")
            logger.error(f"LexicalValueGeneratorError: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            logger.error(f"Unexpected error in lexical_value_test: {str(e)}")

def corpus_manager_test(corpus_manager):
    while True:
        action = input("Choose action (1: List texts, 2: Search texts, 3: Get all texts, 'back' to return): ")
        if action.lower() == 'back':
            break

        try:
            if action == '1':
                texts = corpus_manager.list_texts()
                print("Available texts:", texts)
                logger.info(f"Listed {len(texts)} texts")
            elif action == '2':
                query = input("Enter search query: ")
                search_lemma = input("Search in lemmas? (y/n): ").lower() == 'y'
                results = corpus_manager.search_texts(query, search_lemma)
                print(f"Found {len(results)} results:")
                for result in results[:5]:  # Print first 5 results
                    print(f"Text: {result['text_id']}, Sentence: {result['sentence'][:50]}...")
                logger.info(f"Searched texts with query '{query}', found {len(results)} results")
            elif action == '3':
                all_texts = corpus_manager.get_all_texts()
                print(f"Total number of texts: {len(all_texts)}")
                for text_id, sentences in all_texts.items():
                    print(f"Text: {text_id}, Number of sentences: {len(sentences)}")
                logger.info(f"Retrieved all texts, total: {len(all_texts)}")
            else:
                print("Invalid action. Please choose 1, 2, or 3.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            logger.error(f"Error in corpus_manager_test: {str(e)}")

def comprehensive_lexical_value_test(lexical_generator):
    logger.info("Starting comprehensive LexicalValueGenerator test")
    
    try:
        # Test create_lexical_entry
        word = "φλέψ"
        logger.info(f"Testing create_lexical_entry with word: {word}")
        lexical_entry = lexical_generator.create_lexical_entry(word)
        print(f"Created lexical entry for '{word}':")
        print(json.dumps(lexical_entry.__dict__, indent=2, ensure_ascii=False))

        # Test get_lexical_value
        logger.info(f"Testing get_lexical_value with lemma: {word}")
        retrieved_entry = lexical_generator.get_lexical_value(word)
        print(f"Retrieved lexical entry for '{word}':")
        print(json.dumps(retrieved_entry.__dict__, indent=2, ensure_ascii=False))

        # Test list_lexical_values
        logger.info("Testing list_lexical_values")
        values = lexical_generator.list_lexical_values()
        print("Available lexical values:", values)

        # Test update_lexical_value
        logger.info(f"Testing update_lexical_value for lemma: {word}")
        lexical_entry.translation = "Updated translation for test"
        lexical_generator.update_lexical_value(lexical_entry)
        updated_entry = lexical_generator.get_lexical_value(word)
        print(f"Updated lexical entry for '{word}':")
        print(json.dumps(updated_entry.__dict__, indent=2, ensure_ascii=False))

        # Test delete_lexical_value
        logger.info(f"Testing delete_lexical_value for lemma: {word}")
        result = lexical_generator.delete_lexical_value(word)
        print(f"Deleted lexical value for '{word}': {result}")

        logger.info("Comprehensive LexicalValueGenerator test completed successfully")
    except LexicalValueGeneratorError as e:
        print(f"LexicalValueGeneratorError: {str(e)}")
        logger.error(f"LexicalValueGeneratorError in comprehensive test: {str(e)}")
    except Exception as e:
        logger.error(f"Error in test_phleps_search: {str(e)}")

def test_phleps_search(corpus_manager):
    logger = get_logger()
    logger.info("Starting test for searching 'φλέψ'")
    
    try:
        # Test CorpusManager search
        results = corpus_manager.search_texts("φλέψ")
        logger.info(f"CorpusManager: Found {len(results)} results for 'φλέψ'")
        
        for i, result in enumerate(results[:5], 1):  # Print first 5 results
            logger.info(f"Result {i}:")
            logger.info(f"Text ID: {result['text_id']}")
            logger.info(f"Sentence: {result['sentence'][:100]}...")  # Print first 100 characters of the sentence
        
        lemma_results = corpus_manager.search_texts("φλέψ", search_lemma=True)
        logger.info(f"CorpusManager: Found {len(lemma_results)} results for 'φλέψ' when searching lemmas")
        
        for i, result in enumerate(lemma_results[:5], 1):  # Print first 5 results
            logger.info(f"Lemma Result {i}:")
            logger.info(f"Text ID: {result['text_id']}")
            logger.info(f"Sentence: {result['sentence'][:100]}...")  # Print first 100 characters of the sentence

        # Test LexicalValueGenerator
        lexical_generator = LexicalValueGenerator(corpus_manager)
        
        # Test word search
        word_entry = lexical_generator.create_lexical_entry("φλέψ", search_lemma=False)
        logger.info("LexicalValueGenerator: Created entry for 'φλέψ' (word search)")
        logger.info(json.dumps(word_entry.__dict__, indent=2, ensure_ascii=False))

        # Test lemma search
        lemma_entry = lexical_generator.create_lexical_entry("φλέψ", search_lemma=True)
        logger.info("LexicalValueGenerator: Created entry for 'φλέψ' (lemma search)")
        logger.info(json.dumps(lemma_entry.__dict__, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"Error in test_phleps_search: {str(e)}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the playground script with various options.")
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level')
    parser.add_argument('--test-mode', choices=['interactive', 'comprehensive', 'phleps'], default='interactive', help='Choose test mode')
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

    if args.test_mode == 'comprehensive':
        comprehensive_lexical_value_test(lexical_generator)
    elif args.test_mode == 'phleps':
        test_phleps_search(corpus_manager)
    else:
        interactive_test(oracle, lexical_generator)

    logger.info("Playground execution completed")