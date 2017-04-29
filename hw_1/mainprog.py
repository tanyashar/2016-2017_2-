import requests
import json
import re
import matplotlib.pyplot as plt
from matplotlib import style
style.use('ggplot') 

from collections import Counter

def vk_api(method, **kwargs):
    api_request = 'https://api.vk.com/method/'+method + '?'
    api_request += '&'.join(['{}={}'.format(key, kwargs[key]) for key in kwargs])
    return json.loads(requests.get(api_request).text)

def count_words(text):
    regexp = re.compile('[а-яА-Я-]+', flags = re.U | re.DOTALL)
    lst = regexp.findall(text)
    return len(lst)

def find_age(lst, day, month, year):  
    for i in range(len(lst)):
        lst[i] = int(lst[i])
    if (lst[1] < month) or (lst[1] == month and lst[0] <= day):
        age = year-lst[2]
    else: age = year-lst[2]-1     
    return age

#tvrain
group_info = vk_api('groups.getById', group_id='public.cinemaholics', v='5.63')
group_id = group_info['response'][0]['id']  #узнаем общую информацию о группе

f = open('posts.txt', 'w', encoding='utf-8')
posts = []
posts_amount = 300
while len(posts) < posts_amount:
    result = vk_api('wall.get', owner_id=-group_id, v='5.63', count=100, offset=len(posts))
    posts += result['response']["items"]

for i in posts:
    print(i, file=f)
f.close() #скачиваем посты, выводим их в файл posts.txt 

post_com={}
age_com={}
city_com={}
age_post={}
city_post={}

f=open('comments.txt', 'w', encoding='utf-8')
fout=open('user_info.txt', 'w', encoding='utf-8')
for i in posts:
    post_id = i['id']    
    length_post = count_words(i['text'])

    signer_id=''
    if 'signer_id' in i:
        signer_id = i['signer_id']
        result = vk_api('users.get', uids=signer_id, fields='bdate,city')
        dct = result['response']
    
        if len(dct)!=0:
            dct = dct[0]
            
        age=0
        if 'bdate' in dct:
            bdate = dct['bdate']
            lst = bdate.split('.')
            age=0
            if len(lst) == 3:
                age = find_age(lst, 1, 5, 2017)

                if age in age_post:
                    age_post[age][0] += length_post
                    age_post[age][1] += 1
                else:
                    age_post[age] = [length_post, 1]
            
        if 'city' in dct:
            city = dct['city']
            if city in city_post:
                city_post[city][0] += length_post
                city_post[city][1] += 1
            else:
                city_post[city] = [length_post, 1]
    
    comments = []
    comments_amount = 300
    while len(comments) < comments_amount:
        result = vk_api('wall.getComments', owner_id=-group_id, post_id=post_id, v='5.63', count=100, offset=len(comments))  
        comments += result['response']["items"]
        if len(result['response']["items"]) < 100:
            break
    print(comments, file=f)

    ccl_post=0 #средняя длина комментария
    for j in comments:
        length_com = count_words(j['text'])
        ccl_post += length_com

        user_id = j['from_id']
        result = vk_api('users.get', uids=user_id, fields='bdate,city')
        dct = result['response']
        if len(dct)!=0:
            dct = dct[0]
        print(result, file=fout) #социолингв информация о пользователе        

        age=0
        if 'bdate' in dct:
            bdate = dct['bdate']
            lst = bdate.split('.')
            if len(lst) == 3:
                age = find_age(lst, 1, 5, 2017)

                if age in age_com:
                    age_com[age][0] += length_com
                    age_com[age][1] += 1
                else:
                    age_com[age] = [length_com, 1]
                
        if 'city' in dct:
            city = dct['city']
            if city in city_com:
                city_com[city][0] += length_com
                city_com[city][1] += 1
            else:
                city_com[city] = [length_com, 1]
        
    if len(comments) != 0:
        ccl_post //= len(comments)

    if length_post in post_com:
        post_com[length_post][0] += ccl_post
        post_com[length_post][1] += 1
    else:
        post_com[length_post] = [ccl_post, 1]
    
