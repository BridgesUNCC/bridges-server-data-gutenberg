from app import app
from flask import request
from flask import send_file
from flask import jsonify
import logging
from logging.handlers import RotatingFileHandler
import wget
import os
import sys
import time
import json
import math
from datetime import datetime
import shutil
import gutenberg_cleaner

import epub_conversion
from epub_conversion.utils import open_book, convert_epub_to_lines

import xml.etree.ElementTree as ET
import requests
import re
from flask import cli
import zipfile
import tarfile
from app import meta
from app import search
from werkzeug.exceptions import HTTPException
from apscheduler.schedulers.background import BackgroundScheduler


index = [] # entries in the index are arrays where 0 is ID, 1 is title, 2 is lang, 3 is data_added, 4 is authors, 5 is genres, and 6 is loc class
titles = []
log_sep = "_________________________________________"

if os.getenv("META_MAXLIMIT") is not None:
    maxLimit = int(os.getenv("META_MAXLIMIT"))
else:
    maxLimit = 1000

if os.getenv("META_DEFAULT") is not None:
    defaultLimit = int(os.getenv("META_DEFAULT"))
else:
    defaultLimit = 20



""" Search Route
    get:
        summary: search book index
        description: Searches the index of books for matching terms then returns a json list
        path: /search
        parameters:
            search (String): the string you want to search the index for
            type (String): the string representing the category you want to search through (id, title, language, date, author, genre, loc)
            limit (int): (OPTIONAL) set the amount of responses you want to get back

        responses:
            200:
                description: a json string object that contains a list of found books' meta data
"""
@app.route('/search')
def data_search_request():
    app_log.info(log_sep)
    mysearch = request.args['search']
    search_type = request.args['type']
    if ("limit" in request.args):
        metaLimit = int(request.args["limit"])
    else:
        metaLimit = defaultLimit

    if (metaLimit <= 0):
        metaLimit = defaultLimit
    elif (metaLimit > maxLimit):
        metaLimit = maxLimit
    
    start_time = time.time()

    
    data = search.lookup(mysearch, search_type) #search for list of id's

    ti = (time.time() - start_time)
    print(f"Time: {ti} seconds")

    
    json_data = {"book_list": []}
    
    for i, d in enumerate(data):
        if i >= metaLimit:
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



    #return json.dumps(json_data)
    return jsonify(json_data)

""" Book Route

    get:
        summary: Book text return
        description: Returns the book text of a certain id
        path: /book
        parameters:
            id (int): the id of a book you want the text of
            strip (String): (OPTIONAL), true(default) or false,  cleans up the returned book text to remove all Gutenberg header and footer data

        responses:
            200:
                description: json string: returns the book text within a json string object
"""
@app.route('/book')
def downloadBook():
    app_log.info(log_sep)
    dict_json = {}
    num_arg = request.args['id'].split(",")
    map_obj = map(int, num_arg)
    num_list = list(map_obj)
    os.makedirs(f"app/books/", exist_ok=True)
    #check for strip parameter (optional)
    if 'strip' in request.args:
        strip = request.args['strip'].lower()
    else:
        strip = "true"
        
    for num in num_list:
        url = f"https://www.gutenberg.org/cache/epub/{num}/pg{num}.txt"
        filename = f"app/books/{num}.json"
        if (not(bookCheck(num))):
            try:
                response = requests.get(url)
                if (response.status_code == 404): #if txt file doesnt exsist, check for epub
                    response = requests.get(f"https://www.gutenberg.org/cache/epub/{num}/pg{num}.epub")
                    response.raise_for_status()
                    app_log.info("Converting epub...")
                    print("Converting epub...")
                    os.makedirs(f"app/tmp/", exist_ok=True)
                    with open("app/tmp/temp.epub", "wb") as f:
                        f.write(response.content)
                        f.close()
                    book = open_book("app/tmp/temp.epub")
                    lines = convert_epub_to_lines(book)
                    data = ' '.join(lines)
                    book.close()
                    cleanr = re.compile('<.*?>') #removes html encoding
                    data = re.sub(cleanr, '', data)
                    shutil.rmtree("app/tmp")

                else:
                    response.raise_for_status()
                    data = response.content.decode()

            except requests.exceptions.HTTPError as a:
                app_log.info(a)
                return a
            except requests.exceptions.RequestException as e:
                app_log.info(e)
                return e
            
            
            with open(filename, 'w') as outfile:
                dict_json[str(num)] = data
                temp = {}
                temp[str(num)] = data
                json.dump(temp, outfile)
                LRU(num)
        else:
            LRU(num)
            with open(filename) as json_file:
                dict_json.update(json.load(json_file))
    
        if (strip == "true"):
            for book_text in dict_json:
                dict_json[book_text] = gutenberg_cleaner.simple_cleaner(dict_json[book_text])


    #return json.dumps(f, indent = 4)
    return jsonify(dict_json)

""" Meta Route
    get:   
        summary: Individual meta data return
        description: Returns the meta data associated with a book id
        path: /meta
        parameters:
            id(int): the id of a book you want the meta data of

        responses:
            200:
                description: a json string object containing the books meta data
"""
@app.route('/meta')
def meta_id():
    app_log.info(log_sep)
    book_id = int(request.args['id'])
    starttime = time.time()
    ret = meta.get_meta_by_id(book_id)
    endtime = time.time()
        
    print ("processing "+request.url+" in "+ '{0:.6f}'.format(endtime-starttime) +" seconds")
    
    return jsonify(ret)

