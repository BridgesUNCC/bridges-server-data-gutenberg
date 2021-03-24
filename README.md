# bridges-server-data-gutenburg

## Making Requests
### Searching Database
To return the book data use a URL similar to
```
http://192.168.2.14:5000/search?search=home&type=title
```
The route you should use is /search

The parameters to pass are:
  * search : The search you want returned
  * type : The value you want to search through (Example: author or title)
  * strip : (OPTIONAL) Tells the server if you want to remove header and footer data from the book text, default is True
 
 Type and Strip have specific values that it is looking for:
  * type = id, title, language, date, author, genre, loc
  * strip = true or false (True = yes strip the data, False = don't strip the data)

The returned data is in json format such as:
```json
{
    "book_list": [
        {
            "id": "60045",
            "title": "The Golden Wheel Dream-book and Fortune-teller",
            "lang": "en",
            "date_added": "2019-08-03",
            "authors": [
                "Fontaine, Felix"
            ],
            "genres": [
                "Dream interpretation",
                "Fortune-telling"
            ],
            "loc_class": [
                "BF"
            ]
        },
        {
            "id": "62485",
            "title": "Edgings: crocheted, tatted, hair pin lace",
            "lang": "en",
            "date_added": "2020-06-26",
            "authors": [
                "American Thread Company"
            ],
            "genres": [
                "Crocheting -- Patterns",
                "Tatting -- Patterns",
                "Knitting -- Patterns"
            ],
            "loc_class": [
                "TT"
            ]
        }
    ]
}
```
### Returning Meta data based on ID
To return meta data based on Id use this URL format 
```
http://192.168.2.14:5000/meta?id=2701
```

The parameters to pass are:
  * id : The id of the book you want meta data on
  
The returned data is in json format such as:
```json
{
    "book_list": [
        {
            "id": "2701",
            "title": "Moby Dick; Or, The Whale",
            "lang": "en",
            "date_added": "2001-07-01",
            "authors": [
                "Melville, Herman"
            ],
            "genres": [
                "Whaling -- Fiction",
                "Adventure stories",
                "Sea stories",
                "Whaling ships -- Fiction",
                "Ship captains -- Fiction",
                "Whales -- Fiction",
                "Psychological fiction",
                "Ahab, Captain (Fictitious character) -- Fiction",
                "Mentally ill -- Fiction"
            ],
            "loc_class": [
                "PS"
            ]
        }
    ]
}
```
### Getting Book Texts
To return a books text use this URL:
```
http://192.168.2.14:5000/book?id=2701
```
The parameters to pass are:
  * id : The id of the book you want the text of

The data returned is just a plain string that holds the books text

*A books text may return a 404, this indicates that the text request was not successful when accessing Gutenberg


> Note: Certain search types are not fully functioning as they should, date only returns the date that the Gutenberg entry was last edited/added to the database
