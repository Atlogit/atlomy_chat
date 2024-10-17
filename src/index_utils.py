import json
import re
import importlib.util
from pathlib import Path
from .logging_config import logger

class TLGParser:
    def __init__(self, tlg_index_path, work_numbers_path):
        self.tlg_index = self._load_index(tlg_index_path, 'TLG_INDEX')
        self.work_numbers = self._load_index(work_numbers_path, 'TLG_WORKS_INDEX')

    def _load_index(self, index_path, index_name):
        # Dynamic loading of indices
        index_file_path = Path(index_path).resolve()
        spec = importlib.util.spec_from_file_location("index_module", index_file_path)
        index_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(index_module)
        logger.info(f"Loaded index: {index_name}")
        return getattr(index_module, index_name)

    def _replace_tlg_refs(self, text):
        pattern = (r'<tlg_ref>\[(\d{4})\] \[(\d{3})\] \[(.*?)\] \[(.*?)\]'
                   r'(?: VOL\((.*?)\))?(?:\*VB\((.*?)\))?(?:\*L\((.*?)\))?</tlg_ref>')
    
        def repl(match):
            author_id, work_id, book_abbr, unknown_fourth, volume, vb, line = match.groups()
            # Use author_id to get author name
            author_name = self.tlg_index.get(f"TLG{author_id}", "Unknown Author")
            # Use author_id and work_id to get work name
            work_name = self.work_numbers.get(f"{author_id}", {}).get(work_id, "Unknown Work")
            logger.debug(f"Author: {author_name}, Work: {work_name}")
            logger.debug(f"Work details: {self.work_numbers.get(f'TLG{author_id}', {}).get(work_id, 'Unknown Work')}")
            citation_details = self._construct_citation(volume, vb, line)
            return f"{author_name}, {work_name} ({citation_details})"
            
        return re.sub(pattern, repl, text)
    
    def _construct_citation(self, volume, vb, line):
        # Helper function to construct citation details from captured groups
        details = []
        if volume:
            details.append(f"Volume {volume}")
        if vb:
            details.append(f"Ch. {vb}")
        if line:
            details.append(f"Line {line}")
        return ", ".join(details)

    def process_texts(self, texts):
        logger.info("Processing texts")
        if isinstance(texts, str):
            logger.info("Processing a single text")
            return self._replace_tlg_refs(texts)
        elif isinstance(texts, list):
            logger.info("Processing a list of texts")
            return [self._replace_tlg_refs(text) for text in texts]
        else:
            logger.error("Invalid input type")
            raise ValueError("Input must be a string or a list of strings.")
        
    def process_file(self, input_file_path, output_file_path=None):
        """Process a JSONL file: read, process, and optionally write the processed data back."""
        processed_lines = []
        logger.info(f"Processing file: {input_file_path}")
        with open(input_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                json_obj = json.loads(line)
                text = json_obj.get("text", "")
                processed_text = self._replace_tlg_refs(text)
                json_obj["text"] = processed_text
                processed_lines.append(json_obj)

        if output_file_path:
            logger.info(f"Writing processed data to: {output_file_path}")
            with open(output_file_path, 'w', encoding='utf-8') as file:
                for line in processed_lines:
                    file.write(json.dumps(line) + "\n")

        return processed_lines
