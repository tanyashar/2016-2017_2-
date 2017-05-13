# -*- coding: utf-8 -*-
import flask
import telebot
import conf
import re

def count_words(text):
    regexp = re.compile('[a-zA-Zа-яА-Я0-9-]+', flags = re.U | re.DOTALL)
    lst = regexp.findall(text)
    return len(lst)

WEBHOOK_URL_BASE = "https://{}:{}".format(conf.WEBHOOK_HOST, conf.WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)

bot = telebot.TeleBot(conf.TOKEN, threaded=False) 

bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

app = flask.Flask(__name__)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Здравствуйте! Это бот, который считает длину вашего сообщения в словах.")


@bot.message_handler(func=lambda m: True)  
def send_len(message):
    words = count_words(message.text)
    if words%10 == 1 and words!=11:
        bot.send_message(message.chat.id, 'В вашем сообщении {} слово.'.format(words))
    else:
        if words%10 in [2,3,4] and words not in [12, 13, 14]:
            bot.send_message(message.chat.id, 'В вашем сообщении {} слова.'.format(words))
        else:
            bot.send_message(message.chat.id, 'В вашем сообщении {} слов.'.format(words))  
    

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
