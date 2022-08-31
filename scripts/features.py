from pymongo import MongoClient
from rich.pretty import pprint
from bson.son import SON
import itertools

from authority.algorithm.compare import compare

def compare_pair(pair, articles):
    a, b = pair['pair']
    doc_a = articles.find_one({'_id' : a['ids']})
    doc_b = articles.find_one({'_id' : b['ids']})
    doc_a.update(**a['authors'])
    doc_b.update(**b['authors'])
    feature_dict = compare(doc_a, doc_b)
    return dict(pair=[a, b], features=feature_dict)

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
    pairs          = client.reference_sets_pairs

    client.drop_database('features')
    client.drop_database('feature_groups')

    features       = client.features
    feature_groups = client.feature_groups

    ''' Create feature vectors for the pair collections '''
    for ref_key in pairs.list_collection_names():
        print(ref_key)
        features[ref_key].insert_many(
            compare_pair(pair, articles) for pair in pairs[ref_key].find())

    ''' Sum feature vectors by reference set, to estimate frequency '''
    pipelines = [(i, [{'$group': {
                        '_id'    : {f'x{i}' : f'$features.x{i}'},
                        'count'  : {'$sum': 1},
                        }},
                      {'$sort': SON([('_id', 1)])}
                      ]) for i in range(1, 8)]
    possible = set()
    for ref_key in features.list_collection_names():
        print(ref_key)
        for i, pipeline in pipelines:
            group_key = f'{ref_key}_x{i}'
            feature_groups[group_key].insert_many(
                features[ref_key].aggregate(pipeline))
            for group in feature_groups[group_key].find():
                for k, v in group['_id'].items():
                    possible.add((k, v))
                pprint(group)
    pprint(possible)

    def get_count(group, k, v):
        result = group.find_one({'_id' : {k : v}})
        if result is None:
            return 0
        else:
            return result['count']

    total_matches     = features['match'].count_documents(filter={})
    total_non_matches = features['non_match'].count_documents(filter={})
    ''' Compute r scores by comparing match and non-match frequencies '''
    for i in range(1, 8):
        match_group     = feature_groups[f'match_x{i}']
        non_match_group = feature_groups[f'non_match_x{i}']
        for k, v in possible:
            match_count     = get_count(match_group, k, v)
            non_match_count = get_count(non_match_group, k, v)
            try:
                print(f'{k}={v}: {(match_count / total_matches) / (non_match_count / total_non_matches)}')
            except ZeroDivisionError:
                print(f'{k}={v}: undefined')


