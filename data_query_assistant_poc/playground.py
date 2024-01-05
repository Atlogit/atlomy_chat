import csv
import json
import re
import os
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI, ChatAnthropic

# from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
# from langchain.chains import SimpleSequentialChain
# import numpy as np
import spacy
api_key = os.getenv("OPENAI_API_KEY_ATLOMY")
from tqdm import tqdm



class LLMOracle:
    def __init__(self, chat_model_name="gpt-3.5-turbo", temperature=.5):
        self.chat_model_name = chat_model_name
        self.temperature = temperature

    def query_llm(self, template_fstring, arguments_list=[]):
        formatted_string = template_fstring.format(*arguments_list)
        llm = ChatOpenAI(model=self.chat_model_name, temperature=self.temperature, request_timeout=120)
        user_prompt = PromptTemplate.from_template("# Input\n{text}")
        human_message = HumanMessage(content=user_prompt.format(text=formatted_string))
        answer = llm([human_message])

        return answer.content

def sentencizer(text):
    delimiters_pattern = r'[.|·]'
    sentences = re.split(delimiters_pattern, text)
    return sentences
def clean_text(text):
    clean = text.replace('-\n', "")
    return clean
def create_text_tagging_object(sentences):
    nlp = spacy.load("ner_pipeline_22_dec_trf/model-best")

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
                    # "dep": token.dep_,
                    # "is_alpha": token.is_alpha,
                    # "is_stop": token.is_stop,
                }
                for token in doc
            ]
        }
        sentences_tagged += [doc_dict]
    return sentences_tagged

if __name__ == "__main__":
    from pprint import pprint
    print("hi")
    # oracle = LLMOracle()
    # answer = oracle.query_llm("Do you like ancient greek?")
    # print(answer)

    from spacy.tokens import DocBin

    galenus_text = ''
    with open("TLG_Galen_Anatomical Administrations(AA).txt", 'r') as file:
        galenus_text = file.read()
    galenus_text = clean_text(galenus_text)
    galenus_sentences = sentencizer(galenus_text)
    tagged = create_text_tagging_object(galenus_sentences)


    print("bye")
