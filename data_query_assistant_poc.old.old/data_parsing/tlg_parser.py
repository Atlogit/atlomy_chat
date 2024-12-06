import re
import json
import spacy
import spacy_transformers
from tqdm import tqdm
import os

from LOCAL_SETTINGS import SPACY_MODEL_PATH as spaCy_Model
#spaCy_Model = "models/ner_11_feb_2024_trf/model-best"
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
    cleaned_sentences = [remove_tlg_ref_tags(sentence) for sentence in sentences]
    #for doc in tqdm(nlp.pipe((remove_tlg_ref_tags(sentence) for sentence in sentences), batch_size=1000), total=len(sentences), desc="Processing sentences", unit="sentence"):
    for original_sentence, doc in zip(sentences, tqdm(nlp.pipe(cleaned_sentences), total=len(sentences), desc="Processing sentences", unit="sentence")):
        # Tokenization and part-of-speech tagging
        doc_dict = {
            "text": original_sentence,
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
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            output_file_path = os.path.join(folder_path, "annotated_texts", f"{os.path.splitext(file_name)[0]}.txt_tagged.jsonl")
            if not os.path.exists(output_file_path):
                print(f"Processing file: {file_name}")
                # Process the file and write the output to output_file_path
                tlgu_text = ''
                with open(file_path, 'r') as file:
                    tlgu_text = file.read()
                # text = "[0057] [001] [] [] some text here [0058] [002] [] [] more text [0059] [003] [] [] final text"
                # pattern = r'\[\d*\] +\[\d*\] +\[\d*\] +\[\d*\]'
                pattern = r'(\[\w*\] +\[\w*\] +\[\w*\] +\[\w*\])'
                result = re.split(pattern, tlgu_text)

                # Remove empty strings from the result
                result = [item.strip() for item in result if item.strip()]
                prefixes = result[0::2]
                texts = result[1::2]
                final = []
                for prefix, text in zip(prefixes, texts):
                    lines = text.split("\n")
                    lines = [line.strip() for line in lines if line.strip()]
                    #lines = [line[:6].replace('.', '*') + line[6:] for line in lines]
                    lines = [line[:line.find('\t')].replace('.', '*') + line[line.find('\t'):] for line in lines]
                    lines = ["<tlg_ref>" + prefix + " " + line for line in lines]
                    lines = [line.replace("\t", "</tlg_ref>") for line in lines]
                    final += lines

                tlgu_text = " ".join(final)
                tlgu_text = clean_text(tlgu_text)
                tlgu_text = fix_words_that_carry_over_next_line(tlgu_text)
                sentences = sentencizer(tlgu_text)
                tagged = create_text_tagging_object(sentences)
                write_to_jsonl(tagged, output_file_path)
if __name__ == "__main__":
    create_data()