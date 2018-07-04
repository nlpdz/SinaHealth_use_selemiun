# -*- coding: UTF-8 -*-
#养生 <a target="_blank" href="(.*?)" class="pic_link">
#关注 <a href="(.*?)" class="pic_link">
#食品 <a target="_blank" href="(.*?)" class="pic_link">
#医美 <a target="_blank" href="(.*?)" class="pic_link">
#基因 <a target="_blank" href="(.*?)" class="pic_link">

import sys
import urllib2
import urllib
import threading
import re
import thread
import Queue
import time
import selenium.webdriver.phantomjs
import selenium.webdriver
import selenium.webdriver.support.wait
import MySQLdb
import random
from bs4 import BeautifulSoup
from Tkinter import *

#放置链接的队列
q=Queue.Queue()
#放置源码
content=''

t_info = Tk()
t_info.geometry('500x400+300+300')
t_info.title('爬虫程序')
t_content=Tk()
t_content.geometry('640x360+300+300')
t_content.title('爬虫程序')
lb=Listbox(t_info,width=60,height=10)
t_title=Text(t_info,width=30,height=1)
t_time=Text(t_info,width=30,height=1)
t_source=Text(t_info,width=30,height=1)
t_text=Text(t_content)

#连接数据库
conn= MySQLdb.connect(
            host='localhost',
            port = 3306,
            user= 'root',
            passwd= '123456',
            db = 'test',
            charset='utf8',
            )
print '数据库连接成功！'

# 创建游标
cur = conn.cursor()

def info():
    t_info.mainloop()

def contents():
    t_content.update()
    t_content.mainloop()



#初始化driver
def init():
    global articleDriver
    articleDriver = selenium.webdriver.Firefox()
    global driver
    driver = selenium.webdriver.Firefox()
    print '模拟浏览器启动成功！'
    print "初始化完成！\n"

#关闭driver
def stopDriver():
    global driver
    driver.close()
    driver.quit()
    global articleDriver
    articleDriver.close()
    articleDriver.quit()



#获取网页源码，更新全局 变量Content
def getContent(url):
    global driver
    driver.get(url)
    print('get page source from ' + url)
    print("加载完成")

#下拉页面
def movePage():
    global driver
    js="var q=document.documentElement.scrollTop=10000"
    driver.execute_script(js)
    time.sleep(5)
    driver.execute_script(js)
    time.sleep(5)
    js="var q=document.documentElement.scrollTop=5500"
    driver.execute_script(js)
    time.sleep(5)

#获取Content中的链接，并将链接放入QUeue
def getLinks():
    content = driver.page_source
    #print content
    pattern = re.compile('<h2><a href="(.*?)" target="_blank">.*?</a></h2>')
    items = re.findall(pattern, content)
    for item in items:
        #print(item)
        q.put(item)
    print '队列长度为'+str(len(items))

#根据Queue中的链接获取文章内容
def getArticle(url):
    title=''
    text=''
    source=''
    time=''
    img=''
    print('get article from ' + url)
    lb.insert(END, url)
    global articleDriver
    try:
        articleDriver.get(url)
    except Exception as e:
        print("加载超时")
        articleDriver.close()
        articleDriver = selenium.webdriver.Firefox()
        return
    content = articleDriver.page_source
    #标题
    title_pattern = re.compile('<h1 id="main_title">(.*?)</h1>', re.S)
    title_items = re.findall(title_pattern, content)
    for item in title_items:
        title=item
    if title=='':
        title_pattern = re.compile('<h1 id="artibodyTitle".*?>(.*?)</h1>', re.S)
        title_items = re.findall(title_pattern, content)
        for item in title_items:
            title = item
    #print("------------------------------------------------")
    #主体
    text_pattern=re.compile('<p>(.*?)</p>', re.S)
    text_items=re.findall(text_pattern, content)
    regex = re.compile("</?[^>]+>", re.S)
    for item in text_items:
        item = regex.sub('', item)
        item = re.sub(r'\n', '', item)
        text=text+item+'\n'
    text = text.strip()

    #print(text)
    #print("------------------------------------------------")
    #时间
    time_pattern=re.compile('<span class="titer">(.*?)</span>', re.S)
    time_item=re.findall(time_pattern,content)
    for item in time_item:
        time=item

        #print(item)
    if time=='':
        time_pattern = re.compile('<span id="pub_date">(.*?)</span>', re.S)
        time_item = re.findall(time_pattern, content)
        for item in time_item:
            time = item

            #print(item)
    #来源
    source_pattern = re.compile('<span class="source"><a href.*?>(.*?)</a>.*?</span>')
    source_item=re.findall(source_pattern,content)
    for item in source_item:
        source = item
    if source == '':
        source_pattern = re.compile('<a href=.*?data-sudaclick="media_name".*?>(.*?)</a>')
        source_item = re.findall(source_pattern, content)
        for item in source_item:
            source = item
    if source == '':
        source_pattern = re.compile('<span class="source">(.*?)</span>')
        source_item = re.findall(source_pattern, content)
        for item in source_item:
            source = item
        if source == '':
            source_pattern = re.compile('<span class="fred">(.*?)</span>')
            source_item = re.findall(source_pattern, content)
            for item in source_item:
                source = item
    #图片
    img_pattern = re.compile('<div class="img_wrapper">.*?<img src="(.*?)" alt.*?>.*?</div>')
    img_item = re.findall(img_pattern, content)
    for item in img_item:
        img = item
        #print("图片 "+item)
    #插入数据库
    insertIntoDB(url, title, text, time, source, img)
    print("title: "+title)
    print("time: " + time+" source: "+source)
    print("img:"+img)
    print("已存入数据库")
    t_title.delete(1.0,2.0)
    t_time.delete(1.0,2.0)
    t_source.delete(1.0,2.0)
    Label(t_info, text='文章标题').grid(row=5, column=0, sticky=W)
    t_title.insert(1.0,title)
    t_title.grid(row=6, column=0, sticky=W)
    Label(t_info, text='发布时间').grid(row=3, column=0, sticky=W)
    t_time.insert(1.0,time)
    t_time.grid(row=4, column=0, sticky=W)
    t_text.insert(1.0,text)
    t_text.grid(row=0,column=0,sticky=W)
    Label(t_info, text='文章来源').grid(row=7, column=0, sticky=W)
    t_source.insert(1.0,source)
    t_source.grid(row=8,column=0,sticky=W)
    t_title.update()
    t_time.update()
    t_source.update()
    saveImg(img,title)

