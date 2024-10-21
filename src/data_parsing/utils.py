import re
from functools import wraps
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

class UtilityError(Exception):
    """Custom exception for utility-related errors."""
    pass

def log_exceptions(func):
    """
    Decorator to log exceptions raised by the decorated function.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {str(e)}")
            raise
    return wrapper

@log_exceptions
def sentencizer(text):
    """
    Split the input text into sentences.

    Args:
        text (str): The input text to be split into sentences.

    Returns:
        list: A list of sentences.
    """
    logger.debug("Starting sentence splitting")
    delimiters_pattern = r'[.|·]'
    sentences = re.split(delimiters_pattern, text)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    #print("sentences stripeddd:", sentences)
    logger.debug(f"Split text into {len(sentences)} sentences")
    return sentences

@log_exceptions
def clean_text(text):
    """
    Clean the input text by removing unwanted characters and normalizing apostrophes.

    Args:
        text (str): The input text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    logger.debug("Starting text cleaning")
    print("text:", text)
    text = text.replace("{", "").replace("}", "")
    apostrophes = [' ̓', "᾿", "᾽", "'", "'", "'"]  # all possible apostrophes
    for apostrophe in apostrophes:
        text = text.replace(apostrophe, "ʼ")
    clean = ' '.join(text.replace('-\n', '').replace('\r', ' ').replace('\n', ' ').split())
    logger.debug("Text cleaning completed")
    print("clean:", clean)
    return clean

@log_exceptions
def read_file_with_fallback(file_path):
    """
    Read a file with UTF-8 encoding, falling back to latin-1 if UTF-8 fails.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The content of the file.

    Raises:
        UtilityError: If the file cannot be read with either encoding.
    """
    logger.debug(f"Attempting to read file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        logger.debug(f"File read successfully with UTF-8 encoding: {file_path}")
        return content
    except UnicodeDecodeError:
        logger.warning(f"UnicodeDecodeError encountered. Trying with 'latin-1' encoding for file: {file_path}")
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()
            logger.debug(f"File read successfully with latin-1 encoding: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Failed to read file {file_path} with both UTF-8 and latin-1 encodings")
            raise UtilityError(f"Unable to read file {file_path}: {str(e)}")

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
def process_sentences(sentences, nlp, batch_size=500):
    """
    Process a list of sentences using the provided NLP model.

    Args:
        sentences (list): A list of sentences to process.
        nlp: The spaCy NLP model to use for processing.
        batch_size (int): The batch size for processing.

    Returns:
        list: A list of processed spaCy Doc objects.

    Raises:
        UtilityError: If sentence processing fails.
    """
    logger.debug(f"Processing {len(sentences)} sentences with batch size {batch_size}")
    try:
        processed = list(tqdm(nlp.pipe(sentences, batch_size=batch_size), desc="Processing texts", unit="text", total=len(sentences)))
        logger.debug("Sentence processing completed successfully")
        return processed
    except Exception as e:
        logger.error(f"Error during sentence processing: {str(e)}")
        raise UtilityError(f"Failed to process sentences: {str(e)}")

@log_exceptions
def create_token_dict(token, doc):
    """
    Create a dictionary representation of a spaCy token.

    Args:
        token (spacy.tokens.Token): A spaCy token.
        doc (spacy.tokens.Doc): The spaCy Doc object containing the token.

    Returns:
        dict: A dictionary containing token information.

    Raises:
        UtilityError: If token dictionary creation fails.
    """
    try:
        return {
            "text": token.text,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "tag": token.tag_,
            "dep": token.dep_,
            "morph": str(token.morph.to_dict()),  # Convert MorphAnalysis to dictionary and then to string
            "category": ", ".join(span.label_ for span in doc.spans.get("sc", []) if span.start <= token.i < span.end)
        }
    except Exception as e:
        logger.error(f"Error creating token dictionary for token '{token.text}': {str(e)}")
        raise UtilityError(f"Failed to create token dictionary: {str(e)}")

@log_exceptions
def create_sentence_dict(original_sentence, doc):
    """
    Create a dictionary representation of a sentence and its tokens.

    Args:
        original_sentence (str): The original sentence text.
        doc (spacy.tokens.Doc): The spaCy Doc object for the sentence.

    Returns:
        dict: A dictionary containing the sentence text and token information.

    Raises:
        UtilityError: If sentence dictionary creation fails.
    """
    try:
        return {
            "text": original_sentence,
            "tokens": [create_token_dict(token, doc) for token in doc]
        }
    except Exception as e:
        logger.error(f"Error creating sentence dictionary: {str(e)}")
        raise UtilityError(f"Failed to create sentence dictionary: {str(e)}")

@log_exceptions
def create_text_tagging_object(sentences, nlp, batch_size=500):
    """
    Create a text tagging object for a list of sentences.

    Args:
        sentences (list): A list of sentences to process.
        nlp: The spaCy NLP model to use for processing.
        batch_size (int): The batch size for processing.

    Returns:
        list: A list of dictionaries, each containing sentence and token information.

    Raises:
        UtilityError: If text tagging object creation fails.
    """
    logger.debug(f"Creating text tagging object for {len(sentences)} sentences")
    try:
        # Clean the sentences by removing TLG reference tags
        cleaned_sentences = [remove_tlg_ref_tags(sentence) for sentence in sentences]
        # Process the cleaned sentences with spaCy
        docs = process_sentences(cleaned_sentences, nlp, batch_size)
        
        # Create the tagged object
        tagged_object = [create_sentence_dict(original_sentence, doc) for original_sentence, doc in zip(sentences, docs)]
        logger.debug("Text tagging object created successfully")
        return tagged_object
    except Exception as e:
        logger.error(f"Error creating text tagging object: {str(e)}")
        raise UtilityError(f"Failed to create text tagging object: {str(e)}")
