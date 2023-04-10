import requests
import urllib.request
from concurrent import futures
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import time
import csv
import json
import os
import sys
import datetime
import re
from . import jst
from . import seleniumDriverWrapper as wrap
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import traceback

class eventListPageParser():
    def __init__(self, _html):
        self.__html = _html

    def getEventList(self):
        soup = BeautifulSoup(self.__html, 'html.parser')
        l = list()
        liList = soup.find_all("a", class_="eventListItem")
        for li in liList:
            url = self.getLink(li)
            l.append({'event_id': self.getEventID(url), 'event_url': url})
        return l

    def isNextButton(self):
        soup = BeautifulSoup(self.__html, 'html.parser')
        nextBtn = soup.find("button", class_="btn next")
        if nextBtn != None:
            return True
        return False

    def clickNextButton(self):
        soup = BeautifulSoup(self.__html, 'html.parser')
        nextBtn = soup.find("button", class_="btn next")
        nextBtn.click()

    def getLink(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            if _BeautifulSoup.has_attr('href'):
                return _BeautifulSoup['href']
        return None

    def getEventID(self, url):
        find_pattern = r"/detail/(?P<id>[0-9]+)/result"
        m = re.search(find_pattern, url)
        if m != None:
            return int(m.group('id'))
        return ''

class eventPageParser():
    def __init__(self, _html, _event_id, _event_url):
        self.__html = _html
        self.__event_id = _event_id
        self.__event_url = _event_url

    def getRankerList(self):
        soup = BeautifulSoup(self.__html, 'html.parser')
        title = self.getTitle(soup)
        event_type = self.getEventType(soup)
        sponsorship = self.getSponsorship(soup)
        address = self.filterRegion(self.getAddress(soup))
        event_day = self.getDateDay(soup)
        event_datetime = self.getDateTime(soup)
        l = list()
        trList = soup.find_all("tr", class_="c-rankTable-row")
        for tr in trList:
            l.append({
                'date': event_day,
                'datetime': event_day+' '+event_datetime,
                'event_id': self.__event_id,
                'event_type': event_type,
                'event_name': title,
                'sponsorship': sponsorship,
                'address': address,
                'event_url': self.__event_url,
                'rank': int(self.getRank(tr)),
                'player_id': self.filterUserID(self.getUserID(tr)),
                'player_name': self.getUserName(tr),
                'player_area': self.getArea(tr),
                'deck_id': self.filterDeckID(self.getLink(tr)),
                })
        return l

    def isNextButton(self):
        soup = BeautifulSoup(self.__html, 'html.parser')
        nextBtn = soup.find("button", class_="btn next")
        if nextBtn != None:
            return True
        return False

    def clickNextButton(self,drvWrapper):
        elementsBtn = drvWrapper.getDriver().find_elements(By.CLASS_NAME, 'next')
        if len(elementsBtn) != 0:
            for btn in elementsBtn:
                btn.click()
                break

    def getDateDay(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            div = _BeautifulSoup.find("div", class_="date-day")
            if div != None:
                find_pattern = r'(?P<x>[0-9]+)年(?P<y>[0-9]+)月(?P<z>[0-9]+)日'
                m = re.search(find_pattern, div.text)
                if m != None:
                    return m.group('x')+'-'+m.group('y')+'-'+m.group('z')
                return div.text
        return None

    def getDateTime(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            div = _BeautifulSoup.find("div", class_="date-time")
            if div != None:
                find_pattern = r'(?P<x>[0-9]+):(?P<y>[0-9]+)'
                m = re.search(find_pattern, div.text)
                if m != None:
                    return m.group('x')+':'+m.group('y')+':00'
                return div.text
        return None

    def getTitle(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            h1 = _BeautifulSoup.find("h1", class_="c-title-event")
            if h1 != None:
                return h1.text
        return None

    def getEventType(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            span = _BeautifulSoup.find("span", class_="event u-mr")
            if span != None:
                return span.text
        return None

    def getSponsorship(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            div = _BeautifulSoup.find("div", class_="sponsorship")
            if div != None:
                a = div.find("a")
                if a != None:
                    return a.text
        return None

    def getAddress(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            div = _BeautifulSoup.find("div", class_="address")
            if div != None:
                div2 = div.find("div")
                if div2 != None:
                    return div2.text
        return None
        
    
    def getRank(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            tdRank = _BeautifulSoup.find("td", class_="rank")
            if tdRank != None:
                span = tdRank.find("span")
                if span != None:
                    return span.text
        return None

    def getUserName(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            td = _BeautifulSoup.find("td", class_="user")
            if td != None:
                span = td.find("span", class_="user-name")
                if span != None:
                    return span.text
        return None

    def getUserID(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            td = _BeautifulSoup.find("td", class_="user")
            if td != None:
                span = td.find("span", class_="user-id")
                if span != None:
                    return span.text
        return None

    def getArea(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            td = _BeautifulSoup.find("td", class_="area")
            if td != None:
                return td.text
        return None

    def getLink(self,_BeautifulSoup):
        if _BeautifulSoup is not None:
            td = _BeautifulSoup.find("td", class_="deck")
            if td != None:
                a = td.find("a", class_="deck-link")
                if a != None:
                    if a.has_attr('href'):
                        return a['href']
        return None

    def filterRegion(self, keyword):
        find_pattern = r'\s(?P<x>.*[都道府県])'
        m = re.search(find_pattern, keyword)
        if m != None:
            return m.group('x')
        return None

    def filterDeckID(self, keyword):
        find_pattern = r'(?P<x>[0-9a-zA-Z]{6})-(?P<y>[0-9a-zA-Z]{6})-(?P<z>[0-9a-zA-Z]{6})'
        if keyword == None:
            print('Deck ID : None')
            return None
        m = re.search(find_pattern, keyword)
        if m != None:
            return m.group('x')+'-'+m.group('y')+'-'+m.group('z')
        print('Deck ID : None')
        return None

    def filterUserID(self, keyword):
        find_pattern = r'：(?P<x>[0-9]+)'
        m = re.search(find_pattern, keyword)
        if m != None:
            return m.group('x')
        return None

class deckListParser():
    def __init__(self, _html):
        self.__html = _html

    def getItemList(self):
        soup = BeautifulSoup(self.__html, 'html.parser')
        deck_id = self.getDeckID(soup)
        if deck_id is None:
            return None
        section = self.getSection(soup)
        l = list()
        tblList = section.find_all("table", class_="KSTable KSTable-small")
        for tbl in tblList:
            l.append({
                "deck_id": deck_id,
                "card_id": self.getCardID(tbl),
                "card_name": self.getItemName(tbl),
                "count": int(re.findall('[0-9]+', self.getCount(tbl).replace(',',''))[0]),
                #"image": self.getImage(tbl),
            })
        return l

    def getDeckID(self,_BeautifulSoup):
        _id = _BeautifulSoup.find("span", id="copyID")
        if _id is not None:
            return _id.get_text()
        return None
    
    def getCount(self,_BeautifulSoup):
        span = _BeautifulSoup.find("span")
        if span is not None:
            return span.get_text()
        return None

    def getSection(self,_BeautifulSoup):
        setct = _BeautifulSoup.find("section", id="cardImagesView")
        if setct is not None:
            return setct
        return None
    
    def getItemName(self,_BeautifulSoup):
        img = _BeautifulSoup.find("img")
        if img is not None:
            if img.has_attr('alt'):
                return img['alt']
        return None

    def getCardID(self,_BeautifulSoup):
        img = _BeautifulSoup.find("img")
        if img is not None:
            if img.has_attr('id'):
                find_pattern = r"img_(?P<cardid>\d*).*"
                m = re.search(find_pattern, img['id'])
                if m != None:
                    return int(m.group('cardid'))
        return None

    def getImage(self,_BeautifulSoup):
        img = _BeautifulSoup.find("img")
        if img is not None:
            if img.has_attr('src'):
                return img['src']
        return None

class eventSearchCsv():
    def __init__(self,_out_dir, _event_id):
        dt = jst.now().replace(microsecond=0)
        self.__list = list()
        self.__date = str(dt.date())
        self.__datetime = str(dt)
        self.__file = _out_dir+'/'+self.__datetime.replace("-","_").replace(":","_").replace(" ","_")+'_'+_event_id+'.csv'

    def init(self):
        labels = [
         'date',
         'datetime',
         'event_type',
         'event_name',
         'organizer',
         'address',
         'event_url',
         'rank',
         'player_id', 
         'player_name', 
         'player_area', 
         'deck_id'
         ]
        try:
            with open(self.__file, 'w', newline="", encoding="utf_8_sig") as f:
                writer = csv.DictWriter(f, fieldnames=labels)
                writer.writeheader()
                f.close()
        except IOError:
            print("I/O error")

    def add(self, data):
        data['date'] = str(self.__date)
        data['datetime'] = str(self.__datetime)
        self.__list.append(data)
        
    def save(self):
        if len(self.__list) == 0:
            return
        df = pd.DataFrame.from_dict(self.__list)
        if os.path.isfile(self.__file) == False:
            self.init()
        df.to_csv(self.__file, index=False, encoding='utf_8_sig')


'''
    [{"deck_id": ,
     "card_id": ,
     "card_name": ,
     "count":
    },{...},...]
'''
class officialDeckScrapBot():

    def download(self, drvWrapper, deck_id):
        self.getResultPage(drvWrapper.getDriver(), deck_id)

        try:
            print("Wait deck : "+deck_id)
            drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.CLASS_NAME,'thumbsImage')))
            time.sleep(5)
        except TimeoutException as e:
            print("ERROR deck : "+deck_id)
            print("TimeoutException" )
        except Exception as e:
            print("ERROR deck : "+deck_id)
            print(traceback.format_exc())

        listHtml = drvWrapper.getDriver().page_source.encode('utf-8')
        parser = deckListParser(listHtml)
        l = parser.getItemList()

        return l

    def getResultPage(self, driver, deck_id):
        try:
            url = 'https://www.pokemon-card.com/deck/confirm.html/deckID/'+deck_id
            print("Get deck : "+deck_id)
            driver.get(url)
        except WebDriverException as e:
            print("ERROR deck : "+deck_id)
            print("WebDriverException")
        except Exception as e:
            print("ERROR deck : "+deck_id)
            print(traceback.format_exc())

    def checkDeckID(self, deck_id):
        find_pattern = r'^(?P<x>[0-9a-zA-Z]{6})-(?P<y>[0-9a-zA-Z]{6})-(?P<z>[0-9a-zA-Z]{6})$'
        m = re.search(find_pattern, deck_id)
        if m != None:
            print(m.group('x')+'-'+m.group('y')+'-'+m.group('z'))
            return True
        return False

class officialEventRankerCsvBot():
    def getFilePath(self, event_id, out_dir):
        return out_dir+'/'+event_id+'.csv'

    def isFile(self, event_id, out_dir):
        if os.path.exists(self.getFilePath(event_id, out_dir)) == True:
            return True
        return False

    def download(self, drvWrapper, event_id, event_url, out_dir):
        # カード一覧へ移動
        find_next = True
        rankerList = []
        url = 'https://players.pokemon-card.com'+event_url
        
        try:
            print("Get event : "+event_id)
            drvWrapper.getDriver().get(url)
        except WebDriverException as e:
            print("Get event : "+event_id)
            print("WebDriverException")
        except Exception as e:
            print("Get event : "+event_id)
            print(traceback.format_exc())

        while find_next:
            print("Wait event : "+event_id)
            try:
                drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.CLASS_NAME,'deck-link')))
                time.sleep(5)
                eventHtml = drvWrapper.getDriver().page_source.encode('utf-8')
                parser = eventPageParser(eventHtml, event_id, event_url)
                rankerList.extend(parser.getRankerList())
                if parser.isNextButton() == True:
                    parser.clickNextButton(drvWrapper)
                else:
                    print('Not found next')
                    find_next = False
            except TimeoutException as e:
                print("ERROR event : "+event_id)
                print("TimeoutException")
                find_next = False
            except Exception as e:
                print("ERROR event : "+event_id)
                print(traceback.format_exc())
        
        writeData = []
        deckBot = officialDeckScrapBot()
        for ranker in rankerList:
            if ranker['deck_id'] != None:
                print('Start download : '+ranker['deck_id'])
                cardList = deckBot.download(drvWrapper, ranker['deck_id'])
                print('Complete download : '+ranker['deck_id'])
                for card in cardList:
                    writeData.append({
                        'date': ranker['date'],
                        'datetime': ranker['datetime'],
                        'event_type': ranker['event_type'],
                        'event_name': ranker['event_name'],
                        'sponsorship': ranker['sponsorship'],
                        'address': ranker['address'],
                        'event_id': event_id,
                        'event_url': ranker['event_url'],
                        'rank': ranker['rank'],
                        'player_id': ranker['player_id'],
                        'player_name': ranker['player_name'],
                        'deck_id': ranker['deck_id'],
                        'card_id': card['card_id'],
                        'card_name': card['card_name'],
                        'count': card['count']
                    })
        
        self.save(writeData,self.getFilePath(event_id, out_dir))

    def save(self, dict_array, _file):
        try:
            df = pd.DataFrame.from_dict(dict_array)
            df.to_csv(_file, index=False, encoding='utf_8_sig')
        except IOError:
            print("I/O error")

class officialEventCsvBot():
    def download(self, drvWrapper, out_dir, id_list, start_page):
        # カード一覧へ移動
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        page_no = start_page
        find_next = True
        targetList = []
        while find_next:
            self.getResultPageNormal(drvWrapper.getDriver(), page_no)
            try:
                drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.CLASS_NAME,'c-btn-primary-outline')))
                time.sleep(3)
                listHtml = drvWrapper.getDriver().page_source.encode('utf-8')
                parser = eventListPageParser(listHtml)
                rankerBot = officialEventRankerCsvBot()
                l = parser.getEventList()
                for item in l:
                    print(item)
                    if str(item['event_id']) in id_list:
                        print('already exists. skip event:'+str(item['event_id']))
                    elif rankerBot.isFile(str(item['event_id']), out_dir) == True:
                        print('file is already exists. skip event:'+str(item['event_id']))
                        #find_next = False
                        #break
                    else:
                        targetList.append(item)

                find_next = False

                for item in targetList:
                    print('Download event:'+str(item['event_id']))
                    rankerBot.download(drvWrapper, str(item['event_id']), item['event_url'], out_dir)

            except TimeoutException as e:
                print("TimeoutException")
            except Exception as e:
                print(traceback.format_exc())

    def getResultPageNormal(self, driver, page):
        url = 'https://players.pokemon-card.com/event/result/list?offset='+str(page*20)+'&order=4&result_resist=1&event_type=3:1&event_type=3:2'
        print("Get page : "+url)
        try:
            driver.get(url)
        except WebDriverException as e:
            print("WebDriverException")
        except Exception as e:
            print(traceback.format_exc())
