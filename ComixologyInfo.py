#!/usr/bin/python
#coding=utf-8
!pip install -U fake-useragent
!pip install -U func_timeout
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from google.colab import drive
from math import ceil
from posixpath import normpath
from urllib.parse import urlencode, urljoin, urlparse, urlparse, urlunparse
from datetime import date, datetime, timedelta
import csv, func_timeout, html, os, re, requests, string, time
 
#drive.mount('/content/drive')
print(str(UserAgent().random))
 
@func_timeout.func_set_timeout(30)#添加func_set_timeout(2)的装饰器，参数2表示超时时间，此处设置为2s。
def askChoice(slogan):#将需要询问的内容封装进一个函数
    inputs = input(f'{slogan}\n')
    return inputs
#程序执行时先调用askChoice函数，并开始计时。
#若用户在计时期间内输入，则正常传参
#若用户超时，则触发func_timeout.exceptions.FunctionTimedOut异常，try...except捕捉异常，并进行后续操作。
 
def getHTMLText(Url, code = 'utf-8'):
    Headers = {'User-Agent':str(UserAgent().random)}
    r = requests.get(Url, headers = Headers, timeout = 30)
    r.raise_for_status()
    r.encoding = code
    return r.text
 
def getHTMLText_with_retry(Url, code = 'utf-8', retry = 10):
    for i in range(retry):
        try:
            request_text = getHTMLText(Url, code='utf-8')
            return request_text
        except Exception as e:
            print(f'网页访问失败: {e}')
        if i > 5:
            time.sleep(10)
    print(f'Load {Url} failed 10 times')
    return ''
 
def get_key(dct, value):
  return [k for (k,v) in dct.items() if v == value][0]#字典中根据值倒查键
 
def validate(date_text):
    date_text = re.sub(r'[^0-9/-]','',date_text)
    if date_text != '':
        try:
            if re.search('[/-]',date_text):
                if '/' in date_text:#匹配形如2020/01/01
                    tmZone = date_text.split('/')

                elif '-' in date_text:
                    tmZone = date_text.split('-')

                if len(tmZone[0]) == 2:#若年份是2位数，补全成20**
                    tmYear = time.strftime('%Y',time.strptime(tmZone[0], '%y'))
                else:
                    tmYear = tmZone[0]

                if len(tmZone) < 3:
                    Date = datetime(int(tmYear), int(tmZone[1]), 1)
                else:
                    Date = datetime(int(tmYear), int(tmZone[1]), int(tmZone[2]))#格式化成20200101形式
                Date = Date.strftime('%Y-%m-%d')#规范成2020-01-01
            
            elif date_text.isdigit():
                if len(date_text) == 8:
                    Date = datetime.strptime(date_text, '%Y%m%d').strftime('%Y-%m-%d')
                elif len(date_text) == 6:
                    try:
                        Date = datetime.strptime(date_text, '%y%m%d').strftime('%Y-%m-%d')
                    except:
                        Date = datetime.strptime(date_text, '%Y%m%d').strftime('%Y-%m-%d')
                else:
                    str_list = list(date_text)#匹配形如2020930这样7位日期
                    nPos = str_list.index(date_text[4])#提取年份
                    str_list.insert(nPos,'0')#月份前补充0位
                    date_text = ''.join(str_list)#列表转字符串
                    Date = datetime.strptime(date_text, '%Y%m%d').strftime('%Y-%m-%d')
 
        except:# ValueError:
            Date = validate(input())#排除手误情况，允许重新输入
    else:
        Date = time.strftime('%Y-%m-%d')#排除手误情况，默认今天
    return Date
 
def validate_2(date_text):#未使用 检查输入的是否符合日期格式YYYY-MM-DD
    if date_text != '':
        try:
            time.strptime(date_text, '%Y-%m-%d')
            Date = date_text
        except ValueError:
            Date = validate(input('What date is it? (YYYY-MM-DD) '))
    else:#默认输入今天
        Date = time.strftime('%Y-%m-%d')
    return Date
 
