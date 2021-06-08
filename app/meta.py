import time
from app import routes
import json


id_to_book = {}

def get_meta_by_id(book_id: int):
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
        
        return json.dumps(book_json)
    except KeyError:
        return "id does not exist" #this should change HTTP return code

    
def build_index():
    for x in routes.index:
        id_to_book[int(x[0])] = x
        
    print ("meta index is "+str(len(id_to_book))+" entries long")
