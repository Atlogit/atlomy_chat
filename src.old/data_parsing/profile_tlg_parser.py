import cProfile
import pstats
import io
from tlg_parser import process_tlg_file, spaCy_Model, TLGParsingError
from utils import UtilityError
import spacy
import os
import argparse
import sys
from logging_config import get_logger, setup_logging

logger = get_logger()

def profile_function(func, *args, **kwargs):
    pr = cProfile.Profile()
    pr.enable()

    try:
        result = func(*args, **kwargs)
    except (TLGParsingError, UtilityError) as e:
        logger.error(f"An error occurred while processing: {str(e)}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {str(e)}")
        return None

    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Print top 20 time-consuming functions
    
    return result, s.getvalue()

def profile_process_tlg_file(file_path, nlp):
    logger.info(f"Profiling process_tlg_file for: {file_path}")
    result, profile_output = profile_function(process_tlg_file, file_path, nlp)
    
    if result is not None:
        logger.info("File processed successfully")
        logger.info("Profiling results:")
        print(profile_output)
    else:
        logger.error("Failed to process the file")

def profile_specific_function(func_name, file_path, nlp):
    logger.info(f"Profiling {func_name} for: {file_path}")
    
    # Import the function dynamically
    try:
        module = __import__('tlg_parser')
        func = getattr(module, func_name)
    except AttributeError:
        logger.error(f"Function {func_name} not found in tlg_parser module")
        return

    # For simplicity, we'll read the file content here
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        logger.error(f"Failed to read file: {str(e)}")
        return

    result, profile_output = profile_function(func, content, nlp)
    
    if result is not None:
        logger.info(f"{func_name} executed successfully")
        logger.info("Profiling results:")
        print(profile_output)
    else:
        logger.error(f"Failed to execute {func_name}")

if __name__ == "__main__":
    # Set up logging
    setup_logging()

    # Default file path using absolute path
    default_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                     'assets', 'texts', 'original', 'TLG', 'TLG0057_galen-021.txt')

    parser = argparse.ArgumentParser(description="Profile the TLG parser with a specified file.")
    parser.add_argument('--file_path', default=default_file_path, help='Path to the TLG file for profiling')
    parser.add_argument('--function', help='Specific function to profile (optional)')
    args = parser.parse_args()

    if os.path.exists(args.file_path):
        logger.info(f"Starting profiling for file: {args.file_path}")
        
        # Load spaCy model
        logger.info("Loading spaCy model...")
        nlp = spacy.load(spaCy_Model)
        nlp.get_pipe("spancat").cfg["threshold"] = 0.2
        
        if args.function:
            profile_specific_function(args.function, args.file_path, nlp)
        else:
            profile_process_tlg_file(args.file_path, nlp)
    else:
        logger.error(f"File not found: {args.file_path}")
        logger.error("Please provide a valid TLG file path for profiling.")
        sys.exit(1)