def Group(group):
    UrlLists = []#publisherParams根据Comixology New Release页
    publisherParams = {"DC":"1",
             "Marvel":"2",
             "Dark Horse":"3",
             "Image":"4",
             }
    if group == '1':
        #https://www.comixology.com/release-date/{WorM}-{Year}-{Date}{Params}
        try:#WorM
            Week_or_Month = askChoice('按 周Week 还是按 月Month？#不填默认按周').lower()#判断是按周还是按月爬取 .lower()转小写
            Week_and_Month = {"week":"w",
                     "month":"m"}
            if Week_or_Month in Week_and_Month.keys():#允许输入完整周/月分类
                print(f'Pre {Week_or_Month}')#根据输入倒查周/月分类
                Week_or_Month = Week_and_Month[Week_or_Month]
            elif Week_or_Month in Week_and_Month.values():
                print(f'Pre {get_key(Week_and_Month, Week_or_Month)}')#根据publisher数值倒查出版社名称
                Week_or_Month = Week_or_Month
            else:
                print(f'Pre week')
                Week_or_Month = 'w'#超时默认按周
        except func_timeout.exceptions.FunctionTimedOut as e:
            print(f'Pre week')
            Week_or_Month = 'w'#超时默认按周
        Params = {}
        try: #Params
            publisher = askChoice('选择出版社')#写入出版社
            if publisher in publisherParams.keys():#允许输入完整出版社名字
                print(f'Publisher is {publisher}')#根据publisher数值倒查出版社名称
                Params['publisher'] = publisherParams[publisher]
            elif publisher in publisherParams.values():
                print(f'Publisher is {get_key(publisherParams, publisher)}')#根据publisher数值倒查出版社名称
                Params['publisher'] = publisher
            else:
                pass
        except func_timeout.exceptions.FunctionTimedOut as e:
            pass #超时默认不填写
        
        if len(Params) != 0:
            Params = f'?{urlencode(Params)}'
        else:
            Params = ''
#————————————————————————————————————————
        if Week_or_Month == 'm':
            try:
                AllWorM = askChoice('爬取全年12个月？？#不填爬取全年')#询问是否遍历全年
                if AllWorM == '':
                    try:#Year
                        Year = int(askChoice('哪一年？'))
                    except func_timeout.exceptions.FunctionTimedOut as e:
                        Year = int(time.strftime('%Y'))
                    
                    if Year == '':#默认爬取今年
                        Year = int(time.strftime('%Y'))
 
                    for Month in range(1, 13):
                        Date = datetime(Year, Month, 1).strftime('%Y-%m-01')
                        UrlLists.append(f'https://www.comixology.com/release-date/m-{Date}{Params}')
                else:
                    Date = datetime.strptime(validate(input('哪一天？ (YYYY-MM-DD)\n')),'%Y-%m-%d')
                    Date = datetime(Date.year, Date.month, 1).strftime('%Y-%m-01')#格式化成每月第一天
                    UrlLists.append(f'https://www.comixology.com/release-date/m-{Date}{Params}')
            except func_timeout.exceptions.FunctionTimedOut as e:#超时爬取当前周全部，不带出版社参数
                UrlLists.append('https://www.comixology.com/release-date')
        else:
            Wednesday = (datetime.now() - timedelta(days = datetime.now().isoweekday()-3)).strftime('%Y-%m-%d')#格式化成周三
            UrlLists.append(f'https://www.comixology.com/release-date/w-{Wednesday}{Params}')
            LastWed = (datetime.now() - timedelta(days = datetime.now().isoweekday()-3, weeks = 1)).strftime('%Y-%m-%d')#上一个周三
            UrlLists.append(f"https://www.comixology.com/release-date/w-{LastWed}{Params}")
 
    elif group == '2':
        UrlLists.append('https://www.comixology.com/comics-best-sellers')#销量榜
    elif group == '3':
        UrlLists.append('https://www.comixology.com/comics-sale')#大促
    elif re.match('.*comixology.com/',group): 
        UrlLists.append(group)
    else:
        exit()
    return UrlLists
 
def output(Url):#文件输出路径
    fpath = re.sub('.*comixology.com/','',Url).replace('-', '_')
    fpath = re.sub('(\?|&).*','',fpath)#删除页码
    fpath = re.sub('[A-Z]',lambda x:' '+x.group(0),fpath).title()#首字母大写
    #fpath = re.sub('_(\d+)',lambda x: x.group(1),fpath)#删除页码然后拼接
    fpath = fpath.replace('=', '').replace('_', '').replace(' ', '')#删除数字前的空格
    output_file = f'/content/drive/My Drive/{fpath}.csv'
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    print(f'File will be saved in {fpath}.csv')
    return output_file
 
def list_app(old_list, new_list = list()):#未使用，展平嵌套列表
    #'''isinstance去判断遍历的l是不是还是一个list如果还是list, 用递归继续反复遍历'''
    for l in old_list:
        if isinstance(l, list):
            list_app(l) # 调用递归
        else:
            # 如果不是, 把l添加进一个新的list
            new_list.append(l)
    return new_list
 
