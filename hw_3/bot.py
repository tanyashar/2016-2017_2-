# -*- coding: utf-8 -*-
import flask
import telebot
import conf
import json
import random
import re
import pymorphy2
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()

def find_words(text):
    regexp = re.compile('[a-zA-Z0-9-]+', flags = re.U | re.DOTALL)
    lst = regexp.findall(text)
    return lst

def find_words_rus(text):
    regexp = re.compile('[^а-яА-Я0-9-]+', flags = re.U | re.DOTALL)
    lst = regexp.findall(text)
    return lst

def make_text(text):
    lst = json.load(open('lemmas.json', 'r', encoding='utf-8'))
    
    ct = 0
    if len(text) != 0:
        for i in range(len(text)-1,0,-1):
            if text[i] != ' ':
                break
            else:
                ct += 1
    text = text[0:len(text)-ct]

    s = text.split(' ')
    ss=[]
    for i in s:
        symb = find_words_rus(i)
        if len(symb)!=0:
            if len(i)-len(symb[0]) != 0:
                ss.append(i[0:len(i)-len(symb[0])])
            ss.append(symb[0])
        else:
            ss.append(i)
            
    l = ['NPRO', 'PREP', 'CONJ', 'PRCL']
    #чтобы сохранить согласование, меняем любые части речи, кроме местоимений-существительных, предлогов, союзов и частиц
    final_text=''
    capital=0
    for i in ss:
        if not ('а'<=i[0]<='я' or 'А'<=i[0]<='Я'):
            if i[0]=='-':
                final_text += ' '
            final_text += i
            continue
            
        capital = 0
        if 'А'<=i[0]<='Я':
            capital = 1
        
        word = morph.parse(i)[0]
        if word.tag.POS not in l:      
            new_word = morph.parse(random.choice(lst))[0]        
            while word.normalized.tag != new_word.normalized.tag:
                new_word = morph.parse(random.choice(lst))[0]
            forms = set(find_words(str(word.tag))[1:])
            ft = new_word.inflect(forms).word
            if 'Name' in forms or 'Geox' in forms or 'Surn' in forms or 'Patr' in forms or 'Orgn' in forms or 'Trad' in forms:
                ft = ft[0].upper() + ft[1:]
            if 'Abbr' in forms:
                ft = ft.upper()
        else:
            ft = word.word

        if capital == 1:
            ft = ft[0].upper() + ft[1:]
        
        if len(final_text)!=0 and final_text[len(final_text)-1]!=' ':
            final_text += ' '
        
        final_text += ft

    return final_text



WEBHOOK_URL_BASE = "https://{}:{}".format(conf.WEBHOOK_HOST, conf.WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)

bot = telebot.TeleBot(conf.TOKEN, threaded=False) 

bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

app = flask.Flask(__name__)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Здравствуйте! Это бот, который будет вас передразнивать.")


@bot.message_handler(func=lambda m: True)  
def send_len(message):
    final_text = make_text(message.text)
    bot.send_message(message.chat.id, final_text)  
    

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'check OK'


@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
