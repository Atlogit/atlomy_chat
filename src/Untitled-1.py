import os
import json
from typing import List, Dict, Any

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """
    Load processed data from a JSONL file.
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

processed_texts: Dict[str, Any] = {}

corpus_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'texts', 'annotated')
for file_name in os.listdir(corpus_dir):
                if file_name.endswith('_tagged.jsonl'):
                    text_id = file_name.replace('_tagged.jsonl', '')
                    if text_id not in processed_texts:
                        processed_texts[text_id] = load_jsonl(os.path.join(corpus_dir, file_name))

result = []
for text_id, sentences in processed_texts.items():
    for sentence in sentences:
        for token in sentence['tokens']:
            if 'ADV' in token['pos']:
                result.append(sentence['text'])                  
                print(sentence['text'])
print(result)