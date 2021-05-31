from bs4 import BeautifulSoup
import requests
from fuzzywuzzy import fuzz
from time import process_time, strptime
import re
import urllib
import json
import re
import time
import calendar
import datetime
import comicutil
import comicdb
import copy

baseUrl = 'https://leagueofcomicgeeks.com'

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def get_issue_by_id(id):
    response = requests.get(id,headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    description = ""
    try:
        description = re.sub('<[^<]+?>', '', soup.find("div", {"class": "col-12 listing-description"}).text).replace("\n","").replace("\r","").replace("\t","")
    except:
        pass
    details_section = soup.find_all("div", {"class": "col-xxl-4 col-lg-6 col-6 mb-3 details-addtl-block"})
    page_count = details_section[1].find("div", {"class": "value"}).contents[0].strip().split()[0]
    price = details_section[2].find("div", {"class": "value"}).contents[0].strip().split()[0]
    creators_section = soup.find_all("div", {"class": "d-flex flex-column align-self-center"})
    credits = []
    for creator in creators_section:
        try:
            title = creator.find("div", {"class": "role color-offset copy-really-small"}).contents[0].strip()
            for t in title.split(","):
                c = {}
                title = t.strip()
                if "cover" in t.lower():
                    title = "Cover Artist"
                if "story" in t.lower():
                    title = "Writer"
                name = creator.find("div", {"class": "name color-primary font-weight-bold"}).find("a").contents[0].strip()
                c["role"] = title
                c["person"] = name
                if c not in credits:
                    credits.append(c)
        except:
            pass
        issueObject = {}
    issueObject['price'] = price
    issueObject['page_count'] = page_count
    issueObject['credits'] = credits
    issueObject['description'] = description
    return issueObject

        
    
    
def get_series_by_id(id):
    issue_list = []
    #url = f"{baseUrl}/comic/get_comics?addons=1&list=series&list_option=&user_id=0&view=thumbs&format%5B%5D=1&format%5B%5D=5&date_type=&date=&date_end=&series_id={id}&creators=0&character=&title=&order=date-desc&_={calendar.timegm(time.gmtime())}"
    url = f"{baseUrl}/comic/get_comics?addons=1&list=series&list_option=&user_id=0&view=thumbs&format%5B%5D=1&date_type=&date=&date_end=&series_id={id}&creators=0&character=&title=&order=date-desc&_={calendar.timegm(time.gmtime())}"
    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(json.loads(response.text)["list"], 'html.parser')
    issues = soup.find_all("li")
    for issue in issues:
        cover_section = issue.find("div", {"class": "cover"})
        issue_link = f'{baseUrl}{cover_section.find("a")["href"]}'
        issue_cover = cover_section.find("a").find("img")['data-src']
        if "https" not in issue_cover:
            issue_cover = f"{baseUrl}{issue_cover}"
        issue_name = issue.find("div", {"class": "title color-primary"}).find("a").contents[0].strip()
        epoch = issue.find("div", {"class": "details"}).find("span", {"class": "date"})['data-date']
        store_date = "0000-00-00"
        try:
            store_date = datetime.datetime.fromtimestamp(int(epoch)).strftime('%Y-%m-%d')
        except:
            pass
        issueObject = {}
        issueObject['coverImage'] = issue_cover
        issueObject['issueName'] =  issue_name
        issueObject['issueNumber'] = comicutil.get_issue_number(issue_name)
        issueObject['id'] = issue_link
        issueObject['issueLink'] =  issue_link
        issueObject['storeDate'] = store_date
        issue_list.append(issueObject)
    return issue_list

def search_series(query,volumeConfidence=0,issueConfidence=0):
    results = []
    comic_details = comicutil.get_comic_details(query)
    #url = f"{baseUrl}/comic/get_comics?addons=1&list=search&list_option=series&user_id=0&view=thumbs&format%5B%5D=1&format%5B%5D=6&format%5B%5D=5&format%5B%5D=2&format%5B%5D=3&format%5B%5D=4&date_type=&date=&date_end=&series_id=0&creators=0&character=0&title={urllib.parse.quote(comic_details.series)}&order=alpha-asc&filterCreator=1&filterCharacter=1&_={calendar.timegm(time.gmtime())}"
    url = f"{baseUrl}/comic/get_comics?addons=1&list=search&list_option=series&user_id=0&view=thumbs&format%5B%5D=1&date_type=&date=&date_end=&series_id=0&creators=0&character=0&title={urllib.parse.quote(comic_details.series)}&order=alpha-asc&filterCreator=1&filterCharacter=1&_={calendar.timegm(time.gmtime())}"

    try:
        response = requests.get(url,headers=headers)
    except Exception as e:
        return results
    soup = BeautifulSoup(json.loads(response.text)["list"], 'html.parser')
    all_series = soup.find_all("li")
    for series in all_series:
        issue_count = series.find("span", {"class": "details count-issues"}).contents[0].strip()
        cover_section = series.find("div", {"class": "cover"})
        volume_link = f'{baseUrl}{cover_section.find("a", {"class": "link-collection-series"})["href"]}'
        series_cover = cover_section.find("a", {"class": "link-collection-series"}).find("img")["data-src"]
        series_id = cover_section.find("a", {"class": "link-collection-series"})["data-id"]
        publisher = series.find("div", {"class": "publisher color-offset"}).contents[0].strip()
        series_name = series.find("div", {"class": "title color-primary"}).find("a").contents[0].strip()
        start_year = series.find("div", {"class": "series"})['data-begin']
        end_year =  series.find("div", {"class": "series"})['data-end']
        ratio = fuzz.ratio(series_name,comic_details.series)
        if ratio > volumeConfidence:
            series = {}
            series["name"] = series_name
            series["issue_count"] = issue_count
            series["publisher"] = comicdb.map_publisher(publisher)
            series["link"] =  volume_link
            series['year'] = f"{start_year}-{end_year}"
            series['start_year'] = start_year
            series['volumeYear'] = start_year
            series["volumeName"] = series_name
            series['end_year'] = end_year
            series["confidence"] = ratio
            series['id'] = series_id
            results.append(series)
    results.sort(key=lambda x: int(x['confidence']),reverse = True)
    return results


def search_comics(query,volumeConfidence=0,issueConfidence=0):
    results = []
    comic_details = comicutil.get_comic_details(query)
    url = f"{baseUrl}/comic/get_comics?addons=1&list=search&list_option=series&user_id=0&view=thumbs&format%5B%5D=1&format%5B%5D=6&format%5B%5D=5&format%5B%5D=2&format%5B%5D=3&format%5B%5D=4&date_type=&date=&date_end=&series_id=0&creators=0&character=0&title={urllib.parse.quote(comic_details.series)}&order=alpha-asc&filterCreator=1&filterCharacter=1&_={calendar.timegm(time.gmtime())}"
    try:
        response = requests.get(url,headers=headers)
    except Exception as e:
        return results
    soup = BeautifulSoup(json.loads(response.text)["list"], 'html.parser')
    all_series = soup.find_all("li")
    for series in all_series:
        cover_section = series.find("div", {"class": "cover"})
        volume_link = f'{baseUrl}{cover_section.find("a", {"class": "link-collection-series"})["href"]}'
        series_cover = cover_section.find("a", {"class": "link-collection-series"}).find("img")["data-src"]
        series_id = cover_section.find("a", {"class": "link-collection-series"})["data-id"]
        publisher = series.find("div", {"class": "publisher color-offset"}).contents[0].strip()
        series_name = series.find("div", {"class": "title color-primary"}).find("a").contents[0].strip()
        start_year = series.find("div", {"class": "series"})['data-begin']
        end_year =  series.find("div", {"class": "series"})['data-end']
        ratio = fuzz.ratio(series_name,comic_details.series)
        if ratio > volumeConfidence:
            series_details = get_series_by_id(series_id)
            for issue in series_details:
                issue_ratio = fuzz.ratio(issue['issueName'],f"{comic_details.series} #{comic_details.issue}")
                issue["volumeName"] = series_name
                issue["volumeLink"] = volume_link
                issue["publisher"] = comicdb.map_publisher(publisher)
                issue['volumeYear'] = start_year
                issue['confidence'] = issue_ratio
                results.append(issue)
    results.sort(key=lambda x: int(x['confidence']),reverse = True)
    return results


def search_comics_scrape(query,volumeConfidence=0,issueConfidence=0):
    url = '{}/search?keyword={}'.format(baseUrl,urllib.parse.quote(query))
    comic_details = comicutil.get_comic_details(query)
    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    volumes = soup.find_all("a", {"class": "link-collection-series"})
    searchResults = []
    for series in volumes:
        if series.contents[0] != "\n":
            ratio = fuzz.ratio(series.contents[0].strip(),comic_details.series)
            if ratio > volumeConfidence:
                url = '{}{}'.format(baseUrl,series['href'])
                seriesid = series['data-id']
                url = f"{baseUrl}/comic/get_comics?addons=1&list=series&list_option=&user_id=0&view=thumbs&format%5B%5D=1&format%5B%5D=5&date_type=&date=&date_end=&series_id={seriesid}&creators=0&character=&title=&order=date-desc&_={calendar.timegm(time.gmtime())}"
                response = requests.get(url,headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                volumeYear = 'UNKNOWN'
                try:
                    volumeYear = comicutil.getYearFromVolume(soup.find("div", {"class": "page-details"}).find("div", {"class": "header-intro"}).contents[2])
                except Exception as e:
                    pass
                issues = soup.find("ul", {"id": "comic-list-issues"}).find_all("li")
                for issue in issues:
                    comicTitle = issue.find("div", {"class": "title color-primary"})
                    description = ''
                    try:
                        description = issue.find("div", {"class": "comic-description"}).text
                    except:
                        pass
                    title = comicTitle.find('a').contents[0]
                    secondratio = fuzz.ratio(f"{comic_details.series} #{comic_details.issue}",comicutil.stripBadChars(title))
                    if secondratio > issueConfidence:
                        issueObject = {}
                        cover_image =  issue.find("div", {"class": "cover"}).find('a').find("img")['data-src']
                        if "medium-" in cover_image:
                            cover_image = cover_image.replace("medium","large")
                        issueObject['coverImage'] = cover_image
                        issueObject['volumeName'] = series.contents[0].strip()
                        issueObject['issueName'] =  title.strip()
                        issueObject['issueNumber'] = comicutil.get_issue_number(title)
                        issueObject['issueLink'] =  '{}{}'.format(baseUrl,comicTitle.find('a')['href'])
                        issueObject['volumeLink'] =  url
                        issueObject['publisher'] = comicdb.map_publisher(issue.find("div", {"class": "publisher color-offset"}).contents[0].strip())
                        issueObject['description'] = description
                        issueObject['storeDate'] = '000-00-00'
                        dateArray = issue.find("div", {"class": "details"}).find("span",{"class": "date"}).text.replace(',','').split()
                        try:
                            issueObject['storeDate'] = '{}-{}-{}'.format(dateArray[2],strptime(dateArray[0],'%b').tm_mon,dateArray[1][:-2])
                        except Exception as e:
                            pass
                            
                        issueObject['volumeId'] = series['href']
                        issueObject['issueId'] = comicTitle.find('a')['href']
                        issueObject['volumeYear'] = volumeYear
                        #issueObject['diamondSku'] = issue.find("span", {"class": "comic-diamond-sku"}).contents[0].strip()
                        issueObject['confidence'] = str(secondratio)
                        searchResults.append(issueObject)
    searchResults.sort(key=lambda x: int(x['confidence']),reverse = True)                    
    return searchResults

if __name__ == "__main__":
    #results = get_issue_by_id("https://leagueofcomicgeeks.com/comic/1717071/way-of-x-2")
    results = get_issue_by_id("https://leagueofcomicgeeks.com/comic/6599986/teenage-mutant-ninja-turtles-the-last-ronin-1")
    print(results)