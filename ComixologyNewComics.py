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

@func_timeout.func_set_timeout(30)#添加func_set_timeout(2)的装饰器，参数2表示超时时间，此处设置为2s。
def askChoice(slogan):#将需要询问的内容封装进一个函数
    inputs = input(f'{slogan}\n')
    return inputs
#程序执行时先调用askChoice函数，并开始计时。
#若用户在计时期间内输入，则正常传参
#若用户超时，则触发func_timeout.exceptions.FunctionTimedOut异常，try...except捕捉异常，并进行后续操作。
 
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

def getKey(dct, value):
  return [k for (k,v) in dct.items() if v == value][0]#字典中根据值倒查键

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

def validate(dateText):
    dateText = re.sub(r'[^0-9\s/-]','',dateText)#保留
    if dateText != '':
        try:
            if re.search('[\s/-]',dateText):
                if '/' in dateText:
                    timeZone = [timeZone.strip() for timeZone in dateText.split('/') if timeZone.strip() != '']
                elif '-' in dateText:#匹配2020/01/01
                    timeZone = [timeZone.strip() for timeZone in dateText.split('-') if timeZone.strip() != '']
                elif ' ' in dateText:
                    timeZone = [timeZone.strip() for timeZone in dateText.split(' ') if timeZone.strip() != '']
                if len(timeZone[0]) == 2:#若年份是2位数，补全成20**
                    year = time.strftime('%Y',time.strptime(timeZone[0], '%y'))
                else:
                    year = timeZone[0]
                if len(timeZone) < 3:
                    date = datetime(int(year), int(timeZone[1]), 1).strftime('%Y-%m-%d')
                else:
                    date = datetime(int(year), int(timeZone[1]), int(timeZone[2])).strftime('%Y-%m-%d')#格式化成20200101后转成2020-01-01
            elif dateText.isdigit():
                if len(dateText) == 8:
                    date = time.strftime('%Y-%m-%d',time.strptime(dateText, '%Y%m%d'))
                elif len(dateText) == 6:
                    try:
                        try:
                            date = time.strftime('%Y-%m-%d',time.strptime(dateText, '%y%m%d'))
                        except:
                            date = time.strftime('%Y-%m-%d',time.strptime(dateText, '%Y%m%d'))
                    except:
                        date = time.strftime('%Y-%m-%d',time.strptime(dateText, '%Y%m'))
                else:
                    strList = list(dateText)#匹配2020111 7位日期
                    insertZero = strList.index(dateText[4])#提取年份2020
                    strList.insert(insertZero,'0')#第5位（月份）前补充一个0转成20200111
                    date = time.strftime('%Y-%m-%d',time.strptime(''.join(strList), '%Y%m%d'))#按20200101格式匹配
        except:# ValueError:
            date = validate(input())#排除手误情况，重新输入
    else:
        date = time.strftime('%Y-%m-%d')#默认今天
    return date

