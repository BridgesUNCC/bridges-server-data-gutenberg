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
import re
from flask import cli
import zipfile
import tarfile
from app import meta
from app import search


index = [] # entries in the index are arrays where 0 is ID, 1 is title, 2 is lang, 3 is data_added, 4 is authors, 5 is genres, and 6 is loc class
titles = []


@app.route('/search')
def data_search_request():
    mysearch = request.args['search']
    search_type = request.args['type']
    limit = 20
    
    try:
        strip = request.args['strip'].lower()
    except:
        strip = "true"

    start_time = time.time()


    data = search.lookup(mysearch, search_type) #search for list of id's

    ti = (time.time() - start_time)
    print(f"Time: {ti} seconds")

    
    json_data = {"book_list": []}
    
    for i, d in enumerate(data):
        if i > limit:
            break
        book = {}
        book['id'] = d[0]
        book['title'] = d[1]
        book['lang'] = d[2]
        book['date_added'] = d[3]
        book['authors'] = d[4]
        book['genres'] = d[5]
        book['loc_class'] = d[6]

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
    filename = f"app/books/{num}.json"
    os.makedirs(f"app/books/", exist_ok=True)
        
    error_404 = False
    if (not bookCheck(num)):
        response = requests.get(url)
        if response.status_code == 404: # Checks to see if book url 404s
            error_404 = True
        else:
            data = response.content.decode()
            with open(filename, 'w') as outfile:
                dict_json = {"book" : data}
                json.dump(dict_json, outfile)

    if error_404 == False:
        LRU(num)
        with open(filename) as json_file:
            f = json.load(json_file)

        if (strip == "true"):
            f["book"] = gutenberg_cleaner.simple_cleaner(f["book"])
    else:
        f = 404

    return json.dumps(f, indent = 4)

@app.route('/meta') # returns meta data based on ID
def meta_id():
    book_id = int(request.args['id'])
    starttime = time.time()
    ret = meta.get_meta_by_id(book_id)
    endtime = time.time()
        
    print ("processing "+request.url+" in "+ '{0:.6f}'.format(endtime-starttime) +" seconds")
    
    return ret
    
    
def parseIndex():
    root = "index\cache\epub"

    count = 0

    print("Index Parsing Started:")
    print("Progress")
    pro = 0
    
    '''
    index_dir = "index/catalog.rdf"

    
    tree = ET.parse(index_dir)
    root = tree.getroot()
    
    for child in root:

        #       ID, TITLE, LANG, ISSUED, CREATORS, GENRES, LoC Class
        temp = [None, None, None, None, [], [], []]
        if (child.tag.endswith("etext")):
            temp[0] = int(child.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID"].replace("etext", ""))
            for smallerchild in child:
                if (smallerchild.tag.endswith("title") and not smallerchild.tag.endswith("friendlytitle")):
                    temp[1] = (smallerchild.text.replace("\n", " "))
                elif (smallerchild.tag.endswith("language")):
                    temp[2] = (smallerchild[0][0].text)
                elif (smallerchild.tag.endswith("created")):
                    temp[3] = (smallerchild[0][0].text)
                elif (smallerchild.tag.endswith("creator")):
                    if (smallerchild.text != None): #checks for single value
                        temp[4].append(smallerchild.text)
                    else:
                        for agent in smallerchild:
                            if (agent.tag.endswith("li")):
                                temp[4].append(agent.text)

                elif (smallerchild.tag.endswith("subject")):
                    for i in smallerchild:
                        if(i.tag.endswith("LCC")):
                            temp[6].append(i[0].text)
                        elif (i.tag.endswith("LCSH")):
                            temp[5].append(i[0].text)
                        elif (i.tag.endswith("Bag")):
                            for x in i:
                                temp[5].append(x[0][0].text)


            index.append(temp)
            count = count + 1
    print("Parse Complete")
    print(f"Total Text Count: {count}")

    '''

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

    meta.build_index()
    search.build_index()

    
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
    url = "https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.zip"
    if (os.path.isdir("/index")):
        os.rmdir("/index")
    index_dir = wget.download(url)
    #response = request.get(url)
    with zipfile.ZipFile(index_dir,"r") as zip_ref:
        zip_ref.extractall("index")
    os.remove("rdf-files.tar.zip")

    my_tar = tarfile.open('index/rdf-files.tar')
    my_tar.extractall('./index') # specify which folder to extract to
    my_tar.close()
    return

@app.cli.command('update')
def force_parse():
    os.remove("index.json")
    downloadIndex()
    parseIndex()
    shutil.rmtree("index")
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
