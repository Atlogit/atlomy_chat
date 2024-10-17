import re
import json
import spacy
import spacy_transformers
import os
import sys
from functools import wraps
from tqdm import tqdm

# Use relative imports for local modules
from ..corpus_manager import CorpusManager
from ..logging_config import get_logger, setup_logging
from .utils import (
    log_exceptions, sentencizer, clean_text, read_file_with_fallback,
    create_text_tagging_object
)

# Get the logger
logger = get_logger()

# Use an absolute path or a path relative to the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
spaCy_Model = os.path.join(project_root, "assets", "models", "atlomy_full_pipeline_annotation_131024", "model-best")

class TLGParsingError(Exception):
    """Custom exception for TLG parsing errors."""
    pass

@log_exceptions
def remove_tlg_ref_tags(text):
    """
    Remove <tlg_ref>...</tlg_ref> tags from the given text.

    Args:
        text (str): The input text containing TLG reference tags.

    Returns:
        str: The text with TLG reference tags removed.
    """
    pattern = re.compile(r'<tlg_ref>.*?</tlg_ref>', re.DOTALL)
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

@log_exceptions
def fix_words_that_carry_over_next_line(text):
    """
    Fix words that are split across lines due to TLG reference tags.

    Args:
        text (str): The input text with potentially split words.

    Returns:
        str: The text with split words fixed.
    """
    pattern = r'(\S+)-\s*<tlg_ref>.*?</tlg_ref>\s*(\w+)'
    
    def replace_function(match):
        return match.group(1) + match.group(2) + match.group(0)[len(match.group(1)) + 1:-len(match.group(2))]
    
    text = re.sub(pattern, replace_function, text)
    return text

@log_exceptions
def replace_citation_levels(text):
    """
    Replace citation levels with specified prefixes.

    Args:
        text (str): The input text containing citation levels.

    Returns:
        str: The text with citation levels replaced by prefixes.
    """
    pattern = r'(\.?\d*[a-zA-Z\d]*)(\.(\d*[a-zA-Z\d]*))?(\.(\d*[a-zA-Z\d]*))?'

    def replacement(match):
        parts = match.groups()
        citation = []
        
        if parts[0] and (parts[0].strip('.').isalnum() or parts[0].strip('.').isalpha()):
            citation.append(f"VOL({parts[0]})")
        if parts[2] and (parts[2].isalnum() or parts[2].isalpha()):
            citation.append(f"VB({parts[2]})")
        if parts[4] and (parts[4].isalnum() or parts[4].isalpha()):
            citation.append(f"L({parts[4]})")
        while len(citation) < 3:
            citation.insert(0, None)
            
        if citation:
            return "*".join(filter(None, citation))
    
    return re.sub(pattern, replacement, text)

@log_exceptions
def split_text_into_sections(tlgu_text):
    """
    Split the TLG text into sections based on a specific pattern.

    Args:
        tlgu_text (str): The input TLG text.

    Returns:
        list: A list of text sections.

    Raises:
        TLGParsingError: If no sections are found in the text.
    """
    pattern = r'(\[\w*\] +\[\w*\] +\[\w*\] +\[\w*\])'
    result = re.split(pattern, tlgu_text)
    sections = [item.strip() for item in result if item.strip()]
    if not sections:
        raise TLGParsingError("No sections found in the text")
    return sections

@log_exceptions
def process_text_sections(sections):
    """
    Process the text sections by applying various transformations.

    Args:
        sections (list): A list of text sections.

    Returns:
        str: The processed text.

    Raises:
        TLGParsingError: If there's an uneven number of sections.
    """
    if len(sections) % 2 != 0:
        raise TLGParsingError("Uneven number of sections found")
    
    prefixes = sections[0::2]
    texts = sections[1::2]
    final = []
    for prefix, text in zip(prefixes, texts):
        lines = text.split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        lines = [replace_citation_levels(line[:line.find('\t')]) + line[line.find('\t'):] if '\t' in line else replace_citation_levels(line) for line in lines]
        lines = ["<tlg_ref>" + prefix + " " + line for line in lines]
        lines = [line.replace("\t", "</tlg_ref>") for line in lines]
        final += lines
    return " ".join(final)

