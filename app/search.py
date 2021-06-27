from app import routes
from app import meta
import difflib

from operator import itemgetter

anythingshort = []

titlehash = {}

def title_lookup(para, t):
    found = []
    candidatecount = {}
    title = para.lower()

    candidates = []
    if (len(title) < 7) :
        for idd in anythingshort:
            candidates.append ((idd, 1))
    else:
        
        for i in range (0, len(title) - 4):
            first = title[i]
            second = title[i+1]
            third = title[i+2]
            fourth = title[i+3]
                
            try:
                for idin in titlehash[first][second][third][fourth]:
                    if idin not in candidatecount:
                        candidatecount[idin] = 1
                    else:
                        candidatecount[idin] +=1
            except KeyError:
                pass

        candidates = sorted(candidatecount.items(), key=itemgetter(1), reverse=True)

        # only retain top 100
        candidates = candidates[:100]

    maxcount = candidates[0][1]

#    threshold = .90
    threshold = min(.90, (len(title)-1)/float(len(title)))
    
    for idd, count in candidates:
        # ignore all candidates with less count than 50% of max
        if (count > maxcount / 2):
            #print (idd)

            x = meta.id_to_book[int(idd)]
                
            try:
                ratio = difflib.SequenceMatcher(None, para, x[t]).quick_ratio()
                for i in x[t].split(" "):
                    if i == para:
                        ratio = 1
                        break
            except:
                ratio = 0
            if (ratio >= threshold):
                found.append(x)

    return found

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
        try:
            for x in routes.index:
                for auth in x[t]:
                    if (len(x[1]) == 0):
                        continue
                    flipAuth = auth.split(" ")
                    if len(flipAuth) > 1:
                        flipAuthStr = f"{flipAuth[1]} {flipAuth[0]}"
                    else:
                        flipAuthStr = auth
                    if (difflib.SequenceMatcher(None, para, auth).quick_ratio() >= .90 or difflib.SequenceMatcher(None, para, flipAuthStr).quick_ratio() >= .90):
                        found.append(x)
                    else:
                        for i in auth.split(' '):
                            if para == i:
                                found.append(x)
        except Exception as e:
            routes.app_log.info(e)

    #genre list search
    elif t == 5 or t == 6: 
        for x in routes.index:
            for genre in x[t]:
                ratio = difflib.SequenceMatcher(None, para, genre).quick_ratio()
                if (ratio >= .75):
                    found.append(x)
    elif t == 1:
        found = title_lookup(para, t)
    else:

        for x in routes.index:
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

    return found

def build_index():
    totallen = 0
    for x in routes.index:
        if (x[1] == None):
            continue
        else:
            if (len(x[1]) < 7):
                anythingshort.append(x[0])
            else:
                title = x[1].lower()
                for i in range (0, len(title) - 4):
                    first = title[i]
                    second = title[i+1]
                    third = title[i+2]
                    fourth = title[i+3]
                    
                    if (first not in titlehash.keys()):
                        titlehash[first] = {}
                    if (second not in titlehash[first].keys()):
                        titlehash[first][second] = {}
                    if (third not in titlehash[first][second].keys()):
                        titlehash[first][second][third] = {}
                    if (fourth not in titlehash[first][second][third].keys()):
                        titlehash[first][second][third][fourth] = []

                    titlehash[first][second][third][fourth].append(x[0])
                    
            totallen += len(x[1])

    print ("total length:  " + str(totallen))
