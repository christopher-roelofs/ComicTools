from os import write
import requests
import urllib
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from time import strptime
import re
import comicutil
import comicdb


showFuture = False

urls = {'base': 'https://www.comixology.com',
        'search':
        {'searchBasic': 'https://www.comixology.com/search?search={}',
         'searcCollectionsUrl': 'https://www.comixology.com/search/items?search={}&subType=COLLECTIONS',
         'searchSeriesUrl': 'https://www.comixology.com/search/series?search={}',
         'searchIssuesUrl': 'https://www.comixology.com/search/items?search={}&subType=SINGLE_ISSUES',
         'SearchcomingSoonUrl': 'https://www.comixology.com/search/items?search={}&subType=comingsoon'}
        }

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def getIssueNumberFromName(name):
    if "#" in name:
        split = name.split()
        for part in split:
            if "#" in part:
                return re.sub("[^0-9]", "", part)
        return "UNKNOWN"
    else:
        return "UNKNOWN"

def get_name(name):
    return re.sub(r" ?\([^)]+\)", "", name)

def fix_name(name):
    part1 = name.partition(" (")[0]
    part2 = re.split("#[0-999]",name,1)[-1]
    return f"{part1}{part2}"

def getYearFromName(name):
    try:
        #return re.search('\d{4}',name).group()
        return re.findall('\d{4}',name)[-1]
    except:
        return "UNKNOWN"

def get_year(string):
    try:
        year = string.split("(")[1].replace(")","")
        if not bool(re.search(r'\d', year)):
            return "UNKNOWN-UNKNOWN"
        else:
            return year
        return 
    except:
        return "UNKNOWN-UNKNOWN"

def get_issue_by_id(id):
    return {}