def newUrl(base, Url):
    Url1 = urljoin(base, Url)
    arr = urlparse(Url1)
    path = normpath(arr[2])
    return urlunparse((arr.scheme, arr.netloc, path, arr.params, arr.query, arr.fragment))
 
def emb_numbers(s):
    re_digits = re.compile(r'(\d+)')
    pieces = re_digits.split(s)
    pieces[1::2] = map(int,pieces[1::2])    
    return pieces
 
def sort_strings_with_emb_numbers(alist):
    aux = [(emb_numbers(s),s) for s in alist]
    aux.sort()
    return [s for __,s in aux]
#没搞懂，按https://www.cnblogs.com/ajianbeyourself/p/5395653.html，找机会用key替换掉DSU排序
 
def list_title(list_title):
    if re.match('Week .*',list_title):#每周上新页形式
        title = re.search(' (\w+ \d{1,2}) (\d{4}|.*)- (\w+ \d{1,2}) (\d{4}).*\((\d+)', list_title)
        Total_Count = int(title.group(5).strip())#(* items)
        if title.group(2).strip() == '':
            year = title.group(4).strip()
        else:
            year = title.group(2).strip()
        Begin_Date = datetime.strptime(f'{title.group(1)} {year}','%B %d %Y').strftime('%Y/%m/%d (%a)')
        End_Date = datetime.strptime(f'{title.group(3)} {title.group(4)}','%B %d %Y').strftime('%Y/%m/%d (%a)')
        print(f'\nWeek from {Begin_Date} to {End_Date} ({Total_Count} Items)')
    
    if re.match('Month .*',list_title):
        title = re.search(' (\w+ \d{4}).*\((\d+)', list_title)
        Total_Count = int(title.group(2).strip())
        print(f"\nMonth Begin with {datetime.strptime(f'{title.group(1)}','%B %Y').strftime('%Y/%m/%d (%a)')}")
    
    elif re.match('.*Sale',list_title):#促销页形式
        title = re.search('\\((\d+) Items', list_title)
        Total_Count = int(title.group(1).strip())
        print(f'\n{list_title},', end = ' ')
        if soup.select_one('h4.list-subtitle'):#促销活动完结日期
            list_subtitle = soup.select_one('h4.list-subtitle').string#Sale ends Monday, 11/30/2020
            subtitle = re.search('(\d{1,2}/\d{1,2}/\d{4})', list_subtitle)
            end_date = datetime.strptime(subtitle.group(1), '%m/%d/%Y')
            date_left = (end_date-datetime.now()).days
                        #-datetime.strptime(date.today().isoformat(),'%Y-%m-%d')).days
            print(f"Sale ends {end_date.strftime('%Y/%m/%d (%a)')}, {date_left} days left")
    
    else:
        Total_Count = len(soup.select('li.content-item'))
    return Total_Count

def getList(Url):#未使用，查找更多内容View_More
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    UrlList = []
    UrlList.append(Url)
    html = getHTMLText_with_retry(Url, 'uft-8')
    soup = BeautifulSoup(html, 'html.parser')
    a = soup.find_all('a', class_ = re.compile('all-link'))
    if a == '':
        More = ''
    else:
        for link in a:
            More = link.attrs['href']
            if re.match(r'.*(\?|&)lang=1',More):
                ends = re.compile(r'(\?|&)lang=1')#删除可能的以lang = 1结尾的网址（默认语言）
                More = ends.sub('',More)
                More.replace('&','?',1)
                if More.endswith('?'):
                    More = More[:-1]
                if More.endswith('&'):
                    More = More[:-1]
            attrs = re.compile(r'&(lang=\d+|cu=\d+)|(lang=.\d+|cu=.\d+)&')# clean cu = 0, avoid different link for same page
            More = attrs.sub('',More)
            UrlList.append(More)
    UrlList = flatten(UrlList)
    UrlList = sorted(list(set(UrlList)))
    print(f'Find {len(UrlList)} page(s) can View_More\r', end = '')
    return UrlList
 