def Group(group, urlLists = list()):
    if group == '1':#添加一个默认选项，爬取今天（本周）
        urlLists.append(f"https://www.comixology.com/new-comics/{time.strftime('%Y-%m-%d')}")
        print(f"Today is {time.strftime('%Y/%m/%d')}")
    elif group == '2':
        try:
            Date = askChoice("Back to?")#判断是按周还是按月爬取 .lower()转小写
            if Date.isdigit():
                Date = int(Date)
            elif Date == 'm':
                Date = int(time.strftime('%d'))-1#本月初至今
            else:
                Date = 28 #错填默认4周
        except func_timeout.exceptions.FunctionTimedOut as e:
            Date = 28 #超时则默认4周
        print(f"Begin with {(datetime.now()-timedelta(days=Date)).strftime('%Y/%m/%d')}")
        
        if Date == 30 or Date == 31:
            urlLists.append(f'https://www.comixology.com/new-comics')
        else:
            for i in range (0, Date+1):
                urlLists.append(f"https://www.comixology.com/new-comics/{(datetime.now()-timedelta(days=int(i))).strftime('%Y-%m-%d')}")#返回‘YYYY-MM-DD’格式的日期字符串
    elif group == "3":
        try:
            Ends = validate(askChoice('Begin with '))#比较过去的日期
            EndDate = -(datetime.strptime(Ends,'%Y-%m-%d')-datetime.now()).days
            #-datetime.strptime(date.today().isoformat(),'%Y-%m-%d')).days
        except func_timeout.exceptions.FunctionTimedOut as e:
            EndDate = 0
        try:
            Starts = validate(askChoice('End with '))#比较靠近现在的日期
            StartDate = -(datetime.strptime(Starts,'%Y-%m-%d')-datetime.now()).days
        except func_timeout.exceptions.FunctionTimedOut as e:
            StartDate = 1
        if EndDate < StartDate:#结束日期必须 大于 开始日期
            StartDate = EndDate
            EndDate = StartDate + 99
        if EndDate == '' or EndDate == StartDate:#如果结束日期为空，那划定一个99天的范围
            EndDate = StartDate + 99
        if EndDate < 0:#排除未来日期
            EndDate = 0
        if StartDate < 0:#排除未来日期
            StartDate = 0
        NewStartDate = (datetime.now()-timedelta(days=StartDate-1)).strftime('%Y/%m/%d')#经过上面排除错误值之后得出的新值
        NewEndDate = (datetime.now()-timedelta(days=EndDate-1)).strftime('%Y/%m/%d')
        print(f'From {NewEndDate} to {NewStartDate}, {EndDate - StartDate} day(s)')
        for i in range (StartDate - 1, EndDate):
            urlLists.append(f"https://www.comixology.com/new-comics/{(datetime.now()-timedelta(days=int(i))).strftime('%Y-%m-%d')}")
    else:
        exit()
    return urlLists

def output(url):#文件输出路径
    fpath = re.sub('.*comixology.com/','',url).replace('-', '_')
    fpath = re.sub('(\?|&).*','',fpath)#删除页码
    fpath = re.sub('[A-Z]',lambda x:' '+x.group(0),fpath).title()#首字母大写
    #fpath = re.sub('_(\d+)',lambda x: x.group(1),fpath)#删除页码然后拼接
    fpath = fpath.replace('=', '').replace('_', '').replace(' ', '')#删除数字前的空格
    outputPath = f'/content/drive/My Drive/{fpath}.csv'
    if not os.path.exists(os.path.dirname(outputPath)):
        os.makedirs(os.path.dirname(outputPath))
    print(f'File will be saved in {fpath}.csv')
    return outputPath

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
 
def getList(url, urlList = list()):
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    url = cleanLink(url)
    pageHtml = getHTMLText_with_retry(url, 'uft-8')
    dom_tree = h.fromstring(pageHtml.content)
    urlList.append(url)
    a = dom_tree.xpath("//a[contains(@class,'all-link')]/@href")
    if a != '':
        for link in a: 
            urlList.append(cleanLink(link))
    else:
        pass
    return urlList
 
def getListPlus(url, urlLists = list()):
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    pageHtml = getHTMLText_with_retry(url, 'uft-8')
    dom_tree = h.fromstring(pageHtml.content)
    #<class 'lxml.html.HtmlElement'>
    #解析成xml
    a = dom_tree.xpath("//a[contains(@class,'pager-link')]")#查找所有页面链接
    #在xml中定位节点，返回的是一个列表
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
        print(f'Only find 1 page,   {len(urlLists)} page(s) in total')
    else:
        pages = []
        urlLists.append(cleanLink(url))
        pages = pages.extend(getList(url))#查找有没View_More展开
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
        print(f'Find {len(pages)} more page(s), {len(urlLists)} page(s) in total')
    return urlLists
 