def get_series_by_id(id):
    searchResults = []
    response = requests.get(id, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    page_count = 1
    try:
        page_count = re.sub("[^0-9]", "",soup.find("div", {"class": "pager-jump-container"}).contents[4])
    except:
        pass
    for n in range(int(page_count)):
        url = f"{id}?Issues_pg={n+1}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find("div", {"class": "list Issues"}).find_all("li", {"class": "content-item"})
        for result in results:
            link = result.find("a", {"class": "content-img-link"})['href']
            name = result.find("h5", {"class": "content-title"}).contents[0].partition('(')[0].strip()
            volume = result.find("h5", {"class": "content-title"}).contents[0].partition('(')[0].strip()
            coverImageBase = result.find("img", {"class": "content-img"})['src'].split('https://images-na.ssl-images-amazon.com/images/S/cmx-images-prod/Item/')
            coverImageMedium = 'https://images-na.ssl-images-amazon.com/images/S/cmx-images-prod/Item/{}'.format(urllib.parse.quote(coverImageBase[1]))
            coverImageLarge = coverImageMedium.replace('SX312','SX360')
            coverImageSmall = coverImageMedium.replace('SX312','SX170')
            credits = []
            try:
                name = '{} {}'.format(name,result.find("h6", {"class": "content-subtitle"}).contents[0].strip('Issue ').partition('(')[0].strip())
            except Exception as e:
                pass
            if 'Bundle' not in name:
                response = requests.get(link, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                description = ""
                try:
                    description = soup.find("section", {"class": "item-description"}).text.replace("\n","").replace("\r","").replace("\t","")
                except:
                    pass
                publisher = soup.find("h3", {"title": "Publisher"}).contents[0].strip()
                credits_section = soup.find("div", {"class": "credits"})
                for credit in credits_section:
                    try:
                        c = {}
                        c["person"] = credit.find("h2").text.strip()
                        role = credit.find("h2")['title']
                        if "art" in role.lower():
                            role = "Artists"
                        if "written" in role.lower():
                            role = "Writer"
                        if "cover" in role.lower():
                            role = "Cover Artist"
                        if "pencil" in role.lower():
                            role = "Penciler"
                        if "colored" in role.lower():
                            role = "Colorist"
                        c["role"] = role
                        if c not in credits:
                            credits.append(c)
                    except:
                        pass
                genre_list = []
                genres = ""
                asgroup = soup.find_all("a")
                for a in asgroup:
                    try:
                        if "comics-genre" in a["href"]:
                            genre_list.append(a.text.strip())
                    except:
                        pass
                if len(genre_list) > 0:
                    genres = ", ".join(genre_list)
                aboutTitle = soup.find_all("h4", {"class": "subtitle"})
                aboutText = soup.find_all("div", {"class": "aboutText"})
                breadcrumb = soup.find("div", {"class": "breadcrumb"})
                publisherLInk = crubms = breadcrumb.find_all('a')[1]
                volumeLink = breadcrumb.find_all('a')[2]['href'].partition('?')[0]
                pageCount = aboutText[0].contents[0].strip().replace(" Pages","")
                printDate = aboutText[1].contents[0].strip()
                digitalDate = aboutText[2].contents[0].strip()
                ageRating = aboutText[3].contents[0].strip()
                issueObject = {}
                issueObject['coverImageMedium'] = coverImageMedium
                issueObject['coverImageSmall'] = coverImageSmall
                issueObject['coverImage'] = coverImageLarge
                issueObject['volumeName'] = volume
                issueObject['issueName'] =  get_name(soup.find("h1", {"itemprop": "name"}).contents[0])
                issueObject['issueNumber'] = getIssueNumberFromName(soup.find("h1", {"itemprop": "name"}).contents[0])
                issueObject['issueLink'] =  link.partition('?')[0]
                issueObject['volumeLink'] =  volumeLink
                issueObject['volumeYear'] = getYearFromName(breadcrumb.find_all('a')[2].find('h3').contents[0].strip())
                issueObject['publisher'] = comicdb.map_publisher(publisher)
                issueObject['credits'] = credits
                issueObject['description'] = description
                issueObject['genres'] = genres
                issueObject['page_count'] = pageCount
                dateArray = printDate.split()
                issueObject['storeDate'] = '{}-{}-{}'.format(dateArray[2],dateArray[1],strptime(dateArray[0],'%B').tm_mon)
                issueObject['volumeId'] = volumeLink.strip(urls["base"])
                issueObject['issueId'] = link.partition('?')[0].strip(urls["base"])
                searchResults.append(issueObject)
    return searchResults
    

def search_series(query,volumeConfidence=0,issueConfidence=0):
    comic_details = comicutil.get_comic_details(query)
    searchResults = []
    url = urls["search"]["searchSeriesUrl"]
    response = requests.get(url.format(urllib.parse.quote(query)), headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all("li", {"class": "content-item"})
    for result in results:
        link = result.find("a", {"class": "content-img-link"})['href']
        name = result.find("h5", {"class": "content-title"}).contents[0].partition('(')[0].strip()
        volume = result.find("h5", {"class": "content-title"}).contents[0].partition('(')[0].strip()
        coverImageBase = result.find("img", {"class": "content-img"})['src'].split('https://images-na.ssl-images-amazon.com/images/S/cmx-images-prod/Series/')
        coverImageMedium = 'https://images-na.ssl-images-amazon.com/images/S/cmx-images-prod/Series/{}'.format(urllib.parse.quote(coverImageBase[1]))
        coverImageLarge = coverImageMedium.replace('SX312','SX360')
        coverImageSmall = coverImageMedium.replace('SX312','SX170')
        if 'Bundle' not in name:
            ratio = fuzz.ratio(comicutil.stripBadChars(name),f"{comic_details.series} #{comic_details.issue}")
            if ratio > issueConfidence:
                response = requests.get(link, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                #description = soup.find("section", {"class": "item-description"}).contents[2]
                year = get_year(soup.find("div", {"class": "title"}).find("h1", {"itemprop": "name"}).contents[0])
                try:
                    if year.split("-")[1] == "":
                        year = year +  "PRESENT"
                except:
                    pass
                end_year = "PRESENT"
                try:
                    if year.split("-")[1] != "":
                        end_year = year.split("-")[1]
                except:
                    pass
                start_year = "UNKNOWN"
                try:
                    start_year = year.split("-")[0]
                except:
                    pass
                publisher = soup.find("h3", {"title": "Publisher"}).contents[0].strip()
                aboutTitle = soup.find_all("h4", {"class": "subtitle"})
                aboutText = soup.find_all("div", {"class": "aboutText"})
                breadcrumb = soup.find("div", {"class": "breadcrumb"})
                publisherLInk = crubms = breadcrumb.find_all('a')[1]
                volumeLink = link.partition('?')[0]
                issueObject = {}
                issueObject['coverImageMedium'] = coverImageMedium
                issueObject['coverImageSmall'] = coverImageSmall
                issueObject['coverImage'] = coverImageLarge
                issueObject['volumeName'] = volume
                issueObject['issueName'] =  name
                issueObject['name'] = name
                issueObject["issue_count"] = "UNKNOWN"
                issueObject['link'] = link.partition('?')[0]
                issueObject['year'] = year
                issueObject['start_year'] = year.split("-")[0]
                issueObject['end_year'] = end_year
                issueObject['issueNumber'] = getIssueNumberFromName(name)
                issueObject['issueLink'] =  link.partition('?')[0]
                issueObject['volumeLink'] =  volumeLink
                issueObject['volumeYear'] = start_year
                issueObject['publisher'] = comicdb.map_publisher(publisher)
                issueObject['volumeId'] = volumeLink.strip(urls["base"])
                issueObject['issueId'] = link.partition('?')[0].strip(urls["base"])
                issueObject['confidence'] = str(ratio)
                issueObject['id'] = link.partition('?')[0]
                searchResults.append(issueObject)
    #searchResults.sort(key=lambda x: int(x['confidence']),reverse = True)
    return searchResults

def search_comics(query,volumeConfidence=0,issueConfidence=0):
    comic_details = comicutil.get_comic_details(query)
    urlList = [urls['search']['searchIssuesUrl'],urls['search']['searcCollectionsUrl']]
    if showFuture:
        urlList.append(urls['search']['SearchcomingSoonUrl'])
    searchResults = []
    for url in urlList:
        response = requests.get(url.format(urllib.parse.quote(query)), headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all("li", {"class": "content-item"})
        for result in results:
            link = result.find("a", {"class": "content-img-link"})['href']
            name = result.find("h5", {"class": "content-title"}).contents[0].partition('(')[0].strip()
            volume = result.find("h5", {"class": "content-title"}).contents[0].partition('(')[0].strip()
            coverImageBase = result.find("img", {"class": "content-img"})['src'].split('https://images-na.ssl-images-amazon.com/images/S/cmx-images-prod/Item/')
            coverImageMedium = 'https://images-na.ssl-images-amazon.com/images/S/cmx-images-prod/Item/{}'.format(urllib.parse.quote(coverImageBase[1]))
            coverImageLarge = coverImageMedium.replace('SX312','SX360')
            coverImageSmall = coverImageMedium.replace('SX312','SX170')
            try:
                name = '{} {}'.format(name,result.find("h6", {"class": "content-subtitle"}).contents[0].strip('Issue ').partition('(')[0].strip())
            except Exception as e:
                pass
            if 'Bundle' not in name:
                ratio = fuzz.ratio(comicutil.stripBadChars(name),f"{comic_details.series} #{comic_details.issue}")
                if ratio > issueConfidence:
                    response = requests.get(link, headers=headers)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    writers = []
                    try:
                        ws = soup.find_all("h2", {"title": "Written by"})
                        for writer in ws:
                            writers.append(writer.find("a").contents[0].strip())
                    except:
                        pass
                    #description = soup.find("section", {"class": "item-description"}).contents[2]
                    publisher = soup.find("h3", {"title": "Publisher"}).contents[0].strip()
                    artists = []
                    try:
                        ars = soup.find_all("h2", {"title": "Art by"})
                        for artist in ars:
                            artists.append(artist.find('a').contents[0].strip())
                    except:
                        pass
                    coverartists = []
                    try:
                        cas = soup.find_all("h2", {"title": "Cover by"})
                        for coverartist in cas:
                            coverartists.append(coverartist.find('a').contents[0].strip())
                    except:
                        pass
                    year = get_year(soup.find("div", {"id": "column2"}).find("h1", {"class": "title"}).contents[0])
                    try:
                        if year.split("-")[1] == "":
                            year = year +  "PRESENT"
                    except:
                        pass
                    end_year = "PRESENT"
                    try:
                        if year.split("-")[1] != "":
                            end_year = year.split("-")[1]
                    except:
                        pass
                    start_year = "UNKNOWN"
                    try:
                        start_year = year.split("-")[0]
                    except:
                        pass
                    aboutTitle = soup.find_all("h4", {"class": "subtitle"})
                    aboutText = soup.find_all("div", {"class": "aboutText"})
                    breadcrumb = soup.find("div", {"class": "breadcrumb"})
                    publisherLInk = crubms = breadcrumb.find_all('a')[1]
                    volumeLink = breadcrumb.find_all('a')[2]['href'].partition('?')[0]
                    pageCount = aboutText[0].contents[0].strip().replace(" Pages","")
                    printDate = aboutText[1].contents[0].strip()
                    digitalDate = aboutText[2].contents[0].strip()
                    ageRating = aboutText[3].contents[0].strip()
                    issueObject = {}
                    issueObject['coverImageMedium'] = coverImageMedium
                    issueObject['coverImageSmall'] = coverImageSmall
                    issueObject['coverImage'] = coverImageLarge
                    issueObject['volumeName'] = volume
                    issueObject['issueName'] =  name
                    issueObject['issueNumber'] = getIssueNumberFromName(name)
                    issueObject['issueLink'] =  link.partition('?')[0]
                    issueObject['volumeLink'] =  volumeLink
                    issueObject['volumeYear'] = start_year
                    issueObject['publisher'] = comicdb.map_publisher(publisher)
                    issueObject['writers'] = writers
                    issueObject['artists'] = artists
                    issueObject['covertartists'] = coverartists
                    dateArray = printDate.split()
                    issueObject['storeDate'] = '{}-{}-{}'.format(dateArray[2],dateArray[1],strptime(dateArray[0],'%B').tm_mon)
                    issueObject['volumeId'] = volumeLink.strip(urls["base"])
                    issueObject['issueId'] = link.partition('?')[0].strip(urls["base"])
                    issueObject['confidence'] = str(ratio)
                    searchResults.append(issueObject)
    return searchResults


if __name__ == "__main__":
    results = get_series_by_id("https://www.comixology.com/The-Walking-Dead-Deluxe/comics-series/148151?ref=Y29taWMvdmlldy9kZXNrdG9wL2JyZWFkY3J1bWJz")
    print(results)

