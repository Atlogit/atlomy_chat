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

def clean_line(line, citation_config):
    """
    Removes line details and returns them separately based on patterns in the citation config.
    """
    for pattern in citation_config['citation_patterns']:
        regex = re.compile(pattern['pattern'])
        #print("regex:", regex)
        match = regex.match(line)
        #print("match:", match)
        if match:
            # Return the remaining line and the matched citation details
            remaining_line = line[match.end():].strip()
            #print("remaining_line:", remaining_line)
            # Extract the citation details from the matched pattern
            citation_details = match.group(0)
            #print("citation_details:", citation_details)
            return remaining_line, citation_details
    # Return the line as is if no pattern matches
    return line, None

def merge_lines(lines, citation_config):
    """
    Merges lines while handling split words and preserving line references.
    Returns a list of sentences with associated citation and line number data.
    """
    merged_sentences = []
    current_sentence = ""
    current_line_numbers = []  # Tracks line numbers for the current sentence
    sentence_in_progress = False  # To track whether we are in a sentence that spans lines

    for line in lines:
        # Clean the line and extract line number details
        cleaned_line, line_number = clean_line(line, citation_config)

        # Handle split words
        if current_sentence.endswith('-'):
            current_sentence = current_sentence.rstrip('-') + cleaned_line.lstrip()
        else:
            current_sentence += " " + cleaned_line
        get_parser_logger().debug(f"Current sentence: {current_sentence}")
        current_sentence = current_sentence.strip()
        
        # Accumulate line numbers
        if line_number and (not current_line_numbers or line_number != current_line_numbers[-1]):
            current_line_numbers.append(line_number)
            get_parser_logger().debug(f"Current line numbersas long as sentence is incomplete: {current_line_numbers}")
        else:
            get_parser_logger().debug(f"Line number not added: {line_number}. Must be the sentence end")
        # Check if the sentence ends (e.g., ".","·")
        if re.search(r'[.·](?:\s|$)', cleaned_line):
            # We encountered a sentence-ending punctuation mark
            
            # Split the sentence based on delimiters and process it
            sentences = re.split(r'([.·](?:\s|$))', current_sentence)
            
            for i in range(0, len(sentences) - 1, 2):
                sentence = (sentences[i] + sentences[i + 1]).strip()
                get_parser_logger().debug(f"Sentence after split: {sentence}")
                if sentence:
                    # Save the sentence along with its line numbers
                    merged_sentences.append((sentence, list(current_line_numbers)))

            # Handle remaining part after last delimiter
            current_sentence = sentences[-1].strip() if len(sentences) % 2 == 1 else ""
            get_parser_logger().debug(f"Current sentence remaining part after last delimiter: {current_sentence}")
            get_parser_logger().debug(f"Current line numbers after processing the full sentence: {current_line_numbers}")
            # Reset line numbers and sentence tracking after processing the full sentence
            if not current_sentence:
                current_line_numbers = []  # Reset line numbers after full sentence
                sentence_in_progress = False
                get_parser_logger().debug(f"Sentence in progress after processing the full sentence if not current sentence: {sentence_in_progress}")
                get_parser_logger().debug(f"Current line numbers after processing the full sentence and resetting the line numbers if not current sentence: {current_line_numbers}")
            else:
                current_line_numbers = [current_line_numbers[-1]] if current_line_numbers else []
                sentence_in_progress = True
                get_parser_logger().debug(f"Sentence in progress after processing the full sentence if current sentence: {sentence_in_progress}")
                get_parser_logger().debug(f"Current line numbers after processing the full sentence and resetting the line numbers if current sentence: {current_line_numbers}")

        else:
            # If we haven't encountered a sentence-ending punctuation mark, the sentence continues
            get_parser_logger().debug(f"Current sentence if no sentence-ending punctuation mark: {current_sentence}")
            sentence_in_progress = True
            get_parser_logger().debug(f"Sentence in progress if no sentence-ending punctuation mark: {sentence_in_progress}")
            get_parser_logger().debug(f"current_line_numbers if no sentence-ending punctuation mark:", current_line_numbers)
            
    # Add any remaining sentence after the loop
    if current_sentence.strip():
        merged_sentences.append((current_sentence.strip(), list(current_line_numbers)))
        get_parser_logger().debug(f"current_line_numbers after adding remaining sentence after the loop:", current_line_numbers)
    get_parser_logger().debug(f"merged_sentences after adding remaining sentence after the loop:", merged_sentences)
    return merged_sentences

