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
    sentences = [sentence.strip() for sentence in sentences]
    #print("sentence: ", sentences)
    return sentences
def clean_text(text):

    text = text.replace("{", "").replace("}", "")


    apostrophes = [' ̓', "᾿", "᾽", "'", "’", "‘"]  # all possible apostrophes
    for apostrophe in apostrophes:
        text = text.replace(apostrophe, "ʼ")
    clean = ' '.join(text.replace('-\n', '').replace('\r', ' ').replace('\n', ' ').split())
    #clean = text.replace('-\n', "").replace('\r', " ").replace('\n', " ")
    # print("clean sentence: ",clean)
    return clean
def write_to_jsonl(data_list, file_path="output.jsonl"):
    with open(file_path, 'w', encoding='utf-8') as file:
        for data_dict in data_list:
            json.dump(data_dict, file, ensure_ascii=False)
            file.write('\n')


def remove_tlg_ref_tags(text):
    # Define the pattern to match <tlg_ref>...</tlg_ref> tags
    pattern = re.compile(r'<tlg_ref>.*?</tlg_ref>', re.DOTALL)

    # Remove the matched tags and content
    cleaned_text = re.sub(pattern, '', text)

    return cleaned_text
def create_text_tagging_object(sentences):
    nlp = spacy.load(spaCy_Model)

    sentences_tagged = []
    for sentence in tqdm(sentences, desc="Processing sentences", unit="sentence"):
        # Tokenization and part-of-speech tagging
        doc = nlp(remove_tlg_ref_tags(sentence))

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

def fix_words_that_carry_over_next_line(text):
    # pattern = r'(\S+)-\s*<tlg_ref>.*?</tlg_ref>\s*((\w+))'
    # match = re.search(pattern, text)
    # if match:
    #     # word_to_move = match.group(1)
    #     a = match.group(0)
    #     b = match.group(1)
    #     c = match.group(2)
    #     d = match.group(3)
    #     e = match.group(3)
    #     # modified_text = re.sub(pattern, r'\1 <tlg_ref>', text)
    #     # return modified_text.replace(word_to_move + '-', word_to_move)
    pattern = r'(\S+)-\s*<tlg_ref>.*?</tlg_ref>\s*(\w+)'
    def replace_function(match):
        return match.group(1) + match.group(2) + match.group(0)[len(match.group(1)) + 1:-len(match.group(2))]

    # Perform the substitution
    text = re.sub(pattern, replace_function, text)
    return text
def create_data():
    tlgu_text = ''
    with open("TLG0627_hippocrates.txt-001.txt", 'r') as file:
        tlgu_text = file.read()
    # text = "[0057] [001] [] [] some text here [0058] [002] [] [] more text [0059] [003] [] [] final text"
    # pattern = r'\[\d*\] +\[\d*\] +\[\d*\] +\[\d*\]'
    pattern = r'(\[\d*\] +\[\d*\] +\[\d*\] +\[\d*\])'
    result = re.split(pattern, tlgu_text)

    # Remove empty strings from the result
    result = [item.strip() for item in result if item.strip()]
    prefixes = result[0::2]
    texts = result[1::2]
    final = []
    for prefix, text in zip(prefixes, texts):
        lines = text.split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        lines = [line[:6].replace('.', '*') + line[6:] for line in lines]
        lines = ["<tlg_ref>" + prefix + " " + line for line in lines]
        lines = [line.replace("\t", "</tlg_ref>") for line in lines]
        final += lines

    tlgu_text = " ".join(final)
    tlgu_text = clean_text(tlgu_text)
    tlgu_text = fix_words_that_carry_over_next_line(tlgu_text)
    sentences = sentencizer(tlgu_text)
    tagged = create_text_tagging_object(sentences)
    write_to_jsonl(tagged, "hippocrates_tagged_data.jsonl")
if __name__ == "__main__":
    create_data()