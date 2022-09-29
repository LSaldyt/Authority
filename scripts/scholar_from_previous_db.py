import sqlite3
from pymongo import MongoClient
from rich.pretty import pprint
from rich import print
import itertools
import pymongo
from authority.validation.google_scholar import process_google_scholar_name
from authority.process.process import remove_stop_words

''' Parse 24,763 google scholar articles from previous sqlite3 db '''

table    = 'google_scholar_new'
all_rows = 'SELECT * from {}'

def expand_author_row(row, articles):
    _, ids, full_name, scholar_id = row
    name = process_google_scholar_name(full_name)
    pprint(name)
    mongo_ids = []
    titles    = []
    dois      = []
    for doi in ids.split(','):
        article = articles.find_one({'front.article-meta.article-id.#text' : doi})
        if article is not None:
            mongo_ids.append(article['_id'])
            titles.append(article['title'])
            dois.append(doi)
    pprint(dict(author=name, title=titles, dois=dois, mongo_ids=mongo_ids))
    return dict(author=name, title=titles, dois=dois, mongo_ids=mongo_ids)

def run():
    mongo_client = MongoClient('localhost', 27017)

    sql_client   = sqlite3.connect('database/jstor-authority.db')
    sql_cursor   = sql_client.cursor()

    jstor_database    = mongo_client.jstor_database
    scholar_db        = mongo_client.google_scholar
    scholar_jstor_doi = scholar_db.jstor_doi
    scholar_authors   = scholar_db.authors
    articles          = jstor_database.articles

    scholar_db.drop_collection('jstor_doi')

    sql_cursor.execute(all_rows.format(table))
    for row in sql_cursor.fetchall():
        scholar_jstor_doi.insert_one(expand_author_row(row, articles))