def getData(item_page_url):
    datas = {
        'item_title':'', 
        'item_description':'', 
        'item_badge':[], 
        'item_publisher':'', 
        'item_credits':[], #其中包括written by、pencils、inks、colored by等信息
        'item_genres':[], 
        'item_abouttext':[]
    }
    #跳转item页面
    page = getHTMLText_with_retry(item_page_url)
    dom_tree = h.fromstring(page.content)
    #获取面包屑导航栏信息
    breadcrumbs = dom_tree.xpath("//div[@id='cmx_breadcrumb']/a")
    breadcrumb_url = cleanLink(breadcrumb.xpath('../a[last()]/@href')[0])#连载对应的系列地址，直接取最后一个元素
    breadcrumb_text = breadcrumb.xpath('../a[last()]//text()')[0])
    #for breadcrumb in breadcrumbs:#用遍历的方法找到最后一个
        #datas['breadcrumb_url'] = cleanLink(breadcrumb.xpath('.//@href')[0])#连载对应的系列地址
        #datas['breadcrumb_text'] = breadcrumb.xpath('.//text()')[0]
    item_title = dom_tree.xpath("//div[@id='column2']/h1[@class='title']/text()")[0]
    datas['item_title'] = html.unescape(item_title.strip()).replace('	',' ').replace('  ',' ')
    #清洗长文本中多余的/r/n空行
    item_description = [description.strip() for description in dom_tree.xpath("//div[@id='column2']/section[@class='item-description']/text()") if description.strip() != '']
    datas['item_description'] = '\n'.join(html.unescape(item_description)).strip().replace('	',' ').replace('  ',' ')
    #可能存在多个badge信息，因此用列表装载
    badges = []
    for badge in dom_tree.xpath("//div[@id='column2']/div[@class='badges']/img[@class='badge']"):
        badges.append(badge.xpath("./@title")[0])
    datas['item_badge'] = badges
    datas['item_publisher'] = ' '.join(html.unescape(dom_tree.xpath("//h3[@title='Publisher']/text()")[0].split()))
    #找credits
    creditList = []
    for credit in dom_tree.xpath("//div[@id='column3']/div[@class='credits']/div[@class='credits']"):
        sub = credit.xpath('.//dt/text()')[0]
        nameList = []
        nameList.append(sub+':') 
        for a in credit.xpath('.//a'):
            if a.xpath('./text()')[0].strip() != 'More...' and a.xpath('./text()')[0].strip() != 'HIDE...':
                nameList.append(a.xpath('./text()')[0].strip())
        creditList.append(nameList)
    datas['item_credits'] = creditList
    genres = []
    for genre in dom_tree.xpath("//div[@id='column3']/div[@class='credits']/a/text()"):
        genres.append(genre.strip())
    datas['item_genres'] = genres
    #直接爬取对应的副标题与对应信息
    subList = []
    for subtitle in dom_tree.xpath("//div[@id='column3']/div[@class='credits']/h4[@class='subtitle']/text()"):
        subList.append(subtitle)
    infoList = []
    for info in dom_tree.xpath("//div[@id='column3']/div[@class='credits']/div[@class='aboutText']/text()"):
        temp = info.strip().replace('\t', '').replace('\n', '')
        infoList.append(temp)
    for i in range(len(subList)):
        datas['item_abouttext'].append(subList[i]+':'+infoList[i])
    return datas
 
