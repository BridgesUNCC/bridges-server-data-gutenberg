from app import app
from flask import request
from flask import send_file
import logging
from logging.handlers import RotatingFileHandler
import wget
import os
import subprocess
import math
import hashlib
import pickle
import io
import shutil
import gutenberg_cleaner
import math
import xml.etree.ElementTree as ET

index = []

@app.route('/index')
def searchIndex():
    count = loadIndex()
    output = ""
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

    if (not bookCheck(num)):
        filename = wget.download(url, out=f"app/books/{num}.txt")

    f = open(filename, "r").read()

    if (strip == "true"):
        f = gutenberg_cleaner.simple_cleaner(f)


    return f

def parse(para):
    
    return

def loadIndex():
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
                            elif (False):
                                temp[2] = None
                index.append(temp)

    print("Parse Complete")
    print(f"Total Text Count: {count}")
    return count


def bookCheck(num):
    return os.path.exists(f"app/books/{num}.txt")


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
