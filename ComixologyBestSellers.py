#!/usr/bin/python
#coding=utf-8
!pip install -U fake-useragent
!pip install -U func_timeout
from bs4 import BeautifulSoup
from lxml import html as h
from fake_useragent import UserAgent
from google.colab import drive
from math import ceil
from posixpath import normpath
from urllib.parse import urlencode, urljoin, urlparse, urlparse, urlunparse
from datetime import date, datetime, timedelta
import pandas as pd
import csv, func_timeout, html, os.path, pickle, re, requests, string, time
 
#drive.mount('/content/drive')
print(str(UserAgent().random))
 
def getHTMLText(url, code = 'utf-8'):
    Headers = {'User-Agent':str(UserAgent().random)}
    r = requests.get(url, headers = Headers, timeout = 30)
    r.raise_for_status()
    r.encoding = code
    return r
 
def getHTMLText_with_retry(url, code = 'utf-8', retry = 10):
    for i in range(retry):
        try:
            request_text = getHTMLText(url, code='utf-8')
            return request_text
        except Exception as e:
            print(f'网页访问失败: {e}')
        if i > 5:
            time.sleep(10)
    print(f'Load {url} failed 10 times')
    return ''
 
def cleanLink(link):
    link = re.sub('\?ref=.*', '', link)#remove ?ref=
    attrs = re.compile(r'lang=\d+|cu=\d+')# clean cu = 0, avoid different link for same page
    link = attrs.sub('',link)
    while link.endswith('?') or link.endswith('&'):
        link = link[:-1]
    return link
 
def newUrl(base, url):
    url1 = urljoin(base, url)
    arr = urlparse(url1)
    path = normpath(arr[2])
    return urlunparse((arr.scheme, arr.netloc, path, arr.params, arr.query, arr.fragment))
 
def embNumbers(s):
    re_digits = re.compile(r'(\d+)')
    pieces = re_digits.split(s)
    pieces[1::2] = map(int,pieces[1::2])    
    return pieces
 
def sortList(alist):#sort_strings_with_embNumbers
    aux = [(embNumbers(s),s) for s in alist]
    aux.sort()
    return [s for __,s in aux]
#没搞懂，按https://www.cnblogs.com/ajianbeyourself/p/5395653.html，找机会用key替换掉DSU排序
 
def getListPlus(url, urlLists = list()):
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    pageHtml = getHTMLText_with_retry(url, 'uft-8')
    dom_tree = h.fromstring(pageHtml.content)
    a = dom_tree.xpath("//a[contains(@class,'pager-link')]")#查找所有页面链接
    try:
        listTitle = dom_tree.xpath("//h3[contains(@class,'list-title')]/text()")[0]
        try:
            listSubitle = dom_tree.xpath("//h4[contains(@class,'list-subtitle')]/text()")[0]
        except:
            listSubitle = ''
        pageTitle(listTitle, listSubitle)
    except:
        pass
    if len(a) == 0: # 如果只有一页
        if url not in urlLists:
            urlLists.append(cleanLink(url))
    else:
        pages = []
        #urlLists.append(cleanLink(url))
        # Get all existing page link
        pages = [a[aElement].attrib['href'] for aElement in range(len(a))]
        # For total page > 5, some page is hidden
        lastPages = [a[aElement].attrib['href'] for aElement in range(len(a)) if a[aElement].text == 'Last']# links[index]返回的是一个字典
        # generate page for hidden page
        for lastPage in lastPages:
            result = re.match('(.*_pg=)(\d+)', lastPage)
            basePath = result.group(1)
            pageNum = int(result.group(2))
            #print(f'path {basePath} {pageNum}')
            pages.extend([f'{basePath}{i+1}' for i in range(pageNum)])
        pages = [cleanLink(newUrl(url, link)) for link in pages]#拼接网址
        bundle = re.compile(r'/bundle/')#目前无法解决爬取套装页，先剔除
        pages = [link for link in pages if not bundle.search(link)]
        pages = sortList(flatten(list(set(pages))))
        urlLists.extend(pages)
    return urlLists

def cleanTitle(title):
    if '(of' in title:
        name = re.search('(.*)#(\d+) \(of (\d+)', title)
        if len(name.group(2)) < 2:
            issue = name.group(2).zfill(2)
        else:
            issue = name.group(2)
        if len(name.group(3)) < 2:
            total = name.group(3).zfill(2)
        else:
            total = name.group(3)
        title = f'{name.group(1)}{issue} (of {total})'
    if '#' in title:
        #((\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?)
        try:
            name = re.search('(.*)#(\d+)(\..*)?', title)
            if len(name.group(2)) < 3:
                issue = name.group(2).zfill(3)
                if name.group(3) != None and name.group(3) != '':
                    title = f'{name.group(1)}{issue}{name.group(3)}'
                else:
                    title = f'{name.group(1)}{issue}'
            else:
                title = title.replace('#','')
        except:
            title = title.replace('#','')
    if 'Vol. ' in title:
        title = title.replace('Vol. ','Vol.')
    title = re.sub('( \(20.{2,3}\)| \(19.{2,3}\))','',title)
    return title

def getInfo(urlLists):
    count = 0
    for url in urlLists:
        page = getHTMLText_with_retry(url)
        dom_tree = h.fromstring(page.content)
        for item in dom_tree.xpath("//li[@class='content-item']"):
            try:
                count += 1
                title = html.unescape(item.xpath(".//img[@class='content-img']/@title")[0]).strip().replace('   ',' ').replace('  ',' ')
                title = cleanTitle(title)
                if count == 1:
                    print(f'🥇No.{count}	{title}')
                elif count == 2:
                    print(f'🥈No.{count}	{title}')
                elif count == 3:
                    print(f'🥉No.{count}	{title}')
                else:
                    print(f'No.{count}	{title}')
                outputPath = f"/content/drive/My Drive/Best Sellers/{time.strftime('%Y%m%d')}Best Sellers.csv"
                if not os.path.exists(os.path.dirname(outputPath)):
                    os.makedirs(os.path.dirname(outputPath))
                with open(outputPath, 'at', encoding = 'utf-8', newline = '') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([count, title, time.strftime('%Y/%m/%d %-H:%-M:%-S')])
            except:# Exception as e:
                #print(e)
                retryList = []
                count = count - currentCount
                retryList.append(url)
                getInfo(retryList)
                time.sleep(1)
                continue
        print(f'''……
Comixology, {time.strftime('%Y/%m/%d')}
📅 Week of {(datetime.now() - timedelta(days = datetime.now().isoweekday()-3, weeks = 1)).strftime('%m/%d')}~{(datetime.now() - timedelta(days = datetime.now().isoweekday()-3)).strftime('%m/%d')}
''')
 
if __name__ == "__main__":
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    start_time = time.time()
    print(f'''----------------------------------------
今天是{time.strftime('%Y/%m/%d 第%W周 星期%w')}
Processing Best Sellers https://www.comixology.com/comics-best-sellers''')
    Links = []
    Links.extend(getListPlus('https://www.comixology.com/comics-best-sellers'))
    Links = sortList(flatten(list(set(Links))))#按页码排序
    print(f'''Find {len(Links)} page(s)
{(datetime.now() - timedelta(days = datetime.now().isoweekday()-3)).strftime('%Y/%m/%d')} ~{time.strftime('%m/%d')}''')
    getInfo(Links)
    print(f'''
{time.strftime('%Y/%m/%d %-H:%-M')}
Finish Time: {datetime.fromtimestamp(time.time()-start_time).strftime('%-H:%-M:%-S.%f')}''')#加短横线-省略多余前置0
    exit()