def getListPlus(Url,UrlList):
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    
    html = getHTMLText_with_retry(Url, 'uft-8')
    soup = BeautifulSoup(html, 'html.parser')
    a = soup.find_all('a', class_ = re.compile('pager-link'))#查找所有页面链接
    
    try:
        print(soup.select_one('h3.list-title').string)
    except:
        pass
 
    if len(a) == 0: # 如果只有一页
        if not Url in UrlList:
            UrlList.append(Url)
        print(f'Only find 1 page, {len(UrlList)} page(s) in total\r', end = '')
    else:
        pages = []
        UrlList.append(Url)
        pages = pages.append(flatten(getList(Url)))#查找有没View_More展开
        pages = sorted(list(set(UrlList)))#删除重负页面
        # Get all existing page link
        pages = [a_element.attrs['href'] for a_element in a]
        # For total page > 5, some page is hidden
        last_pages = [a_element.attrs['href'] for a_element in a if a_element.string == 'Last']
        # generate page for hidden page
        for last_page in last_pages:
            matched_result = re.match('(.*_pg=)(\d+)', last_page)
            base_path = matched_result.group(1)
            page_num = int(matched_result.group(2))
            print('base_path', base_path, page_num)
            pages.extend([f'{base_path}{i+1}' for i in range(page_num)])
        attrs = re.compile(r'&(lang=\d|cu=\d)|(lang=\d|cu=\d)&')
        pages = [attrs.sub('',x) for x in pages] # clean cu = 0, avoid different link for same page
        pages = sorted(list(set(pages)))
        pages = [newUrl(Url, x) for x in pages]#拼接网址
        bundle = re.compile(r'.*//bundle//')#目前无法解决爬取套装页，先剔除
        pages = [x for x in pages if not bundle.match(x)]
        pages = flatten(pages)
        for page in pages:
            if not page in UrlList:
                if page.endswith('?'):
                    page = page[:-1]
                if page.endswith('&'):
                    page = page[:-1]
                UrlList.append(page)#循环写入非重复网址
        print(f'Find {len(pages)} more page(s), {len(UrlList)} page(s) in total\r', end = '')
    UrlList = flatten(UrlList)#展平嵌套列表
    UrlList = sorted(list(set(UrlList)))#删除重复页面
 
    if 'https://www.comixology.com/comics-best-sellers' in UrlList:
        UrlList.remove('https://www.comixology.com/comics-best-sellers')
        
    #UrlLst = list_app(UrlLst)#旧的展平函数
    #print(f'2. Find {len(UrlList)} more page(s)')#跟主函数那一条雷同
    return UrlList
 
def get_data_from_item_page(item_page_url):
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
    html2 = getHTMLText_with_retry(item_page_url)
    #time.sleep(1)
    soup2 = BeautifulSoup(html2, 'html.parser')
 
    #获取面包屑导航栏信息
    for link in soup2.select('div#cmx_breadcrumb > a'):
        datas['breadcrumb_url'] = re.sub('\?ref=.*', '', link['href'])#连载对应的系列地址
        datas['breadcrumb_text'] = link.get_text()#连载系列
 
    item_title = soup2.select_one('div#column2 > h1.title').string.strip()
    item_title = html.unescape(item_title).replace(' ',' ').replace('  ',' ')
    datas['item_title'] = html.unescape(item_title)
 
    item_description = soup2.select_one('div#column2 > section.item-description').get_text().strip()
    datas['item_description'] = html.unescape(item_description).replace(' ',' ').replace('  ',' ')
 
    #可能存在多个badge信息，因此用列表装载
    badges = []
    for badge in soup2.select('div#column2 > div.badges img.badge'):
        badges.append(badge['title'])
    datas['item_badge'] = badges
 
    publisher = ' '.join(soup2.select_one("h3[title='Publisher']").string.split())
    datas['item_publisher'] = publisher
 
    #找credits
    credit_lst = []
    for credit in soup2.select('div#column3 > div.credits > div.credits'):
        #用于放置Written By等信息
        sub = credit.select_one('dt').string
        name_lst = []
        name_lst.append(sub+':')
        for name in credit.select('a'):
            if name.string.strip() != 'HIDE...':
                name_lst.append(name.string.strip())
        credit_lst.append(name_lst)
    datas['item_credits'] = credit_lst
 
    genres = []
    for genre in soup2.select('div#column3 > div.credits > a'):
        genres.append(genre.string.strip())
    datas['item_genres'] = genres
 
    #直接爬取对应的副标题与对应信息
    sub_lst = []
    for subtitle in soup2.select('div#column3 > div.credits > h4.subtitle'):
        sub_lst.append(subtitle.string)
 
    info_lst = []
    for info in soup2.select('div#column3 > div.credits > div.aboutText'):
        temp = info.string.replace('\t', '').replace('\n', '')
        info_lst.append(temp)
    for i in range(len(sub_lst)):
        datas['item_abouttext'].append(sub_lst[i]+':'+info_lst[i])
    return datas
 