#保存图片
def saveImg(imgURL,title):
    if imgURL != '':
        try:
            req = urllib2.Request(imgURL)
            u = urllib2.urlopen(req)
            data = u.read()
        except Exception as e:
            if hasattr(e, "code"):
                print(e.code)
            if hasattr(e, "reason"):
                print(e.reason)
        f=open('D:/vain/Python/sina_img/'+title+'.jpg','wb')
        print "保存成功！\n"
        f.write(data)
        f.close()


#刷新网页，更新全局变量Content
def nextPage():
    global driver
    button = driver.find_element_by_class_name("pagebox_next")
    button.click()
    time.sleep(5)
    global content
    content = driver.page_source

#下5页
def next5Page():
    global driver
    #button=driver.find_element_by_class_name("pagebox_next")
    button = driver.find_element_by_link_text('下5页')
    button.click()
    time.sleep(5)
    global content
    content=driver.page_source

#判断是否是最后一页
def isLastPage():
    global content
    pattern = re.compile('<a href.*?>下一页</a>', re.S)
    items = re.findall(pattern, content)
    if items!= []:
        print("不是最后一页")
        return False
    else:
        print("已是最后一页")
        return True

#跳转到最后一页
def getLastPage():
    global driver
    button = driver.find_element_by_xpath(r'//div[@id="pageZone"]/span[6]')
    button.click()
    time.sleep(5)
    global content
    content = driver.page_source

#插入数据库
def insertIntoDB(url,title,text,time,source,img):
    insert = 'insert into sina values(%s,%s,%s,%s,%s,%s)'
    cur.execute(insert, [url, title, text, time, source, img])
    conn.commit()



#关闭数据库
def closeDB():
    cur.close()
    conn.close()



def getArticleInThread():
    while q.empty() == False:
        link = q.get()
        print("正在获取来自"+link+"的文章")
        getArticle(link)
        snap = 3 + random.randint(0, 2)
        print("睡眠" + str(snap) + "秒")
        time.sleep(snap)

def main():
    init()
    getContent('http://health.sina.com.cn/healthcare/')
    file = open('D:/vain/Python/sina.txt', 'r')
    page=file.read()
    file.close()
    page=int(page)
    count = page
    cycle_5=page/5
    page=page%5
    item_num=0;
    while cycle_5>1:
        movePage()
        next5Page()
        cycle_5=cycle_5-1
    while page>0:
        movePage() #将页面向下拉动两次
        nextPage() #点击下一页
        page=page-1
    while(True):
        count = count + 1;
        Label(t_info,text='———------—正在爬取第'+str(count)+'页—----—————').grid(row=0,column=0,sticky=W)
        print("————------—正在爬取第"+str(count)+"页—----———————")
        f = open('D:/vain/Python/sina.txt', 'w')
        f.write(str(count))
        f.close()
        movePage()
        getLinks()
        print("开始获取文章内容")
        Label(t_info,text='已爬取的链接').grid(row=1,column=0,sticky=W)
        while q.empty() == False:
            link = q.get()
            item_num=item_num+1
            print("第"+str(count)+"页，第"+str(item_num)+"条")
            getArticle(link)
            snap=3+random.randint(0,2)
            print("睡眠" + str(snap) + "秒")
            time.sleep(snap)
            lb.grid(row=2)
            t_info.update()
        item_num=0
        print("-----------------------第" + str(count) + "页结束——————————————")
        if count==2:
            break;
        time.sleep(30)
        nextPage()
    stopDriver()
    closeDB()
    print("——————————共爬取了"+str(count)+"页——————————————")

if __name__ == '__main__':
    main()