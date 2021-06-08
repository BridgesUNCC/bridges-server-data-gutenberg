from app import app
from flask import request
from flask import send_file
import logging
from logging.handlers import RotatingFileHandler
import wget
import os
import json
import math
import time
import io
import shutil
import pickle
import gutenberg_cleaner
#import gutenberg
import xml.etree.ElementTree as ET
import requests
import difflib
import re
from flask import cli
import zipfile


index = [] # entries in the index are arrays where 0 is ID, 1 is title, 2 is lang, 3 is data_added, 4 is authors, 5 is genres, and 6 is loc class
titles = []

id_to_book = {}

@app.route('/search')
def data_search_request():
    search = request.args['search']
    search_type = request.args['type']

    try:
        strip = request.args['strip'].lower()
    except:
        strip = "true"


    data = lookup(search, search_type) #search for list of id's

    json_data = {"book_list": []}
    
    for i, d in enumerate(data):
        if i > 20:
            break
        book = {}
        book['id'] = d[0]
        book['title'] = d[1]
        book['lang'] = d[2]
        book['date_added'] = d[3]
        book['authors'] = d[4]
        book['genres'] = d[5]
        book['loc_class'] = d[6]

        '''url = f"https://www.gutenberg.org/cache/epub/{d[0]}/pg{d[0]}.txt"
        filename = f"app/books/{d[0]}.txt"

        error_404 = False
        if (not bookCheck(d[0])):
            response = requests.get(url)
            if response.status_code == 404: # Checks to see if book url 404s
                error_404 = True
            else:
                data = response.content.decode()
                #data = load_etext(d[0])
                x = open(filename, "w")
                x.write(data)
                x.close()

        if error_404 == False:
            LRU(d[0])
            f = open(filename, "r").read()

            if (strip == "true"):
                f = gutenberg_cleaner.simple_cleaner(f)
        else:
            f = 404



        book['text'] = f'''
        json_data["book_list"].append(book)



    return json.dumps(json_data)

@app.route('/')
def homepage():
    return "If you are reading this, you probably want to see the documentation of the gutenberg server at : https://github.com/BridgesUNCC/bridges-server-data-gutenberg"

'''@app.route('/index')
def searchIndex():
    output = ""

    if (len(request.args) > 0):
        try:
        # ToDo: set up type input 
            data = lookup(request.args['search'], request.args['filter'])
            for x in data:
                output = output + f"[{x[0]}, {x[1]}, {x[2]}, {x[3]}, {x[4]}], "
        except Exception as e:
            print(e)
    else:
        for x in index:
            output = output + f"[{x[0]}, {x[1]}, {x[2]}, {x[3]}, {x[4]}], "
    
    
    return output'''

@app.route('/book')
def downloadBook():
    num = int(request.args['id'])
    #check for strip parameter
    if 'strip' in request.args:
        strip = request.args['strip'].lower()
    else:
        strip = "true"
        
        
    url = f"https://www.gutenberg.org/cache/epub/{num}/pg{num}.txt"
    filename = f"app/books/{num}.txt"
    os.makedirs(f"app/books/", exist_ok=True)
        
    error_404 = False
    if (not bookCheck(num)):
        response = requests.get(url)
        if response.status_code == 404: # Checks to see if book url 404s
            error_404 = True
        else:
            data = response.content.decode()
            #data = load_etext(d[0])
            x = open(filename, "w")
            x.write(data)
            x.close()

    if error_404 == False:
        LRU(num)
        f = open(filename, "r").read()

        if (strip == "true"):
            f = gutenberg_cleaner.simple_cleaner(f)
    else:
        f = 404


    return f

@app.route('/meta') # returns meta data based on ID
def meta_id():
    starttime = time.time()
    book_id = int(request.args['id'])
    book_json = {"book_list": []}
    try:
        
        d = id_to_book[book_id]
    
        book = {}
        book['id'] = d[0]
        book['title'] = d[1]
        book['lang'] = d[2]
        book['date_added'] = d[3]
        book['authors'] = d[4]
        book['genres'] = d[5]
        book['loc_class'] = d[6]
        book_json["book_list"].append(book)
        
        endtime = time.time()
    
        print ("processing "+request.url+" in "+ '{0:.6f}'.format(endtime-starttime) +" seconds")
        return json.dumps(book_json)
    except:
        return "id does not exist" #this should change HTTP return code

def lookup(para, ind):
    if (ind == "id"):
        t = 0
    elif (ind == "title"):
        t = 1
    elif (ind == "language"):
        t = 2
    elif (ind == "date"):
        t = 3
    elif (ind == "author"):
        t = 4
    elif (ind == "genre"):
        t = 5
    elif (ind == "loc"):
        t = 6


    found = []

    #author list search
    if t == 4:
        for x in index:
            for auth in x[t]:
                flipAuth = auth.split(" ")
                flipAuthStr = f"{flipAuth[1]} {flipAuth[0]}"
                if (difflib.SequenceMatcher(None, para, auth).quick_ratio() >= .90 or difflib.SequenceMatcher(None, para, flipAuthStr).quick_ratio() >= .90):
                    found.append(x)
                else:
                    for i in auth.split(' '):
                        if para == i:
                            found.append(x)
    #genre list search
    elif t == 5 or t == 6: 
        for x in index:
            for genre in x[t]:
                ratio = difflib.SequenceMatcher(None, para, genre).quick_ratio()
                if (ratio >= .75):
                    found.append(x)
    
    else:
        start_time = time.time()

        for x in index:
            try:
                ratio = difflib.SequenceMatcher(None, para, x[t]).quick_ratio()
                for i in x[t].split(" "):
                    if i == para:
                        ratio = 1
                        break
            except:
                ratio = 0
            if (ratio >= .90):
                found.append(x)

        
        # found = process.extract(para, titles) Uses external library for attempted speed up

        ti = (time.time() - start_time)
        print(f"Time: {ti} seconds")
    return found
    
