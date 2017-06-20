import urllib.request
import os
import re
import pymorphy2
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()
import json
import datetime
from flask import Flask
from flask import url_for, render_template, request, redirect

def download_page(page_url):
    try:
        user_a = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
        req = urllib.request.Request(page_url, headers={'User-Agent':user_a})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
    except:
        return
    return html

def find_data(html):
    lst=[]
    
    regexp = re.compile('<p class="lid">.*?<div class="article_info">', flags = re.U | re.DOTALL)
    lst = regexp.findall(html)

    reg_clean_0 = re.compile('<.*?>', flags = re.U | re.DOTALL)
    reg_clean_1 = re.compile('\t', flags = re.U | re.DOTALL)
    reg_clean_2 = re.compile('\n', flags = re.U | re.DOTALL)
    reg_clean_3 = re.compile('&.*?;', flags = re.U | re.DOTALL)
        
    t = reg_clean_0.sub(" ", lst[0])
    t = reg_clean_1.sub("", t)
    t = reg_clean_2.sub("", t)
    t = reg_clean_3.sub("", t)

    return t

def find_words(text):
    regexp = re.compile('[a-zA-Zа-яА-Я0-9-]+', flags = re.U | re.DOTALL)
    lst = regexp.findall(text)
    
    for i in range(len(lst)):
        lst[i] = lst[i].lower()

    s=[]
    for word in lst:
        ana = morph.parse(word)[0]
        lemma = ana.normal_form
        s.append(lemma)     
    return sorted(s)

def renew_dct(lst, dct):
    for i in lst:
        if i not in dct:
            dct[i]=1
        else:
            dct[i]+=1
    return dct

def find_top10(dct): 
    dct_srt = set(dct.values())
    dct_srt = sorted(dct_srt)
    dct_srt = dct_srt[len(dct_srt):len(dct_srt)-11:-1]   
    flst = []
    for key in dct:
        if dct[key] in dct_srt:
            flst.append([dct[key], key])
    flst = sorted(flst)
    for i in flst:
        i[0], i[1] = i[1], i[0]
    return flst 

def find_urls(html):
    regexp = re.compile('<ul class="big_listing">.*?</ul>', flags = re.U | re.DOTALL)
    lst = regexp.findall(html)

    regexp = re.compile('<a href="http://www.mk.ru/culture.*?.html"', flags = re.U | re.DOTALL)
    lst = regexp.findall(lst[0])

    reg_clean_0 = re.compile('<a href="', flags = re.U | re.DOTALL)
    reg_clean_1 = re.compile('"', flags = re.U | re.DOTALL)
    
    for i in range(len(lst)):
        j = lst[i]
        t = reg_clean_0.sub("", j)
        t = reg_clean_1.sub("", t)
        lst[i] = t

    lst = set(lst)
    return list(sorted(lst))

def today_is():
    now = str(datetime.datetime.now()).split(' ')[0]
    now = now.split('-')
    return now

def find_beg_day(s):
    today = today_is()
    beg_day = today
    if s == 'w':
        beg_day[2] = str((30+int(today[2])-7)%30) 
        if len(beg_day[2])==1:
            beg_day[2] = '0'+beg_day[2]
    else:
        beg_day[1] = str((12 + int(today[1])-1)%12)
        if len(beg_day[1])==1:
            beg_day[1] = '0'+beg_day[1]
    return beg_day

def download_articles(period):
    common_url='http://www.mk.ru/culture/%s/%s/%s/'
    if period == 7:
        s = 'w'
    else:
        s = 'm'
    beg_day = find_beg_day(s)

    urls=[]
    ct=0
    d = beg_day[2]
    m = beg_day[1]
    while ct != period:
        d = str((31+int(d)+1)%31)
        if len(d)==1:
            d = '0'+d
        if d=='00':
            d = '31'
                
        if d == '01':
            m = str(int(m)+1)
        if len(m)==1:
                m = '0'+m
        
        main_url = common_url%('2017', m, d)
        ct += 1
        html = download_page(main_url)
        if html != None: 
            local_urls = find_urls(html)
            urls.extend(local_urls)
    return urls

def make_top_list(period):
    urls = download_articles(period)
    dct={}
    for url in urls:
        html = download_page(url)
        if html != None:
            text = find_data(html)
            lst = find_words(text)
            dct = renew_dct(lst, dct)
    top_lst = find_top10(dct)
    return top_lst

app = Flask(__name__)

@app.route('/')
def index():
    urls = {'Главная страница': url_for('index'),
            'Данные за 3 дня': url_for('month'),    
            'Данные за 1 день': url_for('week')     
            }
    return render_template('index.html', urls=urls)

#вместо месяца взяты 3 дня, т.к. heroku не справляется 
@app.route('/month')    
def month():
    top_list_m = make_top_list(3)   #чтобы получить данные за месяц - запустить make_top_list(30)
    data = [['слово', 'частотность']]
    data.extend(top_list_m)
    return render_template('month.html', mytable=json.dumps(data), url=url_for('index'))

#вместо недели взят 1 день, т.к. heroku не справляется 
@app.route('/week')
def week():
    top_list_w = make_top_list(1)   #чтобы получить данные за неделю - запустить make_top_list(7) - работает на домашнем сервере, из питона 
    data = [['слово', 'частотность']]
    data.extend(top_list_w)
    return render_template('week.html', mytable=json.dumps(data), url=url_for('index'))

if __name__ == '__main__':
    import os
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