@log_exceptions
def process_tlg_file(file_path, nlp):
    """
    Process a TLG file through various stages of cleaning and tagging.

    Args:
        file_path (str): Path to the TLG file.
        nlp: The spaCy NLP model.

    Returns:
        dict: A tagged object representing the processed TLG file.
    """
    logger.info(f"Processing TLG file: {file_path}")
    tlgu_text = read_file_with_fallback(file_path)
    logger.debug(f"File read successfully: {file_path}")
    
    sections = split_text_into_sections(tlgu_text)
    logger.debug(f"Text split into {len(sections)} sections")
    
    processed_text = process_text_sections(sections)
    logger.debug("Text sections processed")
    
    cleaned_text = clean_text(processed_text)
    logger.debug("Text cleaned")
    
    fixed_text = fix_words_that_carry_over_next_line(cleaned_text)
    logger.debug("Words carrying over next line fixed")
    
    sentences = sentencizer(fixed_text)
    logger.debug(f"Text split into {len(sentences)} sentences")
    
    tagged_object = create_text_tagging_object(sentences, nlp)
    logger.info(f"TLG file processed successfully: {file_path}")
    return tagged_object

@log_exceptions
def create_data(input_path, corpus_manager, nlp, skip_existing=False):
    """
    Create data by processing TLG files and adding them to the corpus.

    Args:
        input_path (str): Path to the input file or directory.
        corpus_manager (CorpusManager): The corpus manager object.
        nlp: The spaCy NLP model.
        skip_existing (bool): Whether to skip existing files in the corpus.
    """
    if os.path.isfile(input_path):
        text_id = os.path.splitext(os.path.basename(input_path))[0]
        if skip_existing and corpus_manager.text_exists(text_id):
            logger.info(f"Skipping {input_path} as it already exists in the corpus.")
        else:
            logger.info(f"Processing file: {input_path}")
            tagged_data = process_tlg_file(input_path, nlp)
            corpus_manager.add_text(text_id, tagged_data)
    elif os.path.isdir(input_path):
        tlg_files = [f for f in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, f)) and f.startswith("TLG")]
        for file_name in tqdm(tlg_files, desc="Processing TLG files"):
            file_path = os.path.join(input_path, file_name)
            text_id = os.path.splitext(file_name)[0]
            if skip_existing and corpus_manager.text_exists(text_id):
                logger.info(f"Skipping {file_name} as it already exists in the corpus.")
            else:
                logger.info(f"Processing file: {file_name}")
                try:
                    tagged_data = process_tlg_file(file_path, nlp)
                    corpus_manager.add_text(text_id, tagged_data)
                except TLGParsingError as e:
                    logger.error(f"Error processing {file_name}: {str(e)}")
                except Exception as e:
                    logger.exception(f"Unexpected error processing {file_name}: {str(e)}")
    else:
        raise ValueError(f"Invalid input path: {input_path}")

if __name__ == "__main__":
    try:
        nlp = spacy.load(spaCy_Model)
        # Set the threshold for the spancat component
        nlp.get_pipe("spancat").cfg["threshold"] = 0.2
        import os
        import argparse
        # Get the script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the project root path
        project_root = os.path.dirname(os.path.dirname(script_dir))
        # Construct the corpus path
        corpus_path = os.path.join(project_root, 'assets', 'texts', 'annotated')
        
        parser = argparse.ArgumentParser(description="Process TLG text files and add them to the corpus.")
        parser.add_argument('--input_path', help='Path to input file or directory')
        parser.add_argument('--corpus_path', default=corpus_path, help='Path to corpus directory')
        parser.add_argument('--skip-existing', action='store_true', help='Skip processing files that already exist in the corpus.')
        parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level')
        args = parser.parse_args()
        
        # Set up logging with the specified log level
        setup_logging(log_level=args.log_level)
        
        logger.info(f"Starting TLG parsing process with input path: {args.input_path}")
        corpus_manager = CorpusManager(args.corpus_path)
        create_data(args.input_path, corpus_manager, nlp, skip_existing=args.skip_existing)
        corpus_manager.save_texts()
        logger.info("TLG parsing process completed successfully")
    except Exception as e:
        logger.exception(f"An error occurred during script execution: {str(e)}")
        sys.exit(1)