@log_exceptions
def apply_citation_patterns(citations, citation_config):
    """
    Applies the citation patterns to the collected citations and formats them.
    
    Args:
        citations (list): A list of line number strings.
        citation_config (dict): The citation pattern configuration.
    
    Returns:
        str: A formatted citation string.
    """
    formatted_citations = []
    for citation in citations:
        formatted_citation = citation  # Default to the raw citation if no pattern matches
        
        # Apply each pattern from the citation config
        for pattern in citation_config['citation_patterns']:
            regex = re.compile(pattern['pattern'])
            match = regex.match(citation)
            if match:
                groups = match.groups()
                group_dict = {name: value for name, value in zip(pattern['groups'], groups) if value}
                
                # Dynamically format the citation based on the matched groups
                parts = []
                for key in pattern['groups']:
                    if key in group_dict:
                        parts.append(f"{key.capitalize()} {group_dict[key]}")
                formatted_citation = ', '.join(parts) + ': '  # Add colon after reference details
                break  # Stop after the first match
        formatted_citations.append(formatted_citation)
    return ', '.join(formatted_citations)  # Combine multiple citations with commas

@log_exceptions
def split_text_into_sections(tlgu_text, citation_config):
    """
    Split the TLG text into sections, merge lines, and apply citation patterns.
    
    Args:
        tlgu_text (str): The input TLG text.
        citation_config (dict): Configuration for formatting citation data.
    
    Returns:
        list: A list of tuples containing (formatted citation, text) pairs.
    """
    pattern = r'(\[\w*\] +\[\w*\] +\[\w*\] +\[\w*\])'
    sections = re.split(pattern, tlgu_text)
    if len(sections) < 2:
        raise TLGParsingError("No sections found in the text")
    grouped_sections = []
    for i in range(1, len(sections), 2):
        citation = sections[i].strip()
        text = sections[i+1].strip() if i+1 < len(sections) else ""
        #print ("citation:", citation, "text: ", text)
        # Split the text into lines and merge them into full sentences
        lines = text.splitlines()
        merged_sentences = merge_lines(lines, citation_config)
        processed_sentences = []
        # Apply citation patterns to format the line metadata
        for sentence, line_numbers in merged_sentences:
            formatted_citation = apply_citation_patterns(line_numbers, citation_config)
            processed_sentence = f"<tlg_ref>{citation}, {formatted_citation}</tlg_ref>{sentence}"
            processed_sentences.append(processed_sentence)
        # Join processed sentences and add to grouped_sections
        processed_text = " ".join(processed_sentences)
        grouped_sections.append((citation, processed_text))

    return grouped_sections

@log_exceptions
def process_text_sections(sections, citation_config):
    """Process the text sections by applying citation patterns."""
    final = []
    
    for citation, processed_text in sections:
        final.append(processed_text)
        
    
    return " ".join(final)

@log_exceptions
def process_tlg_file(file_path, nlp, citation_config):
    """Process a TLG file through various stages of cleaning and tagging."""
    get_parser_logger().info(f"Processing TLG file: {file_path}")
    tlgu_text = read_file_with_fallback(file_path)
    get_parser_logger().debug(f"File read successfully: {file_path}")
    
    sections = split_text_into_sections(tlgu_text, citation_config)
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
