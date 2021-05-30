import requests
import urllib
import json
import re
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from datetime import datetime as dt
import datetime
import comicutil
import comicdb
import config

SETTINGS = config.get_config() 


apikey = SETTINGS["comicvine_key"]
userAgent = 'comicpanda'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
minimumConfidence = 0

def get_issue_details(url):
    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find("p", {"class": "wiki-descriptor"}).find_all("a")
    publisher = results[2].contents[0].strip()
    details = {}
    details["publisher"] = publisher
    return details

def get_volume_details(url):
    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find("p", {"class": "wiki-descriptor"})
    volume_year = results.text.strip().split()[-1].replace(".","")
    details = {}
    details["volumeYear"] = volume_year
    return details

def getIssueById(id):
    url = 'http://comicvine.gamespot.com/api/issue/4000-{}/?api_key={}&format=json'.format(id,apikey)
    response = requests.get(url,headers=headers)
    jsonResponse = json.loads(response.text)
    return jsonResponse['results']

def get_issue_by_id(id): #example "125226"
    url = 'http://comicvine.gamespot.com/api/issue/4000-{}/?api_key={}&format=json'.format(id,apikey)
    response = requests.get(url,headers=headers)
    jsonResponse = json.loads(response.text)
    results = jsonResponse['results']
    store_date = "UNKNOWN"
    try:
        store_date = results['store_date']
    except:
        pass
    try:
        if results['cover_date'] != None:
            store_date = results['cover_date']
    except:
        pass
    description = ""
    if "description" in results:
        soup = BeautifulSoup(results["description"], 'html.parser')
        description = soup.get_text()
        #description = re.sub('<[^<]+?>', '',results["description"])

    credits = []
    if "person_credits" in results:
        for credit in results["person_credits"]:
            c = {}
            c["role"] = credit["role"]
            c["person"] = credit["name"]
            credits.append(c)
    issueObject = {}
    issueObject['coverImage'] = results["image"]['super_url']
    issueObject['issueName'] =  f'{results["volume"]["name"]} #{results["issue_number"]}'
    issueObject['issueNumber'] = results["issue_number"]
    issueObject['storeDate'] = store_date
    issueObject['description'] = description
    issueObject['credits'] = credits
    issueObject['page_count'] = ""
    return issueObject

def getVolumeById(id):
    url = 'http://comicvine.gamespot.com/api/volume/4050-{}/?api_key={}&format=json'.format(id,apikey)
    response = requests.get(url,headers=headers)
    jsonResponse = json.loads(response.text)
    return jsonResponse['results']

def get_series_by_id(id): # example "20701"
    url = 'http://comicvine.gamespot.com/api/volume/4050-{}/?api_key={}&format=json'.format(id,apikey)
    response = requests.get(url,headers=headers)
    jsonResponse = json.loads(response.text)
    issue_list = []
    for result in jsonResponse['results']["issues"]:
        issueObject = {}
        issueObject['id'] = result["id"]
        issueObject['issueLink'] =  result["site_detail_url"]
        issueObject['issueNumber'] = result["issue_number"]
        issue_list.append(issueObject)
    return issue_list

def search_series(query,volumeConfidence=0,issueConfidence=0):
    encodedSearch = urllib.parse.quote(query)
    headers = { 'User-Agent': userAgent }
    url = 'https://comicvine.gamespot.com/api/search/?api_key={}&format=json&sort=name:asc&resources=volume&query={}&field_list=site_detail_url,name,id,start_year,publisher,image,description,count_of_issues&limit=100'.format(apikey,encodedSearch)
    response = requests.get(url,headers=headers)
    jsonResponse = json.loads(response.text)
    results = []
    for result in jsonResponse['results']:
        try:
            ratio = fuzz.ratio(result['name'],query)
            if ratio > volumeConfidence:
                series = {}
                end_year = "UNKNOWN"
                if "end_year" in result:
                    if result["end_year"] != None:
                        end_year = result["end_year"]
                start_year = "UNKNOWN"
                if "start_year" in result:
                    if result["start_year"] != None:
                        start_year = result["start_year"]
                publisher = "UNKNOWN"
                if "publisher" in result:
                    if result["publisher"] != None:
                        publisher = result["publisher"]["name"]
                series["name"] = result["name"]
                series["issue_count"] = result["count_of_issues"]
                series["publisher"] = comicdb.map_publisher(publisher)
                series["link"] =  result['site_detail_url']
                series['year'] = f'{result["start_year"]}-{end_year}'
                series['start_year'] = result["start_year"]
                series['volumeYear'] = result["start_year"]
                series["volumeName"] = result["name"]
                series['end_year'] = end_year
                series["confidence"] = ratio
                series['id'] = result["id"]
                results.append(series)
        except Exception as e:
            pass
    results.sort(key=lambda x: int(x['confidence']),reverse = True)
    return results

