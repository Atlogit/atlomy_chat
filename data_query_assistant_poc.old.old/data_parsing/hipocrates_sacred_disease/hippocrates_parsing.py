import re
import json
import spacy
import spacy_transformers
from tqdm import tqdm
from LOCAL_SETTINGS import SPACY_MODEL_PATH as spaCy_Model
# spaCy_Model = " # reference to the spaCy model"
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


def create_text_tagging_object(sentences):
    nlp = spacy.load(spaCy_Model)

    sentences_tagged = []
    for sentence in tqdm(sentences, desc="Processing sentences", unit="sentence"):
        # Tokenization and part-of-speech tagging
        doc = nlp(sentence)

        doc_dict = {
            "text": sentence,
            "tokens": [
                {
                    "text": token.text,
                    "lemma": token.lemma_,
                    "pos": token.pos_,
                    "tag": token.tag_,
                    "category": token.ent_type_,
                    # "dep": token.dep_,
                    # "is_alpha": token.is_alpha,
                    # "is_stop": token.is_stop,
                }
                for token in doc
            ]
        }
        sentences_tagged += [doc_dict]
    return sentences_tagged

def read_jsonl_to_list(file_path):
    with open(file_path, 'r') as file:
        data_list = [json.loads(line) for line in file]
    return data_list
def create_data():
    text = ''
    with open("Hippocrates_Sacred Disease (Morb. Sacr.).txt", 'r') as file:
        galenus_text = file.read()
    galenus_text = clean_text(galenus_text)
    galenus_sentences = sentencizer(galenus_text)
    tagged = create_text_tagging_object(galenus_sentences)
    write_to_jsonl(tagged, "hippocrates_sacred_disease_tagged_data.jsonl")
if __name__ == "__main__":
    create_data()