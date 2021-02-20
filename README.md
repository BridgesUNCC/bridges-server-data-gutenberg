# bridges-server-data-gutenburg

## Making Requests
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
  * type = id, title, language, date, author
  * strip = true or false (True = yes strip the data, False = don't strip the data)

The returned data is in json format such as:
```json
{
    "book_list": [
        {
            "id": "60960",
            "title": "In an Unknown Prison Land\r\nAn account of convicts and colonists in New Caledonia with jottings out and home",
            "lang": "en",
            "date_added": "2019-12-18",
            "authors": [
                "Griffith, George Chetwynd"
            ],
            "text": "Book text here"
        },
        {
            "id": "43200",
            "title": "Cornell Nature-Study Leaflets\r\nBeing a selection, with revision, from the teachers' leaflets, home nature-study lessons, junior naturalist monthlies and other publications from the College of Agriculture, Cornell University, Ithaca, N.Y., 1896-1904",
            "lang": "en",
            "date_added": "2013-07-12",
            "authors": [
                "New York State College of Agriculture"
            ],
            "text": 404
        }
    ]
}
```
A books text may return a 404, this indicates that the text request was not successful when accessing Gutenberg


> Note: Certain search types are not fully functioning as they should, date only returns the date that the Gutenberg entry was last edited/added to the database
