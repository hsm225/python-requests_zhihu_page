# -*- coding:utf-8 -*-
__author__ = 'Administrator'

import requests
import re
import random
import time
from bs4 import BeautifulSoup

#脚本使用的http头部
headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, sdch, br',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Cache-Control':'max-age=0',
        'Connection':'keep-alive',
        'Host':'www.zhihu.com',
        'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36'
    }

def login():
    '知乎登陆函数部分，结果返回带有cookies的session对象和_xsrf值'
    s = requests.Session()
    r = s.get('https://www.zhihu.com/', headers=headers)
    content = r.content
    _xsrf = re.findall('input\stype="hidden"\sname="_xsrf"\svalue="(.*?)"', content)[0]
    url = 'https://www.zhihu.com/captcha.gif?r=' + str(time.time()).split('.')[0] + str(random.randint(101, 1000)) + '&amp;type=login'
    r = s.get(url=url, headers=headers)
    with open('captcha.gif', 'wb') as f:
        f.write(r.content)
    f.close()
    captcha = raw_input('>>>')
    url = 'https://www.zhihu.com/login/email'
    data={
                '_xsrf':_xsrf,
                'captcha':captcha,
                'email':'hsm225@163.com',
                'password':'nanchang123',
                'remember_me':'True'
            }
    r = s.post(url=url, data=data, headers=headers)
    print r.status_code
    print r.text
    s.headers.update({'_xsrf':str(_xsrf)})
    return (s, _xsrf)

def first_page_parse(response):
    '打开知乎页面时，将页面上面所有的答案全部解析出来'
    soup = BeautifulSoup(response, 'lxml')
    # 获取title信息
    question_title = soup.find('title').text.strip()
    print question_title
    # 获取url信息
    question_url = re.findall('url=(.*?)"', str(soup.find('meta', attrs={'http-equiv': 'mobile-agent'}).extract()))[0]
    #print question_url
    print 'x' * 50
    print soup.find_all(tabindex='-1')
    print 'x' * 50
    for answer_item in soup.find_all(tabindex='-1'):
        # 获取答案url
        answer_url = 'https://www.zhihu.com' + answer_item.link['href']
        # 获取答主信息
        if answer_item.find(attrs={'class': 'author-link'}):
            user_info = answer_item.find(attrs={'class': 'author-link'}).text
        else:
            user_info = ' '
        # 获取赞数
        if answer_item.find(attrs={'class': 'count'}):
            praise_num = answer_item.find(attrs={'class': 'count'}).text
        else:
            praise_num = '0'
        # 获取评论数
        comment_info =  unicode(answer_item.find(attrs={'name': 'addcomment'}).text)
        if re.findall('\d*', comment_info)[1]:
            print re.findall('\d*', unicode(answer_item.find(attrs={'name': 'addcomment'}).text).strip())
            comment_num = re.findall('\d*', comment_info)[1]
        else:
            comment_num = '0'
        # 获取答案信息
        answer = answer_item.find(attrs={'class': 'zm-editable-content clearfix'}).text.strip()
        try:
            print "%s\n%s\n%s\n%s\n%s\n" % (answer_url, user_info, praise_num, comment_num, answer)
            print '*' * 50
        except Exception, e:
            print e

def other_page_parse(response):
    '这是对动态加载的页面进行解析'
    more_info = response.content.replace('\/', '/').replace('<\/a>', '</a>').replace('<\/span>', '</span>').replace('<\/i>', '</i>').replace('<\/div>', '</div>').replace('<\/button>', '</button>').replace('\\"', '"')
    print more_info
    answer_info = re.findall('\["(.*?)"\]', more_info)[0]
    soup = BeautifulSoup(answer_info, 'lxml')
    more_info_list = soup.find_all(tabindex='-1')
    for answer_item in more_info_list:
        # 获取答案url
        answer_url = 'https://www.zhihu.com' + str(answer_item.link['href']).replace('\/', '/')
        # 获取答主信息
        if answer_item.find(attrs={'class': 'author-link'}):
            user_info = answer_item.find(attrs={'class': 'author-link'}).text.strip()
        else:
            user_info = ' '
        # 获取赞数
        if answer_item.find(attrs={'class': 'count'}).text:
            praise_num = answer_item.find(attrs={'class': 'count'}).text.strip()
        else:
            praise_num = '0'
        # 获取评论数
        comment_info =  unicode(answer_item.find(attrs={'name': 'addcomment'}).text)
        if re.findall('\d*', comment_info)[1]:
            comment_num = re.findall('\d*', comment_info)[1]
        else:
            comment_num = '0'
        # 获取答案信息
        answer = answer_item.find(attrs={'class': 'zm-editable-content clearfix'})
        try:
            print "%s\n%s\n%s\n%s\n%s\n" % (answer_url, user_info.decode("unicode-escape"), praise_num, comment_num, answer.text.strip('').decode("unicode-escape"))
            print '*' * 50
        except Exception, e:
            print e

def main(url):
    '主函数，输入一个问题url，将这个问题的所有答案爬取出来'
    #url = 'https://www.zhihu.com/question/20899988'
    question_seq = re.findall('question/(\d*)', url)[0]
    #print question_seq
    login_result = login()
    s = login_result[0]
    _xsrf = login_result[1]
    response_1 = s.get(url, headers=headers).content
    print '#' * 50
    first_page_parse(response_1)
    s.headers.update({'X-Xsrftoken':str(_xsrf)})
    i = 10
    formdata = {
        'method':'next',
        'params':'{"url_token":%s,"pagesize":10,"offset":10}' % question_seq
    }
    r = s.post('https://www.zhihu.com/node/QuestionAnswerListV2', headers=headers, data=formdata)
    while r.status_code == 200 and len(r.content) > 200:
        other_page_parse(r)
        i += 10
        formdata = {'method':'next','params':'{"url_token":%s,"pagesize":10,"offset":%s}' % (question_seq, i)}
        print formdata
        r = s.post('https://www.zhihu.com/node/QuestionAnswerListV2', headers=headers, data=formdata)
        j = 0
        while r.status_code != 200 and j < 3:
            try:
                j += 1
                r = s.post('https://www.zhihu.com/node/QuestionAnswerListV2', headers=headers, data=formdata)
            except Exception, e:
                print e

if __name__ == "__main__":
    #url = 'https://www.zhihu.com/question/20899988'
    url = 'https://www.zhihu.com/question/33302064'
    main(url)