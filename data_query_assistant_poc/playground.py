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



class LLMOAssistant:
    data_query_template = """
    given a list of dicts called 'tagged_galenus' that looks like this:
 {'text': ' ὑμένες δὲ καὶ τούτοις \n'
          "ἐπίκεινται, μεθ' ὧν ἐξαιρήσεις αὐτὰ μετά γε τὴν τῶν μυῶν \n"
          'ἀνατομήν',
  'tokens': [{'lemma': ' ', 'pos': 'ADV', 'tag': 'Df', 'text': ' '},
             {'lemma': 'ὑμένες', 'pos': 'NOUN', 'tag': 'Nb', 'text': 'ὑμένες'},
             {'lemma': 'δὲ', 'pos': 'CCONJ', 'tag': 'C-', 'text': 'δὲ'},
             {'lemma': 'καί', 'pos': 'CCONJ', 'tag': 'C-', 'text': 'καὶ'},
             {'lemma': 'τούτοις',
              'pos': 'PRON',
              'tag': 'Pd__Case=Dat|Gender=Masc|Number=Plur',
              'text': 'τούτοις'},
             {'lemma': '\n', 'pos': 'ADV', 'tag': 'Df', 'text': '\n'},
             {'lemma': 'ἐπίκειντος',
              'pos': 'VERB',
              'tag': 'V-__Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin|Voice=Mid',
              'text': 'ἐπίκεινται'},
             {'lemma': ',', 'pos': 'PUNCT', 'tag': 'Z', 'text': ','},
             {'lemma': "μεθ'", 'pos': 'ADP', 'tag': 'R-', 'text': "μεθ'"},
             {'lemma': 'ὅς',
              'pos': 'PRON',
              'tag': 'Pr__Case=Nom|Gender=Fem|Number=Sing|PronType=Rel',
              'text': 'ὧν'},
             {'lemma': 'ἐξαιρήζω',
              'pos': 'VERB',
              'tag': 'V-__Mood=Ind|Number=Sing|Person=2|Tense=Pres|VerbForm=Fin|Voice=Act',
              'text': 'ἐξαιρήσεις'},
             {'lemma': 'αὐτός',
              'pos': 'PRON',
              'tag': 'Pp__Case=Acc|Gender=Neut|Number=Plur|Person=3|PronType=Prs',
              'text': 'αὐτὰ'},
             {'lemma': 'μετά', 'pos': 'ADP', 'tag': 'R-', 'text': 'μετά'},
             {'lemma': 'γε', 'pos': 'ADV', 'tag': 'Df', 'text': 'γε'},
             {'lemma': 'ὁ',
              'pos': 'DET',
              'tag': 'S-__Case=Acc|Definite=Def|Gender=Fem|Number=Sing|PronType=Dem',
              'text': 'τὴν'},
             {'lemma': 'ὁ',
              'pos': 'DET',
              'tag': 'S-__Case=Gen|Definite=Def|Gender=Masc|Number=Plur|PronType=Dem',
              'text': 'τῶν'},
             {'lemma': 'μῦς', 'pos': 'NOUN', 'tag': 'Nb', 'text': 'μυῶν'},
             {'lemma': '\n', 'pos': 'ADV', 'tag': 'Df', 'text': '\n'},
             {'lemma': 'ἀνατομής',
              'pos': 'NOUN',
              'tag': 'Nb',
              'text': 'ἀνατομήν'}]},
 {'text': ' ὑπόκεινται γὰρ οἱ τοὺς δακτύλους κάμπτοντες τένοντες ἀπὸ δυοῖν '
          'ὁρμώμενοι κεφαλῶν, ἐν ἐκείνῳ μάλιστα τῷ χωρίῳ κείμενοι, ἐν ᾧ τόν τε '
          "σύνδεσμον ἔφην τετάχθαι καὶ τὴν ἐπ' αὐτῷ κεφαλὴν τοῦ πλατυνομένου "
          'τέ- \n'
          'νοντος, ὑπὲρ οὗ πέπαυμαι λέγων',
  'tokens': [{'lemma': ' ', 'pos': 'ADV', 'tag': 'Df', 'text': ' '},
             {'lemma': 'ὑπόκειμαι',
              'pos': 'VERB',
              'tag': 'V-__Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin|Voice=Mid',
              'text': 'ὑπόκεινται'},
             {'lemma': 'γάρ', 'pos': 'CCONJ', 'tag': 'C-', 'text': 'γὰρ'},
             {'lemma': 'ὁ',
              'pos': 'DET',
              'tag': 'S-__Case=Nom|Definite=Def|Gender=Masc|Number=Plur|PronType=Dem',
              'text': 'οἱ'},
             {'lemma': 'ὁ',
              'pos': 'DET',
              'tag': 'S-__Case=Acc|Definite=Def|Gender=Neut|Number=Plur|PronType=Dem',
              'text': 'τοὺς'},
             {'lemma': 'δακτύλους',
              'pos': 'NOUN',
              'tag': 'Nb',
              'text': 'δακτύλους'},
             {'lemma': 'κάμπτω',
              'pos': 'VERB',
              'tag': 'V-__Case=Nom|Gender=Masc|Number=Sing|Tense=Pres|VerbForm=Part|Voice=Act',
              'text': 'κάμπτοντες'},
             {'lemma': 'τένων', 'pos': 'NOUN', 'tag': 'Nb', 'text': 'τένοντες'},
             {'lemma': 'ἀπό', 'pos': 'ADP', 'tag': 'R-', 'text': 'ἀπὸ'},
             {'lemma': 'δύο', 'pos': 'NUM', 'tag': 'Ma', 'text': 'δυοῖν'},
             {'lemma': 'ὁρμώμενοι',
              'pos': 'VERB',
              'tag': 'V-__Case=Nom|Gender=Fem|Number=Plur|Tense=Pres|VerbForm=Part|Voice=Mid',
              'text': 'ὁρμώμενοι'},
             {'lemma': 'κεφαλή', 'pos': 'NOUN', 'tag': 'Nb', 'text': 'κεφαλῶν'},
             {'lemma': ',', 'pos': 'PUNCT', 'tag': 'Z', 'text': ','},
             {'lemma': 'ἐν', 'pos': 'ADP', 'tag': 'R-', 'text': 'ἐν'},
             {'lemma': 'ἐκείνῳ',
              'pos': 'DET',
              'tag': 'Pd__Case=Dat|Gender=Neut|Number=Sing',
              'text': 'ἐκείνῳ'},
             {'lemma': 'μάλα', 'pos': 'ADV', 'tag': 'Df', 'text': 'μάλιστα'},
             {'lemma': 'ὁ',
              'pos': 'DET',
              'tag': 'S-__Case=Dat|Definite=Def|Gender=Neut|Number=Sing|PronType=Dem',
              'text': 'τῷ'},
             {'lemma': 'χωρίῳ', 'pos': 'NOUN', 'tag': 'Nb', 'text': 'χωρίῳ'},
             {'lemma': 'κείμενοι',
              'pos': 'VERB',
              'tag': 'V-__Case=Nom|Gender=Fem|Number=Plur|Tense=Pres|VerbForm=Part|Voice=Mid',
              'text': 'κείμενοι'},
             {'lemma': ',', 'pos': 'PUNCT', 'tag': 'Z', 'text': ','},
             {'lemma': 'ἐν', 'pos': 'ADP', 'tag': 'R-', 'text': 'ἐν'},
             {'lemma': 'ὅς',
              'pos': 'PRON',
              'tag': 'Pr__Case=Dat|Gender=Masc|Number=Sing|PronType=Rel',
              'text': 'ᾧ'},
             {'lemma': 'τόν',
              'pos': 'DET',
              'tag': 'S-__Case=Acc|Definite=Def|Gender=Fem|Number=Sing|PronType=Dem',
              'text': 'τόν'},
             {'lemma': 'τε', 'pos': 'CCONJ', 'tag': 'C-', 'text': 'τε'},
             {'lemma': 'σύνδεσμος',
              'pos': 'NOUN',
              'tag': 'Nb',
              'text': 'σύνδεσμον'},
             {'lemma': 'φημί',
              'pos': 'VERB',
              'tag': 'V-__Aspect=Imp|Mood=Ind|Number=Sing|Person=3|Tense=Past|VerbForm=Fin|Voice=Act',
              'text': 'ἔφην'},
             {'lemma': 'τάσσω',
              'pos': 'VERB',
              'tag': 'V-__Aspect=Perf|Tense=Past|VerbForm=Inf|Voice=Pass',
              'text': 'τετάχθαι'},
             {'lemma': 'καί', 'pos': 'CCONJ', 'tag': 'C-', 'text': 'καὶ'},
             {'lemma': 'ὁ',
              'pos': 'DET',
              'tag': 'S-__Case=Acc|Definite=Def|Gender=Fem|Number=Sing|PronType=Dem',
              'text': 'τὴν'},
             {'lemma': 'ἐπί', 'pos': 'ADP', 'tag': 'R-', 'text': "ἐπ'"},
             {'lemma': 'αὐτός',
              'pos': 'PRON',
              'tag': 'Pp__Case=Dat|Gender=Neut|Number=Sing|Person=3|PronType=Prs',
              'text': 'αὐτῷ'},
             {'lemma': 'κεφαλή', 'pos': 'NOUN', 'tag': 'Nb', 'text': 'κεφαλὴν'},
             {'lemma': 'ὁ',
              'pos': 'DET',
              'tag': 'S-__Case=Gen|Definite=Def|Gender=Fem|Number=Sing|PronType=Dem',
              'text': 'τοῦ'},
             {'lemma': 'πλατυνομένου',
              'pos': 'PART',
              'tag': 'V-__Case=Gen|Gender=Masc|Number=Sing|Tense=Pres|VerbForm=Part|Voice=Pass',
              'text': 'πλατυνομένου'},
             {'lemma': 'τέ', 'pos': 'CCONJ', 'tag': 'C-', 'text': 'τέ'},
             {'lemma': '-',
              'pos': 'PUNCT',
              'tag': 'Ne__Case=Nom|Gender=Masc|Number=Sing',
              'text': '-'},
             {'lemma': '\n', 'pos': 'ADV', 'tag': 'Df', 'text': '\n'},
             {'lemma': 'νος', 'pos': 'VERB', 'tag': 'Nb', 'text': 'νοντος'},
             {'lemma': ',', 'pos': 'PUNCT', 'tag': 'Z', 'text': ','},
             {'lemma': 'ὑπέρ', 'pos': 'ADP', 'tag': 'R-', 'text': 'ὑπὲρ'},
             {'lemma': 'ὅς',
              'pos': 'PRON',
              'tag': 'Pr__Case=Dat|Gender=Masc|Number=Plur|PronType=Rel',
              'text': 'οὗ'},
             {'lemma': 'πέπαυμαι',
              'pos': 'VERB',
              'tag': 'V-__Aspect=Perf|Mood=Ind|Number=Sing|Person=1|Tense=Past|VerbForm=Fin|Voice=Pass',
              'text': 'πέπαυμαι'},
             {'lemma': 'λέγω',
              'pos': 'VERB',
              'tag': 'V-__Case=Nom|Gender=Masc|Number=Sing|Tense=Pres|VerbForm=Part|Voice=Act',
              'text': 'λέγων'}]},\n\n
              
              output a python code that can print the answer to the following question. output only the code, don't include the object itself in the code.\n
              Question: 
    """
    def __init__(self, chat_model_name="gpt-3.5-turbo", temperature=.5):
        self.chat_model_name = chat_model_name
        self.temperature = temperature

    def query_llm(self, query):
        llm = ChatOpenAI(model=self.chat_model_name, temperature=self.temperature, request_timeout=120)
        user_prompt = PromptTemplate.from_template("# Input\n{text}")
        human_message = HumanMessage(content=user_prompt.format(text=query))
        answer = llm([human_message])

        return answer.content
    def the_universal_function(self, python_code):
        exec(python_code)

    def _extract_code(self, input_string):
        pattern = r'```python(.*?)```'

        #re.DOTALL to match across newlines and extract the code part
        match = re.search(pattern, input_string, re.DOTALL)
        return match.group(1) if match else None
    def ask_about_data(self, data_query):
        question = self.data_query_template + data_query

        attempts = 0

        while attempts < 3:
            try:
                answer = self.query_llm(question)
                code_from_answer = self._extract_code(answer)
                result = self.the_universal_function(code_from_answer)

                break
            except Exception as e:
                attempts += 1
                # print(f"Attempt {attempts} failed with error: {e}")

        # Check if all attempts failed
        if attempts == 3:
            print("All attempts failed. Handle the failure accordingly.")
        else:
            print("Operation successful.\n\n")




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

