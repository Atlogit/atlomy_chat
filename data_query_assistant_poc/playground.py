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
api_key = os.environ.get("OPENAI_API_KEY_ATLOMY")
from tqdm import tqdm




class LLMAssistant:
    data_query_template = """
    given a python dictionary names "library" with 2 keys, the first key is "galenus_tagged_data", the second key is "hippocrates_sacred_disease_tagged_data"
    each value is a list of dicts that looks like this:\n"
{'text': ' τῶν μὲν οὖν ἐκτὸς μυῶν συναφαιρεῖν σε χρὴ '
                                   'καὶ τοὺς τένοντας ἅπαντας ἄχρι τῶν περάτων '
                                   'ὧν ἔχουσι καθʼ ἕκαστον δάκτυλον, οὐ μὴν '
                                   'ἁπάντων γε τῶν ἔνδον, ἀλλὰ πρότερον '
                                   'ἐπισκεψάμενον τοὺς παραπεφυκότας τοῖς τὸ '
                                   'τρίτον ἄρθρον κινοῦσι τένουσιν μῦς τοὺς '
                                   'μικροὺς, τότʼ ἤδη πάντας ἀποτέμνειν αὐτούς',
                           'tokens': [{'category': '',
                                       'lemma': ' ',
                                       'pos': 'ADV',
                                       'tag': 'Df',
                                       'text': ' '},
                                      {'category': '',
                                       'lemma': 'ὁ',
                                       'pos': 'DET',
                                       'tag': 'S-__Case=Gen|Definite=Def|Gender=Masc|Number=Plur|PronType=Dem',
                                       'text': 'τῶν'},
                                      {'category': '',
                                       'lemma': 'μέν',
                                       'pos': 'CCONJ',
                                       'tag': 'C-',
                                       'text': 'μὲν'},
                                      {'category': '',
                                       'lemma': 'οὖν',
                                       'pos': 'ADV',
                                       'tag': 'Df',
                                       'text': 'οὖν'},
                                      {'category': '',
                                       'lemma': 'ἐκτός',
                                       'pos': 'ADV',
                                       'tag': 'Df',
                                       'text': 'ἐκτὸς'},
                                      {'category': 'Body Part',
                                       'lemma': 'μῦς',
                                       'pos': 'NOUN',
                                       'tag': 'Nb',
                                       'text': 'μυῶν'},
                                      {'category': '',
                                       'lemma': 'συναφαιρέω',
                                       'pos': 'VERB',
                                       'tag': 'V-__Tense=Pres|VerbForm=Inf|Voice=Act',
                                       'text': 'συναφαιρεῖν'},
                                      {'category': '',
                                       'lemma': 'σύ',
                                       'pos': 'PRON',
                                       'tag': 'Pp__Case=Acc|Gender=Masc|Number=Sing|Person=2|PronType=Prs',
                                       'text': 'σε'},
                                      {'category': '',
                                       'lemma': 'χρή',
                                       'pos': 'VERB',
                                       'tag': 'V-__Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin|Voice=Act',
                                       'text': 'χρὴ'},
                                      {'category': '',
                                       'lemma': 'καί',
                                       'pos': 'CCONJ',
                                       'tag': 'C-',
                                       'text': 'καὶ'},
                                      {'category': '',
                                       'lemma': 'ὁ',
                                       'pos': 'DET',
                                       'tag': 'S-__Case=Acc|Definite=Def|Gender=Neut|Number=Plur|PronType=Dem',
                                       'text': 'τοὺς'},
                                      {'category': 'Body Part',
                                       'lemma': 'τένων',
                                       'pos': 'NOUN',
                                       'tag': 'Nb',
                                       'text': 'τένοντας'},
                                      {'category': 'Adjectives/Qualities',
                                       'lemma': 'ἅπας',
                                       'pos': 'ADJ',
                                       'tag': 'A-__Case=Acc|Degree=Pos|Gender=Fem|Number=Plur',
                                       'text': 'ἅπαντας'},
                                      {'category': 'Topography',
                                       'lemma': 'ἄχρι',
                                       'pos': 'ADP',
                                       'tag': 'R-',
                                       'text': 'ἄχρι'},
                                      {'category': '',
                                       'lemma': 'ὁ',
                                       'pos': 'DET',
                                       'tag': 'S-__Case=Dat|Definite=Def|Gender=Fem|Number=Plur|PronType=Dem',
                                       'text': 'τῶν'},
                                      {'category': 'Topography',
                                       'lemma': 'περάτων',
                                       'pos': 'NOUN',
                                       'tag': 'Nb',
                                       'text': 'περάτων'},
                                      {'category': '',
                                       'lemma': 'ὅς',
                                       'pos': 'PRON',
                                       'tag': 'Pr__Case=Gen|Gender=Fem|Number=Plur|PronType=Rel',
                                       'text': 'ὧν'},
                                      {'category': '',
                                       'lemma': 'ἔχω',
                                       'pos': 'VERB',
                                       'tag': 'V-__Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin|Voice=Act',
                                       'text': 'ἔχουσι'},
                                      {'category': 'Topography',
                                       'lemma': 'καθά',
                                       'pos': 'ADP',
                                       'tag': 'R-',
                                       'text': 'καθʼ'},
                                      {'category': '',
                                       'lemma': 'ἕκαστος',
                                       'pos': 'ADJ',
                                       'tag': 'A-__Case=Acc|Degree=Pos|Gender=Neut|Number=Sing',
                                       'text': 'ἕκαστον'},
                                      {'category': 'Body Part',
                                       'lemma': 'δάκτυλος',
                                       'pos': 'NOUN',
                                       'tag': 'Nb',
                                       'text': 'δάκτυλον'},
                                      {'category': '',
                                       'lemma': ',',
                                       'pos': 'PUNCT',
                                       'tag': 'Z',
                                       'text': ','},
                                      {'category': '',
                                       'lemma': 'οὐ',
                                       'pos': 'ADV',
                                       'tag': 'Df',
                                       'text': 'οὐ'},
                                      {'category': '',
                                       'lemma': 'μείς',
                                       'pos': 'PART',
                                       'tag': 'Df',
                                       'text': 'μὴν'},
                                      {'category': 'Adjectives/Qualities',
                                       'lemma': 'ἁπάντων',
                                       'pos': 'ADJ',
                                       'tag': 'A-__Case=Gen|Degree=Pos|Number=Plur',
                                       'text': 'ἁπάντων'},
                                      {'category': '',
                                       'lemma': 'γε',
                                       'pos': 'CCONJ',
                                       'tag': 'C-',
                                       'text': 'γε'},
                                      {'category': '',
                                       'lemma': 'ὁ',
                                       'pos': 'DET',
                                       'tag': 'S-__Case=Dat|Definite=Def|Gender=Fem|Number=Plur|PronType=Dem',
                                       'text': 'τῶν'},
                                      {'category': 'Topography',
                                       'lemma': 'ἔνδον',
                                       'pos': 'ADV',
                                       'tag': 'Df',
                                       'text': 'ἔνδον'},
                                      {'category': 'Topography',
                                       'lemma': ',',
                                       'pos': 'PUNCT',
                                       'tag': 'Z',
                                       'text': ','},
                                      {'category': 'Topography',
                                       'lemma': 'ἀλλά',
                                       'pos': 'CCONJ',
                                       'tag': 'C-',
                                       'text': 'ἀλλὰ'},
                                      {'category': '',
                                       'lemma': 'πρότερος',
                                       'pos': 'ADV',
                                       'tag': 'Df',
                                       'text': 'πρότερον'},
                                      {'category': 'Action Verbs',
                                       'lemma': 'ἐπισκεψάμενον',
                                       'pos': 'VERB',
                                       'tag': 'V-__Aspect=Perf|Case=Nom|Gender=Masc|Number=Sing|Tense=Past|VerbForm=Part|Voice=Mid',
                                       'text': 'ἐπισκεψάμενον'},
                                      {'category': '',
                                       'lemma': 'ὁ',
                                       'pos': 'DET',
                                       'tag': 'S-__Case=Acc|Definite=Def|Gender=Neut|Number=Plur|PronType=Dem',
                                       'text': 'τοὺς'},
                                      {'category': 'Topography',
                                       'lemma': 'παραπεφυκότας',
                                       'pos': 'VERB',
                                       'tag': 'V-__Aspect=Perf|Case=Nom|Gender=Masc|Number=Sing|Tense=Past|VerbForm=Part|Voice=Act',
                                       'text': 'παραπεφυκότας'},
                                      {'category': '',
                                       'lemma': 'ὁ',
                                       'pos': 'DET',
                                       'tag': 'S-__Case=Dat|Definite=Def|Gender=Fem|Number=Plur|PronType=Dem',
                                       'text': 'τοῖς'},
                                      {'category': '',
                                       'lemma': 'ὁ',
                                       'pos': 'DET',
                                       'tag': 'S-__Case=Acc|Definite=Def|Gender=Neut|Number=Sing|PronType=Dem',
                                       'text': 'τὸ'},
                                      {'category': '',
                                       'lemma': 'τρίτος',
                                       'pos': 'ADJ',
                                       'tag': 'Df',
                                       'text': 'τρίτον'},
                                      {'category': 'Body Part',
                                       'lemma': 'ἄρθρον',
                                       'pos': 'NOUN',
                                       'tag': 'Nb',
                                       'text': 'ἄρθρον'},
                                      {'category': '',
                                       'lemma': 'κινέω',
                                       'pos': 'VERB',
                                       'tag': 'V-__Case=Dat|Gender=Masc|Number=Plur|Tense=Pres|VerbForm=Part|Voice=Act',
                                       'text': 'κινοῦσι'},
                                      {'category': 'Body Part',
                                       'lemma': 'τένων',
                                       'pos': 'NOUN',
                                       'tag': 'Nb',
                                       'text': 'τένουσιν'},
                                      {'category': 'Body Part',
                                       'lemma': 'μῦς',
                                       'pos': 'NOUN',
                                       'tag': 'Nb',
                                       'text': 'μῦς'},
                                      {'category': '',
                                       'lemma': 'ὁ',
                                       'pos': 'DET',
                                       'tag': 'S-__Case=Acc|Definite=Def|Gender=Neut|Number=Plur|PronType=Dem',
                                       'text': 'τοὺς'},
                                      {'category': 'Body Part',
                                       'lemma': 'μικροὺς',
                                       'pos': 'ADJ',
                                       'tag': 'A-__Case=Acc|Degree=Pos|Gender=Fem|Number=Plur',
                                       'text': 'μικροὺς'},
                                      {'category': 'Topography',
                                       'lemma': ',',
                                       'pos': 'PUNCT',
                                       'tag': 'Z',
                                       'text': ','},
                                      {'category': 'Topography',
                                       'lemma': 'τότα',
                                       'pos': 'CCONJ',
                                       'tag': 'C-',
                                       'text': 'τότʼ'},
                                      {'category': '',
                                       'lemma': 'ἤδη',
                                       'pos': 'ADV',
                                       'tag': 'Df',
                                       'text': 'ἤδη'},
                                      {'category': '',
                                       'lemma': 'πάς',
                                       'pos': 'ADJ',
                                       'tag': 'A-__Case=Acc|Degree=Pos|Gender=Fem|Number=Plur',
                                       'text': 'πάντας'},
                                      {'category': '',
                                       'lemma': 'ἀποτέμνω',
                                       'pos': 'VERB',
                                       'tag': 'V-__Tense=Pres|VerbForm=Inf|Voice=Act',
                                       'text': 'ἀποτέμνειν'},
                                      {'category': '',
                                       'lemma': 'αὐτούς',
                                       'pos': 'PRON',
                                       'tag': 'Pp__Case=Acc|Gender=Fem|Number=Plur|Person=3|PronType=Prs',
                                       'text': 'αὐτούς'}]},
              
              output a python code that can get the answer to the following question and put it into a variable named 'result'.
              output only the code, don't include the object itself in the code.\n
              Question: 
    """
    def __init__(self, chat_model_name="gpt-3.5-turbo", temperature=.5):
        self.chat_model_name = chat_model_name
        self.temperature = temperature

    def query_llm(self, query):
        llm = ChatOpenAI(openai_api_key=api_key, model=self.chat_model_name, temperature=self.temperature, request_timeout=120)
        user_prompt = PromptTemplate.from_template("# Input\n{text}")
        human_message = HumanMessage(content=user_prompt.format(text=query))
        answer = llm([human_message])

        return answer.content
    def the_universal_function(self, python_code, *args, **kwargs):
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
                result = 'ERROR'
                self.the_universal_function(code_from_answer)
                print(result)

                break
            except Exception as e:
                attempts += 1
                # print(f"Attempt {attempts} failed with error: {e}")

        # Check if all attempts failed
        if attempts == 3:
            print("All attempts failed. Handle the failure accordingly.")
        else:
            print("Operation successful.\n\n")






