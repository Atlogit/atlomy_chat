import json
import re
import os
import importlib.util
from pathlib import Path
from .logging_config import get_logger

def get_index_logger():
    return get_logger()

class TLGParser:
    def __init__(self, tlg_index_path, work_numbers_path, citation_config_path=None):
        self.logger = get_index_logger()
        self.tlg_index = self._load_index(tlg_index_path, 'TLG_INDEX')
        self.work_numbers = self._load_index(work_numbers_path, 'TLG_WORKS_INDEX')
        
        if citation_config_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            citation_config_path = os.path.join(script_dir, 'data_parsing', 'citation_config.json')
        
        self.citation_config = self._load_citation_config(citation_config_path)
        self.logger.info(f"TLGParser initialized with citation_config: {self.citation_config is not None}")

    def _load_index(self, index_path, index_name):
        index_file_path = Path(index_path).resolve()
        spec = importlib.util.spec_from_file_location("index_module", index_file_path)
        index_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(index_module)
        self.logger.info(f"Loaded index: {index_name}")
        return getattr(index_module, index_name)

    def _load_citation_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Loaded citation config from {config_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"Citation config file not found: {config_path}")
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in citation config file: {config_path}")
        except Exception as e:
            self.logger.error(f"Error loading citation config: {str(e)}")
        return None

    def _replace_tlg_refs(self, text):
        if self.citation_config is None:
            self.logger.warning("Citation config is not loaded. TLG reference replacement may be incomplete.")
            return text

        pattern = r'<tlg_ref>(.*?)</tlg_ref>'
        self.logger.debug(f"Processing text: {text[:100]}...")  # Log first 100 characters

        def repl(match):
            citation = match.group(1)
            self.logger.debug(f"Processing citation: {citation}")
            if 'citation_patterns' not in self.citation_config:
                self.logger.error("citation_patterns not found in citation_config")
                return match.group(0)  # Return the original match if citation_patterns is missing
            for pattern_config in self.citation_config['citation_patterns']:
                regex = re.compile(pattern_config['pattern'])
                citation_match = regex.search(citation)
                if citation_match:
                    groups = dict(zip(pattern_config['groups'], citation_match.groups()))
                    self.logger.debug(f"Matched groups: {groups}")
                    if 'author_id' in groups and 'work_id' in groups:
                        author_name = self.tlg_index.get(f"TLG{groups['author_id']}", "Unknown Author")
                        work_name = self.work_numbers.get(f"{groups['author_id']}", {}).get(groups['work_id'], "Unknown Work")
                        groups['author_name'] = author_name
                        groups['work_name'] = work_name
                    try:
                        # Build the formatted citation with optional fields
                        formatted_citation = f"{groups.get('author_name', '')}, {groups.get('work_name', '')}"
                        if groups.get('division') or groups.get('subdivision'):
                            formatted_citation += f" ({groups.get('division', '')}, {groups.get('subdivision', '')})"
                        # Include the rest of the reference info (e.g., Chapter and Line)
                        rest_of_reference = citation.split('],', 1)[-1].strip()
                        if rest_of_reference:
                            formatted_citation += f", {rest_of_reference}"
                        self.logger.debug(f"Formatted citation: {formatted_citation}")
                        return formatted_citation.strip(', ') + ": "
                    except KeyError as e:
                        self.logger.error(f"KeyError in format string: {str(e)}")
                        return citation  # Return original citation if format fails
            return citation  # Return original citation if no pattern matches

        result = re.sub(pattern, repl, text)
        self.logger.debug(f"Processed text: {result[:100]}...")  # Log first 100 characters of the result
        return result

    def process_texts(self, texts):
        self.logger.info("Processing texts")
        if texts is None:
            self.logger.error("Received None instead of texts to process")
            return []
        if isinstance(texts, str):
            self.logger.info("Processing a single text")
            return [self._replace_tlg_refs(texts)]
        elif isinstance(texts, list):
            self.logger.info(f"Processing a list of {len(texts)} texts")
            processed_texts = []
            for text in texts:
                if isinstance(text, str):
                    processed_texts.append(self._replace_tlg_refs(text))
                else:
                    self.logger.warning(f"Skipping non-string item in texts: {type(text)}")
            self.logger.info(f"Processed {len(processed_texts)} texts")
            return processed_texts
        else:
            self.logger.error(f"Invalid input type: {type(texts)}")
            raise ValueError("Input must be a string or a list of strings.")
        
    def process_file(self, input_file_path, output_file_path=None):
        processed_lines = []
        self.logger.info(f"Processing file: {input_file_path}")
        with open(input_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                json_obj = json.loads(line)
                text = json_obj.get("text", "")
                processed_text = self._replace_tlg_refs(text)
                json_obj["text"] = processed_text
                processed_lines.append(json_obj)

        if output_file_path:
            self.logger.info(f"Writing processed data to: {output_file_path}")
            with open(output_file_path, 'w', encoding='utf-8') as file:
                for line in processed_lines:
                    file.write(json.dumps(line) + "\n")

        return processed_lines
