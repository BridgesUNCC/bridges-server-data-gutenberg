from app import app
from flask import request
from flask import send_file
import logging
from logging.handlers import RotatingFileHandler
import wget
import os
import json
import math
import io
import shutil
import gutenberg_cleaner
import gutenberg
import xml.etree.ElementTree as ET
import requests

index = []

@app.route('/index')
def searchIndex():
    output = ""
    try:
        # ToDo: set up type input 
        output = lookup(request.args['id'], "id")
    except:
        for x in index:
            output = output + f"[{x[0]}, {x[1]}, {x[2]}, {x[3]}, {x[4]}], "
    
    return output

@app.route('/book')
def downloadBook():
    num = request.args['id']
    #check for strip parameter
    try:
        strip = request.args['strip'].lower()
    except:
        strip = "true"
    url = f"https://www.gutenberg.org/cache/epub/{num}/pg{num}.txt"
    filename = f"app/books/{num}.txt"

    print(f"{url}    |    {filename}")

    if (not bookCheck(num)):
        #data = requests.get(url).content
        data = gutenberg.acquire.load_etext(num)
        return data
        open(filename, 'wb').write(data)


    LRU(num)
    f = open(filename, "r").read()

    if (strip == "true"):
        f = gutenberg_cleaner.simple_cleaner(f)


    return f

def lookup(para, ind):
    if (ind == "id"):
        t = 0
    elif (ind == "title"):
        t = 1

    for x in index:
        if (x[t] == para):
            return f"[{x[0]}, {x[1]}, {x[2]}, {x[3]}, {x[4]}]"
    return "No record found"

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


                # ID, TITLE, LANG, ISSUED, CREATORS
                temp = [None, None, None, None, []]
                #TODO: Parse XML Files into index array
                tree = ET.parse(filepath)
                root = tree.getroot()
                temp.append(root)

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
                            elif (smallerchild.tag.endswith("creator")):
                                for agent in smallerchild:
                                    for terms in agent:
                                        if (terms.tag.endswith("name")):
                                            temp[4].append(terms.text)
                                
                                
                index.append(temp)

    print("Parse Complete")
    print(f"Total Text Count: {count}")
    #with open('index.json', 'w') as f:
        #json.dump(index, f)
    return

def bookCheck(num):
    return os.path.exists(f"app/books/{num}.txt")

def loadIndex():
    if (os.path.isfile("index.json")):
        with open("index.json") as fp:
            index = json.load(fp)
    else:
        parseIndex()
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

def updateLRU(key):
    return

#setting up the server log
format = logging.Formatter('%(asctime)s %(message)s')   #TODO: Logger not logging

logFile = 'log.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(format)
my_handler.setLevel(logging.ERROR)

app_log = logging.getLogger('root')
app_log.setLevel(logging.DEBUG)

app_log.addHandler(my_handler)


#loadIndex()
