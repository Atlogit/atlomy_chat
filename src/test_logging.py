import os
import io
import logging
from corpus_manager import CorpusManager
from logging_config import setup_logging, logger

def capture_logs(func):
    def wrapper(*args, **kwargs):
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        logger.addHandler(handler)
        
        try:
            func(*args, **kwargs)
        finally:
            logger.removeHandler(handler)
        
        log_contents = log_capture.getvalue()
        print("Captured logs:")
        print(log_contents)
        return log_contents
    return wrapper

@capture_logs
def test_corpus_manager_logging():
    logger.info("Starting corpus manager logging test")

    # Initialize CorpusManager
    corpus_manager = CorpusManager()

    # Test importing the jsonl example file
    example_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'examples', 'jsonl_example.jsonl')
    try:
        corpus_manager.import_text(example_file)
        logger.info(f"Successfully imported example file: {example_file}")
    except Exception as e:
        logger.error(f"Failed to import example file {example_file}: {str(e)}")

    # Test listing texts
    texts = corpus_manager.list_texts()
    logger.info(f"Listed {len(texts)} texts")

    # Test getting the imported text
    if texts:
        try:
            text = corpus_manager.get_text(texts[0])
            logger.info(f"Successfully retrieved text: {texts[0]}")
        except Exception as e:
            logger.error(f"Failed to retrieve text {texts[0]}: {str(e)}")

    # Test searching texts
    search_results = corpus_manager.search_texts("example")
    logger.info(f"Search returned {len(search_results)} results")

    logger.info("Corpus manager logging test completed")

if __name__ == "__main__":
    test_corpus_manager_logging()