def getInfo(urlLists):
    pageNum = 0
    count = 0
    total = 0#翻页累积总数
    totalCount = 0#页面标题中获取的总数
    error = 0
    for url in urlLists:
        pageNum += 1
        currentCount = 0
        page = getHTMLText_with_retry(url)
        dom_tree = h.fromstring(page.content)
        try:
            listTitle = dom_tree.xpath("//h3[contains(@class,'list-title')]/text()")[0]
            try:
                listSubitle = dom_tree.xpath("//h4[contains(@class,'list-subtitle')]/text()")[0]
            except:
                listSubitle = ''
            totalCount = pageTitle(listTitle, listSubitle)
        except:
            totalCount = len(dom_tree.xpath("//li[@class='content-item']"))
            pass
        currentPageCount = len(dom_tree.xpath("//li[@class='content-item']"))
        if total + currentPageCount <= totalCount:#比较翻页累积数和页面标题中的总数
            total = totalCount
        else:
            total += currentPageCount
        print(f'{currentPageCount}/{total}	Now Processing Page {pageNum}: {url}', end = ' ')
        outputPath = output(url)
        for item in dom_tree.xpath("//li[@class='content-item']"):
            count += 1
            currentCount += 1
            try:
                #所需要的元素
                data = {
                    'code':'',
                    'item_page_url':'', 
                    'cover_url':'', 
                    'title':'', 
                    'subtitle':'', 
                    'price':'', 
                    'full_price':'', 
                    'lang':'', 
                    'breadcrumb_url':'', 
                    'breadcrumb_text':'',
                    }
                cover_url = item.xpath(".//img[@class='content-img']/@src")[0]    
                data['cover_url'] = re.sub('_SX.*_QL.*_TTD_','_SX312_QL80_TTD_',cover_url)
                data['title'] = html.unescape(item.xpath(".//h5[contains(@class,'content-title')]/text()")[0]).strip().replace('	',' ').replace('  ',' ')
                #存在没有副标题的情况
                try:
                    data['subtitle'] = html.unescape(item.xpath(".//h6[contains(@class,'content-subtitle')]/text()")[0]).strip().replace('	',' ').replace('  ',' ')
                except:
                    data['subtitle'] = ''
                data['price'] = item.xpath(".//h5[contains(@class,'item-price')]/text()")[0]
                #存在没有full_price的情况
                try:
                    data['full_price'] = item.xpath(".//h6[contains(@class,'full-price')]/text()")[0]
                except:
                    data['full_price'] = data['price']
                #语种
                try:
                    data['lang'] = item.xpath(".//img[@class='badge']/@title")[0]
                except:
                    data['lang'] = 'English'
                #获取item下一级页面url
                data['item_page_url'] = item.xpath(".//a[@class='content-details']/@href")[0]
                data['code'] = re.sub('.*digital-comic/','',data['item_page_url'])#替换成Code形式
                # Get info from item page url
                subData = getData(data['item_page_url'])
                datas = {**data, **subData}
                print(datas)
                #将字典各value按顺序写出
                CMXInfoList = [value for value in datas.values()]
                with open(outputPath, 'at', encoding = 'utf-8', newline = '') as csvfile:
                    print(f"No.{count}	{datas['item_title']}, {datas['item_publisher']}")
                    writer = csv.writer(csvfile)
                    writer.writerow(CMXInfoList)
            except:
                error += 1
                retryList = []
                item_page_url = item.xpath("//a[@class='content-details']/@href")[0]
                try:
                    bundle = re.compile(r'/bundle/')#检查是否为套装页
                    if bundle.search(item_page_url):
                        retryList.append(item_page_url)
                        print(f'Find bundle: {item_page_url}')
                except:# Exception as e:
                    #print(e)
                    count = count - currentCount
                    retryList.append(url)
                    print(f'{error}/{currentCount}/{count}	Err: {item_page_url}, turn to RetryList')
                getInfo(retryList)
                time.sleep(1)
                continue

if __name__ == "__main__":
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    start_time = time.time()
    try:
        print(f'''----------------------------------------
1 今天是{time.strftime('%Y/%m/%d 第%W周 星期%w')}
2 过去几天
  m 月初1号至今{int(time.strftime('%d'))}天 / ' {(datetime.now()-timedelta(days=30)).strftime('%Y/%m/%d')}至今30天 
3 指定范围''')
        group = askChoice("请输入分组：")#判断是按周还是按月爬取
    except func_timeout.exceptions.FunctionTimedOut as e:
        group = "1"#超时则默认当天
    urls = Group(group)
    Links = []
    for url in urls:#查找View_More
        print(f'Processing {url}\r', end = '')
        Links.extend(getList(url))
        Links = sortList(flatten(list(set(Links))))
    print(f'Find {len(Links)} more page(s) can View_More\n')#查找到View_More
    Pages = []
    for Link in Links:#再对每个页面进行翻页
        print(f'\rProcessing {Link}', end = ' ')
        Pages.extend(getListPlus(Link))
        Pages = sortList(flatten(list(set(Pages))))#按页码排序
    print(f'Find {len(Pages)} page(s) at all\n')
    getInfo(Pages)
    print(f"Finish Time: {datetime.fromtimestamp(time.time()-start_time).strftime('%-H:%-M:%-S.%f')}")#加短横线-省略多余前置0
    exit()