def parseIndex():
    root = "app/epub"

    count = 0

    print("Index Parsing Started:")
    print("Progress")
    pro = 0
    

    for subdirs, dirs, files in os.walk(root):
        for filename in files:
            filepath = subdirs + os.sep + filename

            if filepath.endswith(".rdf"):

                if (math.floor((count/62690)*100) > pro):
                    pro = pro + 10
                    print(f"{pro}%")


                # ID, TITLE, LANG, ISSUED, CREATORS, GENRES, LoC Class
                temp = [None, None, None, None, [], [], []]
                #TODO: Parse XML Files into index array
                tree = ET.parse(filepath)
                root = tree.getroot()
                #temp.append(root)

                for child in root:
                    if (child.tag.endswith("ebook")):
                        temp[0] = (child.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about").split('/')[1])
                        count = count + 1
                        for smallerchild in child:
                            if (smallerchild.tag.endswith("title")):
                                temp[1] = (smallerchild.text)
                            elif (smallerchild.tag.endswith("issued")):
                                temp[3] = (smallerchild.text)
                            elif (smallerchild.tag.endswith("language")):
                                temp[2] = smallerchild[0][0].text
                            elif (smallerchild.tag.endswith("subject")): #genre parse
                                for x in smallerchild[0]:
                                    if x.tag.endswith('value'):
                                        if len(x.text) <= 2:
                                            temp[6].append(x.text)
                                        else:
                                            temp[5].append(x.text)

                            elif (smallerchild.tag.endswith("creator")):
                                for agent in smallerchild:
                                    for terms in agent:
                                        if (terms.tag.endswith("name")):
                                            temp[4].append(terms.text)
                                
                                
                index.append(temp)
                root.clear() #GARBAGE COLLECTION
    print("Parse Complete")
    print(f"Total Text Count: {count}")


    store = {}

    for x in index:
        subStore = {'id' : x[0], 'title': x[1], 'language': x[2], 'date': x[3], 'authors': x[4], 'genres': x[5], 'loc_class': x[6]}
        store[str(x[0])] = subStore

    with open('index.json', 'w') as outfile:
        json.dump(store, outfile)

    store = None
    subStore = None

    return

def bookCheck(num):
    return os.path.exists(f"app/books/{num}.txt")

def loadIndex():
    if (os.path.isfile("index.json")):
        with open("index.json") as fp:
            indexJSON = json.load(fp)
            for key, value in indexJSON.items():
                temp = []
                temp.append(value['id'])
                temp.append(value['title'])
                temp.append(value['language'])
                temp.append(value['date'])
                temp.append(value['authors'])
                temp.append(value['genres'])
                temp.append(value['loc_class'])

                index.append(temp)
            indexJSON = {}
            fp.close
        print("Loaded index from local file")
        
    else:
        parseIndex()

    for x in index:
        id_to_book[int(x[0])] = x
        
    for x in index:
        titles.append(x[1])
    return

def LRU(key):
    lru = []
    #load lru
    if os.path.isfile("lru.json"):
        with open("lru.json") as f:
            lru = json.load(f)

    #checks if key is in LRU list
    if (key in lru):
        lru.remove(key)
    lru.insert(0, key)

    if (len(lru) == 200):
        if (os.path.isfile(f"app/books/{lru[len(lru) - 1]}.txt")):
            os.remove(f"app/books/{lru[len(lru) - 1]}.txt")
            del lru[len(lru) - 1]

    #save lru
    f = open("lru.json", "w")
    f.write(json.dumps(lru))
    f.close()
    return

def stingConditioning(regFilter):
    regFilter = regFilter.lower()
    temp = re.sub('[\'\n:;,./?!&]', '', regFilter)
    return temp


def downloadIndex():
    url = "https://www.gutenberg.org/cache/epub/feeds/catalog.rdf.zip"
    wget.download(url, )
    #response = request.get(url)
    print(response.ok)
    open("index_rdf.zip", 'wb').write(response.content)
    with zipfile.ZipFile("index_rdf.zip","r") as zip_ref:
        zip_ref.extractall("index")
    return


@app.cli.command('update')
def force_parse():
    os.remove("index.json")
    downloadIndex()
    parseIndex()
    return




@app.route('/hist')
def histogram_genre():
    hist = {}
    for x in index:
        for g in x[5]:
            if g in hist:
                hist[g] += 1
            else:
                hist[g] = 1


    hist = {k: v for k, v in sorted(hist.items(), key=lambda item: item[1], reverse=True)}


    string_hist =  ""
    for x in hist:
        string_hist = string_hist + f"{x}  :  {hist[x]}<br>"

    #return json.dumps(hist, indent=4)
    return string_hist

@app.route('/lochist')
def histogram_loc():
    hist = {}
    for x in index:
        for g in x[6]:
            if g in hist:
                hist[g] += 1
            else:
                hist[g] = 1


    hist = {k: v for k, v in sorted(hist.items(), key=lambda item: item[1], reverse=True)}


    string_hist =  ""
    for x in hist:
        string_hist = string_hist + f"{x}  :  {hist[x]}<br>"

    #return json.dumps(hist, indent=4)
    return string_hist

#setting up the server log
format = logging.Formatter('%(asctime)s %(message)s') 

logFile = 'log.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(format)
my_handler.setLevel(logging.ERROR)

app_log = logging.getLogger('root')
app_log.setLevel(level=logging.DEBUG)

app_log.addHandler(my_handler)

os.environ["GUTENBERG_MIRROR"] = 'http://www.gutenberg.org/dirs/'
loadIndex()