def getInfo(UrlLists):
    Total = 0
    Total_Count = 0
    count = 0
    Page_Num = 0
    Error = 0
    ErrorList = []
    for Url in UrlLists:
        this_page_count = 0
        html = getHTMLText_with_retry(Url, 'uft-8')
        #time.sleep(1)
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            Total_Count = list_title(soup.select_one('h3.list-title').string)
        except:
            Total_Count = len(soup.select('li.content-item'))
        
        This_page = len(soup.select('li.content-item'))
        if Total+This_page <= Total_Count:
            Total = Total_Count
        else:
            Total += This_page
        Page_Num += 1
        print(f'{This_page}/{Total}	Now Processing Page {Page_Num}: {Url}', end = ' ')
        output_file = output(Url)
        for item in soup.select('li.content-item'):
            count += 1
            this_page_count += 1
            try:
                #所需要的元素
                datas = {
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
                
                datas['cover_url'] = re.sub('_SX.*_QL.*_TTD_','_SX312_QL80_TTD_',item.select_one('img.content-img')['src'])
 
                if item.select_one('h5.content-title'):
                    datas['title'] = item.select_one('h5.content-title').string
                else:
                    print(f"Err: {item.select_one('h5.content-title')}")
                    continue
 
                #存在没有副标题的情况
                if item.select_one('h6.content-subtitle'):
                    datas['subtitle'] = item.select_one('h6.content-subtitle').string
                else:
                    datas['subtitle'] = ''
 
                datas['price'] = item.select_one('h5.item-price').string
 
                #存在没有full_price的情况
                if item.select_one('h6.item-full-price'):
                    datas['full_price'] = item.select_one('h6.item-full-price').string
                else:
                    datas['full_price'] = item.select_one('h5.item-price').string
 
                #语言
                if item.select_one('img.badge'):
                    datas['lang'] = item.select_one('img.badge')['title']
                else:
                    datas['lang'] = 'English'
 
                #获取item下一级页面url
                datas['item_page_url'] = item.select_one('a.content-details')['href']
                datas['code'] = re.sub('.*digital-comic/','',datas['item_page_url'])#替换成Code形式
                
                # Get info from item page url
                sub_data = get_data_from_item_page(datas['item_page_url'])
                data = {**datas, **sub_data}
 
                #将字典各value按顺序写出
                lst = [value for value in data.values()]
                with open(output_file, 'at', encoding = 'utf-8', newline = '') as csvfile:
                    print(f"No.{count}	{data['item_title']}, {data['item_publisher']}")
                    writer = csv.writer(csvfile)
                    writer.writerow(lst)
            except:
                Error += 1
                Retry = 0
                RetryList = []
                item_page_url = item.select_one('a.content-details')['href']
                bundle = re.compile(r'.*/bundle/')#目前无法解决爬取套装页，先剔除
                if bundle.match(item_page_url):
                    RetryList.append(item_page_url)
                    print(f'Find bundle: {item_page_url}')
                else:
                    RetryList.append(Url)
                    print(f'{Error}/{this_page_count}/{count}	Err: {item_page_url}, turn to RetryList')
                getInfo(RetryList)
                time.sleep(1)
                continue
 
if __name__ == "__main__":
    # Testing item page
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    UrlList = []
    Links = []
    Pages = []
    start_time = time.time()
    try:
        print(f'''----------------------------------------
今天是{time.strftime('%Y/%m/%d 第%W周 星期%w')}
1 发售 Release Date
2 销量 Best Sellers
3 促销 Comics Sale''')
        group = askChoice('请输入分组：')#判断是按周还是按月爬取
    except func_timeout.exceptions.FunctionTimedOut as e:
        exit()
    UrlLists = Group(group)
    for Url in UrlLists:#查找View_More
        print(f'\rProcessing {Url}', end = '')
        Links.extend(getList(Url))
        Links = sort_strings_with_emb_numbers(flatten(list(set(Links))))
    print(f'\rFind {len(Links)} more page(s) can View_More\n')#查找到View_More
    for Link in Links:#再对每个页面进行翻页
        print(f'\rProcessing {Link}', end = ' ')
        Pages.extend(getListPlus(Link,UrlList))
        Pages = sort_strings_with_emb_numbers(flatten(list(set(Pages))))#按页码排序
    print(f'\rFind {len(Pages)} page(s) at all\n')
    getInfo(Pages)
    print(f"Finish Time: {datetime.fromtimestamp(time.time()-start_time).strftime('%-H:%-M:%-S.%f')}")#加短横线-省略多余前置0
    exit()
