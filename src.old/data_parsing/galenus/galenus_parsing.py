import re
import json
import multiprocessing as mp
import spacy
import spacy_transformers
gpu = spacy.prefer_gpu()
print(gpu)
from tqdm import tqdm
#from LOCAL_SETTINGS import SPACY_MODEL_PATH as spaCy_Model
spaCy_Model = "models/ner_pipeline_22_dec_trf/model-best"
def sentencizer(text):


    delimiters_pattern = r'[.|·]'
    sentences = re.split(delimiters_pattern, text)
    #print("sentence: ", sentences)
    return sentences
def clean_text(text):

    text = text.replace("{", "").replace("}", "")


    apostrophes = [' ̓', "᾿", "᾽", "'", "’", "‘"]  # all possible apostrophes
    for apostrophe in apostrophes:
        text = text.replace(apostrophe, "ʼ")
    clean = ' '.join(text.replace('-\n', '').replace('\r', ' ').replace('\n', ' ').split())
    #clean = text.replace('-\n', "").replace('\r', " ").replace('\n', " ")
    print("clean sentence: ",clean)
    return clean
def write_to_jsonl(data_list, file_path="output.jsonl"):
    with open(file_path, 'w', encoding='utf-8') as file:
        for data_dict in data_list:
            json.dump(data_dict, file, ensure_ascii=False)
            file.write('\n')


def create_text_tagging_object(texts):
    from tqdm import tqdm

    docs = list(tqdm(nlp.pipe(texts, batch_size=1000), desc="Processing texts", unit="text"))
    sentences = [list(doc.sents) for doc in docs]
    
    sentences_tagged = []
    for sentence_list in tqdm(sentences, desc="Processing sentences", unit="sentence"):
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
                        "category": token.ent_type_,
                        "dep": token.dep_,
                        # "is_alpha": token.is_alpha,
                        # "is_stop": token.is_stop,
                    }
                    for token in sentence
                ]
            }
            sentences_tagged.append(sentence_dict)
    return sentences_tagged

import os

# Get the current working directory
cwd = os.getcwd()

# Specify the relative path to the file
folder_path = os.path.join(cwd, 'assets/texts')
file_list = os.listdir(folder_path)
os.makedirs(f'{folder_path}/annotated_texts', exist_ok=True)


    
def read_jsonl_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data_list = [json.loads(line) for line in file]
    return data_list
def create_data():
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        # Your existing code here
        galenus_text = ''
        with open(file_path, 'r', encoding='utf-8') as file:
            galenus_text = file.read()
        galenus_text = clean_text(galenus_text)
        galenus_sentences = sentencizer(galenus_text)
        tagged = create_text_tagging_object(galenus_sentences)
        write_to_jsonl(tagged, f"{folder_path}/annotated_texts/{file_name}_tagged.jsonl")
if __name__ == "__main__":
    # Set the start method for multiprocessing
    #mp.set_start_method('spawn')
    nlp = spacy.load(spaCy_Model)
    create_data()   