def write_to_jsonl(data_list, file_path="output.jsonl"):
    with open(file_path, 'w', encoding='utf-8') as file:
        for data_dict in data_list:
            json.dump(data_dict, file, ensure_ascii=False)
            file.write('\n')



def read_jsonl_to_list(file_path):
    with open(file_path, 'r') as file:
        data_list = [json.loads(line) for line in file]
    return data_list

def interactive_test():
    # Create an instance of LLMOAssistant
    oracle = LLMAssistant()



    while True:
        user_question = input("Ask me a question (Press 'Escape' to exit): ")

        if user_question.lower() == 'escape':
            break

        # Call the ask_about_data method and print the answer
        answer = oracle.ask_about_data(user_question)
        # print("Answer:", answer)

    # End of the interactive loop
    print("Exiting the program.")
def read_jsonl_files():
    result_dict = {}

    files = [f for f in os.listdir() if f.endswith(".jsonl")]

    for file_name in files:
        with open(file_name, 'r') as file:

            data_list = [json.loads(line) for line in file]
            result_dict[file_name.replace("jsonl","")] = data_list

    return result_dict
if __name__ == "__main__":
    from pprint import pprint
    # print("hi")
    # oracle = LLMOAssistant()
    #
    #
    # create_data()
    # tagged_galenus = read_jsonl_to_list("galenus_tagged_data.jsonl")
    library = read_jsonl_files()
    # pprint(library)
    #
    # oracle.ask_about_data("")
    interactive_test()


    print("bye")
