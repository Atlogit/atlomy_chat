import re
import json
import spacy
import os
import sys
from functools import wraps
from tqdm import tqdm
from ..logging_config import get_logger, setup_logging
from src.corpus_manager import CorpusManager
from .utils import (
    log_exceptions, sentencizer, clean_text, read_file_with_fallback,
    create_text_tagging_object
)

def get_parser_logger():
    return get_logger()

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
spaCy_Model = os.path.join(project_root, "assets", "models", "atlomy_full_pipeline_annotation_131024", "model-best")

class TLGParsingError(Exception):
    """Custom exception for TLG parsing errors."""
    pass

@log_exceptions
def load_citation_config(config_path):
    """Load citation configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

class DefaultDict(dict):
    """Dictionary that returns a default value for missing keys."""
    def __missing__(self, key):
        return f''
    
@log_exceptions
def apply_citation_patterns(text, citation_config):
    """Apply citation patterns from the configuration to the text."""
    for pattern in citation_config['citation_patterns']:
        regex = re.compile(pattern['pattern'])
        def replace(match):
            groups = match.groups()
            group_dict = {name: value for name, value in zip(pattern['groups'], groups) if value}
            # Dynamically construct the output string based on non-empty groups
            parts = []
            for key in pattern['groups']:
                if key in group_dict:
                    parts.append(f"{key.capitalize()} {group_dict[key]}")
            return ', '.join(parts) + ': '  # Add colon after reference details
        text = regex.sub(replace, text)
    return text

@log_exceptions
def split_text_into_sections(tlgu_text):
    """
    Split the TLG text into sections based on a specific pattern.

    Args:
        tlgu_text (str): The input TLG text.

    Returns:
        list: A list of tuples containing (citation, text) pairs.

    Raises:
        TLGParsingError: If no sections are found in the text.
    """
    pattern = r'(\[\w*\] +\[\w*\] +\[\w*\] +\[\w*\])'
    sections = re.split(pattern, tlgu_text)
    if len(sections) < 2:
        raise TLGParsingError("No sections found in the text")
    
    # Group citations with their corresponding text
    grouped_sections = []
    for i in range(1, len(sections), 2):
        citation = sections[i].strip()
        text = sections[i+1].strip() if i+1 < len(sections) else ""
        grouped_sections.append((citation, text))
    
    return grouped_sections

@log_exceptions
def process_text_sections(sections, citation_config):
    """Process the text sections by applying citation patterns."""
    final = []
    
    for citation, text in sections:
        processed_text = apply_citation_patterns(text, citation_config)
        lines = processed_text.split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        
        for line in lines:
            # Split the line into reference details and main text using the colon
            parts = line.split(":", 1)
            if len(parts) > 1:
                ref_details, main_text = parts
                processed_line = f"<tlg_ref>{citation}, {ref_details.strip()}</tlg_ref>{main_text.strip()}"
            else:
                processed_line = f"<tlg_ref>{citation}</tlg_ref>{line}"
            final.append(processed_line)
    
    return " ".join(final)

@log_exceptions
def process_tlg_file(file_path, nlp, citation_config):
    """Process a TLG file through various stages of cleaning and tagging."""
    get_parser_logger().info(f"Processing TLG file: {file_path}")
    tlgu_text = read_file_with_fallback(file_path)
    get_parser_logger().debug(f"File read successfully: {file_path}")
    
    sections = split_text_into_sections(tlgu_text)
    get_parser_logger().debug(f"Text split into {len(sections)} sections")
    
    processed_text = process_text_sections(sections, citation_config)
    get_parser_logger().debug("Text sections processed")

    cleaned_text = clean_text(processed_text)
    get_parser_logger().debug("Text cleaned")
    
    sentences = sentencizer(cleaned_text)
    get_parser_logger().debug(f"Text split into {len(sentences)} sentences")
    
    tagged_object = create_text_tagging_object(sentences, nlp)
    get_parser_logger().info(f"TLG file processed successfully: {file_path}")
    return tagged_object

@log_exceptions
def create_data(input_path, corpus_manager, nlp, citation_config, skip_existing=False):
    """Create data by processing TLG files and adding them to the corpus."""
    if os.path.isfile(input_path):
        text_id = os.path.splitext(os.path.basename(input_path))[0]
        if skip_existing and corpus_manager.text_exists(text_id):
            get_parser_logger().info(f"Skipping {input_path} as it already exists in the corpus.")
        else:
            get_parser_logger().info(f"Processing file: {input_path}")
            tagged_data = process_tlg_file(input_path, nlp, citation_config)
            corpus_manager.add_text(text_id, tagged_data)
    elif os.path.isdir(input_path):
        tlg_files = [f for f in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, f)) and f.startswith("TLG")]
        for file_name in tqdm(tlg_files, desc="Processing TLG files"):
            file_path = os.path.join(input_path, file_name)
            text_id = os.path.splitext(file_name)[0]
            if skip_existing and corpus_manager.text_exists(text_id):
                get_parser_logger().info(f"Skipping {file_name} as it already exists in the corpus.")
            else:
                get_parser_logger().info(f"Processing file: {file_name}")
                try:
                    tagged_data = process_tlg_file(file_path, nlp, citation_config)
                    corpus_manager.add_text(text_id, tagged_data)
                except TLGParsingError as e:
                    get_parser_logger().error(f"Error processing {file_name}: {str(e)}")
                except Exception as e:
                    get_parser_logger().exception(f"Unexpected error processing {file_name}: {str(e)}")
    else:
        raise ValueError(f"Invalid input path: {input_path}")

if __name__ == "__main__":
    from ..logging_config import initialize_logger
    import argparse

    initialize_logger()
    logger = get_parser_logger()
    
    try:
        nlp = spacy.load(spaCy_Model)
        nlp.get_pipe("spancat").cfg["threshold"] = 0.2
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        corpus_path = os.path.join(project_root, 'assets', 'texts', 'annotated')
        config_path = os.path.join(script_dir, 'citation_config.json')
        
        parser = argparse.ArgumentParser(description="Process TLG text files and add them to the corpus.")
        parser.add_argument('--input_path', help='Path to input file or directory')
        parser.add_argument('--corpus_path', default=corpus_path, help='Path to corpus directory')
        parser.add_argument('--config_path', default=config_path, help='Path to citation configuration file')
        parser.add_argument('--skip-existing', action='store_true', help='Skip processing files that already exist in the corpus.')
        parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level')
        args = parser.parse_args()
        
        setup_logging(log_level=args.log_level)
        
        logger.info(f"Starting TLG parsing process with input path: {args.input_path}")
        corpus_manager = CorpusManager(args.corpus_path)
        citation_config = load_citation_config(args.config_path)
        
        create_data(args.input_path, corpus_manager, nlp, citation_config, skip_existing=args.skip_existing)
        corpus_manager.save_texts()
        logger.info("TLG parsing process completed successfully")
    except Exception as e:
        logger.exception(f"An error occurred during script execution: {str(e)}")
        sys.exit(1)