f.close()
fout.close()


city_com_lst=[]
for key in city_com:
    if key == 0:
        continue
    mittel = city_com[key][0]//city_com[key][1]

    result = vk_api('database.getCitiesById', city_ids=str(key), v='5.63', count=10, offset=len(posts))
    city = ''
    if len(result['response']) != 0:
        city = result['response'][0]['title']
    city_com_lst += [(mittel, city)]
city_com_lst = sorted(city_com_lst)

city_post_lst=[]
for key in city_post:
    if key == 0:
        continue
    mittel = city_post[key][0]//city_post[key][1]

    result = vk_api('database.getCitiesById', city_ids=str(key), v='5.63', count=10, offset=len(posts))
    city = ''
    if len(result['response']) != 0:
        city = result['response'][0]['title']
    city_post_lst += [(mittel, city)]
city_post_lst = sorted(city_post_lst)

age_com_lst=[]
for key in age_com:
    mittel = age_com[key][0]//age_com[key][1]
    age_com_lst += [(key, mittel)]
age_com_lst = sorted(age_com_lst)

age_post_lst=[]
for key in age_post:
    mittel = age_post[key][0]//age_post[key][1]
    age_post_lst += [(key, mittel)]
age_post_lst = sorted(age_post_lst)

post_com_lst=[]
for key in post_com:
    mittel = post_com[key][0]//post_com[key][1]
    post_com_lst += [(key, mittel)]
post_com_lst = sorted(post_com_lst)

print('len(city_com_lst)', len(city_com_lst))
city_com_lst = city_com_lst[len(city_com_lst)-1:len(city_com_lst)-51:-1]
plt.figure(figsize=(20,10))
plt.bar(range(len(city_com_lst)), [i[0] for i in city_com_lst], label='коммент vs. город')
plt.xticks(range(len(city_com_lst)), [i[1] for i in city_com_lst], rotation='vertical')
plt.xlabel('город')
plt.ylabel('среднее кол-во слов')
plt.legend()
plt.show()
plt.savefig('my_graph_1.pdf')

plt.figure(figsize=(20,10))
plt.bar(range(len(city_post_lst)), [i[0] for i in city_post_lst], label='пост vs. город')
plt.xticks(range(len(city_post_lst)), [i[1] for i in city_post_lst], rotation='vertical')
plt.xlabel('город')
plt.ylabel('среднее кол-во слов')
plt.legend()
plt.show()
plt.savefig('my_graph_2.pdf')

plt.figure(figsize=(20,10))
plt.bar(range(len(age_com_lst)), [i[1] for i in age_com_lst], label='коммент vs. возраст')
plt.xticks(range(len(age_com_lst)), [i[0] for i in age_com_lst], rotation='vertical')
plt.xlabel('возраст')
plt.ylabel('среднее кол-во слов')
plt.legend()
plt.show()
plt.savefig('my_graph_3.pdf')

plt.figure(figsize=(20,10))
plt.bar(range(len(age_post_lst)), [i[1] for i in age_post_lst], label='пост vs. возраст')
plt.xticks(range(len(age_post_lst)), [i[0] for i in age_post_lst], rotation='vertical')
plt.xlabel('возраст')
plt.ylabel('среднее кол-во слов')
plt.legend()
plt.show()
plt.savefig('my_graph_4.pdf')

plt.figure(figsize=(20,10))
plt.plot(range(len(post_com_lst)), [i[1] for i in post_com_lst], color='c', label='пост vs. комментарий')
plt.xticks(range(len(post_com_lst)), [i[0] for i in post_com_lst], rotation='vertical')
plt.xlabel('среднее кол-во слов в комментарии')
plt.ylabel('среднее кол-во слов в посте')
plt.legend()
plt.show()
plt.savefig('my_graph_5.pdf')
