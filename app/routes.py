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
import gutenberg-cleaner

index = []

@app.route('/index')
def searchIndex():
    loadIndex()
    return count

@app.route('/book')
def downloadBook():
    num = request.args['id']
    url = f"https://www.gutenberg.org/files/{num}/{num}.txt"
    filename = f"app/books/{num}.txt"

    if (not bookCheck(num)):
        filename = wget.download(url, out=f"app/books/{num}.txt")

    f = open(filename, "r")

    f = gutenberg-cleaner.simple_cleaner(f)


    return f.read()

def parse(para):
    
    return

def loadIndex():
    root = "app/epub"

    count = 0

    for subdirs, dirs, files in os.walk(root):
        for filename in files:
            filepath = subdirs + os.sep + filename

            if filepath.endswith(".rdf"):
                count = count + 1
    print(count)

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