def write_to_jsonl(data_list, file_path="output.jsonl"):
    with open(file_path, 'w', encoding='utf-8') as file:
        for data_dict in data_list:
            json.dump(data_dict, file, ensure_ascii=False)
            file.write('\n')

def create_data():
    galenus_text = ''
    with open("TLG_Galen_Anatomical Administrations(AA).txt", 'r') as file:
        galenus_text = file.read()
    galenus_text = clean_text(galenus_text)
    galenus_sentences = sentencizer(galenus_text)
    tagged = create_text_tagging_object(galenus_sentences)
    write_to_jsonl(tagged, "galenus_tagged_data.jsonl")

def read_jsonl_to_list(file_path):
    with open(file_path, 'r') as file:
        data_list = [json.loads(line) for line in file]
    return data_list

def interactive_test():
    # Create an instance of LLMOAssistant
    oracle = LLMOAssistant()



    while True:
        user_question = input("Ask me a question (Press 'Escape' to exit): ")

        if user_question.lower() == 'escape':
            break

        # Call the ask_about_data method and print the answer
        answer = oracle.ask_about_data(user_question)
        # print("Answer:", answer)

    # End of the interactive loop
    print("Exiting the program.")

if __name__ == "__main__":
    from pprint import pprint
    # print("hi")
    # oracle = LLMOAssistant()
    #
    #
    # create_data()
    tagged_galenus = read_jsonl_to_list("galenus_tagged_data.jsonl")
    #
    # oracle.ask_about_data("")
    interactive_test()


    print("bye")
