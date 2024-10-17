import re
import json
import spacy
import spacy_transformers
from tqdm import tqdm
import os
import sys

# Add the parent directory to the Python path to import CorpusManager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from corpus_manager import CorpusManager

gpu = spacy.prefer_gpu()
print(f"GPU available: {gpu}")

# Use an absolute path or a path relative to the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
spaCy_Model = os.path.join(project_root, "assets", "models", "atlomy_full_pipeline_annotation_131024", "model-best")

print(f"Loading spaCy model from: {spaCy_Model}")

def sentencizer(text):
    delimiters_pattern = r'[.|·]'
    sentences = re.split(delimiters_pattern, text)
    return sentences

def clean_text(text):
    text = text.replace("{", "").replace("}", "")
    apostrophes = [' ̓', "᾿", "᾽", "'", "'", "'"]  # all possible apostrophes
    for apostrophe in apostrophes:
        text = text.replace(apostrophe, "ʼ")
    clean = ' '.join(text.replace('-\n', '').replace('\r', ' ').replace('\n', ' ').split())
    print("Clean sentence: ", clean)
    return clean

def create_text_tagging_object(texts):
    try:
        nlp = spacy.load(spaCy_Model)
        nlp.get_pipe("spancat").cfg["threshold"] = 0.2
    except Exception as e:
        print(f"Error loading spaCy model: {e}")
        raise

    docs = list(tqdm(nlp.pipe(texts, batch_size=1000), desc="Processing texts", unit="text"))
    sentences = [list(doc.sents) for doc in docs]
    
    sentences_tagged = []
    for doc, sentence_list in zip(docs, tqdm(sentences, desc="Processing sentences", unit="sentence")):
        # Tokenization and part-of-speech tagging
        for sentence in sentence_list:
            sentence_dict = {
                "text": sentence.text,
                "tokens": [
                    {
                        "text": token.text,
                        "lemma": token.lemma_,
                        "pos": token.pos_,
                        "tag": token.tag_,
                        "dep": token.dep_,
                        "morph": str(token.morph.to_dict()),
                        "category": ", ".join(span.label_ for span in doc.spans.get("sc", []) if span.start <= token.i < span.end)
                    }
                    for token in sentence
                ]
            }
            sentences_tagged.append(sentence_dict)
    return sentences_tagged

def process_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    text = clean_text(text)
    text_sentences = sentencizer(text)
    tagged = create_text_tagging_object(text_sentences)
    return tagged

def create_data(input_path, corpus_manager, skip_existing=False):
    if os.path.isfile(input_path):
        text_id = os.path.splitext(os.path.basename(input_path))[0]
        if skip_existing and corpus_manager.text_exists(text_id):
            print(f"Skipping {input_path} as it already exists in the corpus.")
        else:
            print(f"Processing file: {input_path}")
            tagged_data = process_text_file(input_path)
            corpus_manager.add_text(text_id, tagged_data)
    elif os.path.isdir(input_path):
        for file_name in os.listdir(input_path):
            file_path = os.path.join(input_path, file_name)
            if os.path.isfile(file_path) and not file_name.startswith("TLG"):
                text_id = os.path.splitext(file_name)[0]
                if skip_existing and corpus_manager.text_exists(text_id):
                    print(f"Skipping {file_name} as it already exists in the corpus.")
                else:
                    print(f"Processing file: {file_name}")
                    tagged_data = process_text_file(file_path)
                    corpus_manager.add_text(text_id, tagged_data)
    else:
        raise ValueError(f"Invalid input path: {input_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process text files and add them to the corpus.")
    parser.add_argument('input_path', help='Path to input file or directory')
    parser.add_argument('--corpus_path', default=os.path.join('..', '..', 'assets', 'texts', 'annotated'), help='Path to corpus directory')
    parser.add_argument('--skip-existing', action='store_true', help='Skip processing files that already exist in the corpus.')
    args = parser.parse_args()
    
    corpus_manager = CorpusManager(args.corpus_path)
    create_data(args.input_path, corpus_manager, skip_existing=args.skip_existing)
    corpus_manager.save_texts()