""" Parse the downloaded raw rdf index files

        Parameters:
            None

        Return:
            None
"""
def parseIndex():
    root = "index\cache\epub"

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
                
                Sound_Check = None
                
                for child in root.iter():
                    if child.tag.endswith("ebook"):
                        temp[0] = list(child.attrib.values())[0].split('/')[1]
                        
                    if (child.tag.endswith("title")):
                        temp[1] = (child.text)
                    elif (child.tag.endswith("issued")):
                        temp[3] = (child.text)
                    elif (child.tag.endswith("language")):
                        temp[2] = child[0][0].text
                    elif (child.tag.endswith("value") and (child.text == "Text")):  #Sound for audio books
                        Sound_Check = child.text
                    elif (child.tag.endswith("subject")): #genre parse
                        for x in child[0]:
                            if x.tag.endswith('value'):
                                if len(x.text) <= 2:
                                    temp[6].append(x.text)
                                else:
                                    temp[5].append(x.text)

                    elif (child.tag.endswith("creator")):
                        for agent in child:
                            for terms in agent:
                                if (terms.tag.endswith("name")):
                                    temp[4].append(terms.text)

                if Sound_Check == None:
                    continue

                index.append(temp)
                count = count + 1
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

""" Checks local storage for saved book text

        Parameters:
            num(int): the id of the book to look up

        Return:
            boolean: returns if the book exists or not
"""
def bookCheck(num):
    return os.path.exists(f"app/books/{num}.json")

""" Loads the locally saved index file

        Parameters:
            None

        Return:
            None
"""
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
        force_parse()

    meta.build_index()
    search.build_index()

    
    for x in index:
        titles.append(x[1])
    return

""" Updates the LRU of book texts

        Parameters:
            key(String): the unique identifier for a books text

        Return:
            None
"""
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
        if (os.path.isfile(f"app/books/{lru[len(lru) - 1]}.json")):
            os.remove(f"app/books/{lru[len(lru) - 1]}.json")
            del lru[len(lru) - 1]

    #save lru
    f = open("lru.json", "w")
    f.write(json.dumps(lru))
    f.close()
    return

""" Cleans up a given string by removing special characters

        Parameters:
            regFilter(String): the text that is to be conditioned

        Return:
            String: conditioned string
"""
def stingConditioning(regFilter):
    regFilter = regFilter.lower()
    temp = re.sub('[\'\n:;,./?!&]', '', regFilter)
    return temp

""" Downloads and unpacks the most recent Index of Gutenberg Books

        Parameters:
            None

        Return:
            None
"""
def downloadIndex():
    url = "https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.zip" # url to compressed index file, contains rdf files for each book
    if (os.path.isdir("/index")):
        os.rmdir("/index")
    index_dir = wget.download(url)
    with zipfile.ZipFile(index_dir,"r") as zip_ref:   # unzips file
        app_log.info("Uncompressing Index Files (May take awhile)")
        zip_ref.extractall("index")
    os.remove("rdf-files.tar.zip")

    my_tar = tarfile.open('index/rdf-files.tar')
    my_tar.extractall('./index') # specify which folder to extract to
    my_tar.close()
    return

""" Command Line Interface to delete, download, and reparse the index of Gutenberg books

        Parameters:
            None

        Return:
            None
"""
@app.cli.command('update')
def force_parse():
    app_log.info(log_sep)
    app_log.info("Index Update Starting...")
    if (os.path.exists("index.json")):
        os.remove("index.json") # removes old index
    downloadIndex()
    parseIndex()
    shutil.rmtree("index") # removes large raw index data
    app_log.info("Index Updated")
    return

""" Hist Route
    get:   
        summary: Genre histogram
        description: Returns a numerical histogram of the genres in the index
        path: /hist
        parameters:
            None

        responses:
            200:
                description: json string object containing an ordered histogram of the occurences of genres
"""
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


    '''string_hist =  ""
    for x in hist:
        string_hist = string_hist + f"{x}  :  {hist[x]}<br>"
    '''
    #return json.dumps(hist, indent=4)
    return jsonify(hist)

""" lochist route
    get:   
        summary: Library of Congress histogram
        description: Returns a numerical histogram of the library of congress(loc) tags in the index
        path: /lochist
        parameters:
            None

        responses:
            200:
                description: json string object containing an ordered histogram of the occurences of loc genres
"""
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

""" Command Line Interface to remove the local cache of books

        Parameters:
            None

        Return:
            None
"""
@app.cli.command('clear')
def clear_cache():
    shutil.rmtree("app/books")
    os.mkdir("app/books")
    os.remove("lru.json")
    return

'''@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    app_log.info(e)
'''

def auto_update_check():
    time_created = datetime.fromtimestamp(os.path.getmtime("index.json"))
    delta = datetime.now() - time_created
    if delta.days > 30:
        app_log.info("Index Update Starting...")
        if (os.path.exists("index.json")):
            os.remove("index.json") # removes old index
        downloadIndex()
        parseIndex()
        shutil.rmtree("index") # removes large raw index data
        app_log.info("Index Updated")
    return




#setting up the server log
format = logging.Formatter('%(asctime)s %(message)s') 

logFile = 'log.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(format)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('root')
app_log.setLevel(level=logging.INFO)

app_log.addHandler(my_handler)


scheduler = BackgroundScheduler()
scheduler.add_job(func=auto_update_check, trigger='interval', hours=6)
scheduler.start()


#logging.basicConfig(format='%(asctime)s: %(message)s', filename='log.log', encoding='utf-8', level=logging.INFO)
#logging.info('Server Start Up')


os.environ["GUTENBERG_MIRROR"] = 'http://www.gutenberg.org/dirs/'
loadIndex()
