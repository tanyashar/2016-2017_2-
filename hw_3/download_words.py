import json
import random
import re
import pymorphy2
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()

def make_set(text):
    regexp = re.compile('[а-яА-Я0-9-]+', flags = re.U | re.DOTALL)
    lst = regexp.findall(text)
    return lst

#создаем базу лемм на основе текста "Архипелаг-Гулаг"
def download_words():
    f = open('gulag.txt', 'r', encoding='utf-8')
    text = f.read()
    f.close()

    ct=0
    s = set()
    lst = make_set(text)

    for word in lst:
        ana = morph.parse(word)[0]
        lemma = ana.normal_form
        s.add(lemma)

        if ct%10000 == 0:
            print(ct/10000)
        ct += 1

    s = list(s)
    json.dump(s, open('lemmas.json', 'w', encoding='utf-8'))
    #теперь леммы в s, записаны в json в файл 'lemmas.json'

download_words()
