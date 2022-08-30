from pymongo import MongoClient
from rich.pretty import pprint
from bson.son import SON
import itertools

from authority.algorithm.compare import compare

def run():
    ''' Calculate the features for the different sets in the database
        for features x1, x2, and x7, there are bounds,
        but for features x3-x6, x8, and x9, there are not tight bounds
        so first independent r(x_i) is estimated for bounded features,
            by using a simple ratio of means between matches and non-matches
        and then r(x_i) is estimated for unbounded features
            using smoothing, interpolation, and extrapolation..
        then, r(x_i) for all i can be computed by multiplying each component r(x_i)
    '''

    client         = MongoClient('localhost', 27017)
    jstor_database = client.jstor_database
    articles       = jstor_database.articles
    reference_sets = client.reference_sets

    match_coll = 'first_initial:middle_initial:last:suffix'
    matches = reference_sets[match_coll]
    for group in matches.find():
        try:
            a, b, *rest = group['ids']
        except ValueError:
            break
        auth_a, auth_b, *rest = group['authors']
        doc_a = articles.find_one({'_id' : a})
        doc_b = articles.find_one({'_id' : b})
        doc_a.update(**auth_a)
        doc_b.update(**auth_b)

        print(doc_a['title'])
        print(doc_b['title'])
        pprint(compare(doc_a, doc_b))
        print()

    1/0
