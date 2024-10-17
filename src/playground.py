import json
import re
import os
from langchain_aws import ChatBedrock
from pprint import pprint

from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

# Import TLGParser class for reference details conversion
from index_utils import TLGParser
# Import CorpusManager for centralized text management
from corpus_manager import CorpusManager
# Import logger from logging_config
from logging_config import logger
# Import LexicalValueGenerator
from lexical_value_generator import LexicalValueGenerator

class LLMAssistant:
    # Data query template remains unchanged
    data_query_template = """
    You are an AI assistant that generates Python code based on specific instructions. You are working with a CorpusManager object named "corpus_manager" with the following methods:
    - get_text(text_id): Returns a list of dictionaries representing sentences for the given text_id.
    - get_all_texts(): Returns a dictionary where keys are text_ids and values are lists of sentence dictionaries.
    - search_texts(query): Returns a list of sentences matching the given query.

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
        match = re.search(pattern, input_string, re.DOTALL)
        if match:
            logger.debug("Successfully extracted Python code from LLM response")
            return match.group(1).strip()
        else:
            logger.warning("No valid Python code found in LLM response")
            return None

    def ask_about_data(self, data_query):
        # Use an absolute path or a path relative to the script's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        authors_path = os.path.join(project_root, "assets", "indexes", "tlg_index.py")
        works_path = os.path.join(project_root, "assets", "indexes", "work_numbers.py")
        
        handler = TLGParser(authors_path, works_path)
        logger.info(f"Initialized TLGParser with authors_path: {authors_path} and works_path: {works_path}")

        attempts = 0

        while attempts < 3:
            try:
                logger.info(f"Attempt {attempts + 1} to process data query")
                answer = self.query_llm(data_query)
                code_from_answer = self._extract_code(answer)
                if code_from_answer is None:
                    raise ValueError("No valid Python code found in the response")
                
                vars_dict = {"result": None, "corpus_manager": self.corpus_manager}
                self.the_universal_function(code_from_answer, vars_dict)
                
                if vars_dict['result'] is None:
                    raise ValueError("The 'result' variable was not set by the generated code")
                
                result = handler.process_texts(vars_dict['result'])
                logger.info("Successfully processed data query")
                return result

            except Exception as e:
                attempts += 1
                logger.error(f"Attempt {attempts} failed with error: {str(e)}")

        logger.error("All attempts failed. Handle the failure accordingly.")
        return None

def interactive_test(oracle, lexical_generator):
    logger.info("Starting interactive test")
    while True:
        mode = input("Choose mode (1: LLMAssistant, 2: LexicalValueGenerator, 'escape' to exit): ")

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
        else:
            print("Invalid mode. Please choose 1 or 2.")
    
    logger.info("Exiting the interactive test")

def demonstrate_lexical_value_generator(lexical_generator):
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
    logger.info("Starting the playground")

    # Initialize CorpusManager
    corpus_manager = CorpusManager()
    
    # Create LLMAssistant instance with CorpusManager
    oracle = LLMAssistant(corpus_manager)

    # Create LexicalValueGenerator instance
    lexical_generator = LexicalValueGenerator(corpus_manager)

    # Demonstrate LexicalValueGenerator
    demonstrate_lexical_value_generator(lexical_generator)

    # Run interactive test
    interactive_test(oracle, lexical_generator)

    logger.info("Playground execution completed")