def search_issue(query):
    encodedSearch = urllib.parse.quote(query)
    headers = { 'User-Agent': userAgent }
    url = 'https://comicvine.gamespot.com/api/search/?api_key={}&limit=100&format=json&sort=name:asc&resources=volume&query={}&field_list=name,id,start_year,publisher,image,description,count_of_issues&limit=100'.format(apikey,encodedSearch)
    response = requests.get(url,headers=headers)
    jsonResponse = json.loads(response.text)
    return jsonResponse['results']

def search_comics(query,volumeConfidence=0,issueConfidence=0):
    comic_details = comicutil.get_comic_details(query)
    encodedSearch = ''
    if query != None:
        encodedSearch = urllib.parse.quote(f"{comic_details.series} #{comic_details.issue} ({comic_details.year})")
    headers = { 'User-Agent': userAgent }
    url = 'https://comicvine.gamespot.com/api/search/?api_key={}&limit=100&format=json&sort=name:asc&resources=issue&query={}'.format(apikey,encodedSearch)
    response = requests.get(url,headers=headers)
    jsonResponse = json.loads(response.text)
    responseArray = []
    for result in jsonResponse['results'][:40]:
        ratio = fuzz.ratio(comicutil.stripBadChars(f"{result['volume']['name']} {result['issue_number']}"), f"{comic_details.series} #{comic_details.issue}")
        if ratio > minimumConfidence:
            volume_details = getVolumeById(result['volume']['id'])
            store_date = result['store_date']
            if store_date == None:
                store_date = result['cover_date']
            comic = {}
            comic['coverImage'] = result['image']['super_url']
            comic['volumeName'] = result['volume']['name']
            comic['issueName'] =  f"{result['volume']['name']} #{result['issue_number']}"
            comic['issueNumber'] = result['issue_number']
            comic['issueLink'] =  result['site_detail_url']
            comic['volumeLink'] =  result['volume']["site_detail_url"]
            comic['publisher'] =  comicdb.map_publisher(volume_details["publisher"]["name"])
            comic['storeDate'] = store_date
            comic['volumeId'] = result['volume']['id']
            comic['issueId'] = result['id']
            comic['volumeYear'] = volume_details["start_year"]
            comic['confidence'] = str(ratio)
            responseArray.append(comic)
    responseArray.sort(key=lambda x: int(x['confidence']),reverse = True)
    return responseArray

def search_comics_old(query,volumeConfidence=0,issueConfidence=0):
    encodedSearch = ''
    if query != None:
        encodedSearch = urllib.parse.quote(query)
    headers = { 'User-Agent': userAgent }
    url = 'https://comicvine.gamespot.com/api/search/?api_key={}&limit=100&format=json&sort=name:asc&resources=issue&query={}'.format(apikey,encodedSearch)
    response = requests.get(url,headers=headers)
    jsonResponse = json.loads(response.text)
    responseArray = []
    for result in jsonResponse['results'][:40]:
        ratio = fuzz.ratio(f"{result['volume']['name']} {result['issue_number']}", query)
        if ratio > minimumConfidence:
            issue_details = get_issue_details(result["site_detail_url"])
            volume_details = get_volume_details(result['volume']['site_detail_url'])
            store_date = ""
            if result['store_date'] is not None:
                store_date = result['store_date']
            comic = {}
            comic['coverImage'] = result['image']['super_url']
            comic['volumeName'] = result['volume']['name']
            comic['issueName'] =  f"{result['volume']['name']} #{result['issue_number']}"
            comic['issueNumber'] = result['issue_number']
            comic['issueLink'] =  result['site_detail_url']
            comic['volumeLink'] =  result['volume']["site_detail_url"]
            comic['publisher'] =  issue_details["publisher"]
            comic['storeDate'] = store_date
            comic['volumeId'] = result['volume']['id']
            comic['issueId'] = result['id']
            comic['volumeYear'] = volume_details["volumeYear"]
            comic['confidence'] = str(ratio)
            responseArray.append(comic)
    responseArray.sort(key=lambda x: int(x['confidence']),reverse = True)
    return responseArray
#134304
if __name__ == "__main__":
    results = get_series_by_id('20701')

 
    
 
