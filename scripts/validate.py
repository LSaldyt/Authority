from pymongo import MongoClient
from rich.pretty import pprint
from rich import print
import dill as pickle
import pandas as pd
import pymongo
import signal
import csv
import os

from bson.objectid import ObjectId

from resolution.validation.metrics import *
from resolution.validation.validate import validate_all, load_sources, possible_sources

def _mongodb_segfault_handler(signum, frame):
    # This is likely from a corrupted binary or document in mondodb, which is hard to isolate
    print(f'MongoDB encountered a segfault while validating, {frame}')

signal.signal(signal.SIGSEGV, _mongodb_segfault_handler)
os.kill(os.getpid(), signal.SIGSEGV)

def run():
    # First connect to MongoDB and setup the databases and collections in it
    client   = MongoClient('localhost', 27017)
    articles = client.jstor_database.articles

    # Load the available validation sources and cache them in memory
    # source_names = possible_sources # To use all

    source_names = ['biodiversity', 'google_scholar', 'self_citations',
                    'merge_heuristic', 'split_heuristic',
                    'meshcoauthor_heuristic', 'name_heuristic']
    sources = load_sources(client, source_names)

    # Controls which clusters we are validating
    query = {}
    # query = {'group_id.last' : 'smith'}
    # query = {'group_id.last' : 'johnson'}
    # query = {'group_id' : {'first_initial' : 'd', 'last' : 'johnson'}}
    # query = {'group_id' : {'first_initial' : 'l', 'last' : 'smith'}}
    # query = {'group_id' : {'first_initial' : 'c', 'last' : 'miller'}}
    # query = {'group_id' : {'first_initial' : 'a', 'last': 'hedenström'}}
    # query = {'group_id.first_initial' : 'a'}

    # prediction_sources = ['authority', 'naive_bayes_components', 'xgboost_components']
    prediction_sources = ['authority', 'naive_bayes_agglomerative', 'xgboost_agglomerative']
    predictions = {k : client.inferred[k] for k in prediction_sources}
    # Leave out authority legacy for now
    # predictions['authority_legacy'] = client.previous_inferred.previous_inferred
    stream = validate_all(client, predictions, query, sources)

    first = next(stream)

    # No memory issues from this method :)
    with open('data/resolution_validation_metrics.csv', 'w') as outfile:
        dict_writer = csv.DictWriter(outfile, first.keys())
        dict_writer.writeheader()
        dict_writer.writerows([first])
        dict_writer.writerows(stream)
