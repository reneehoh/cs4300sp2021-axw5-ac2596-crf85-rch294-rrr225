from collections import Counter
import numpy as np
from nltk.tokenize import TreebankWordTokenizer
from app.irsystem.models.inverted_index import InvertedIndex
from app.irsystem.models.get_data import idx_to_trail_name, NUM_DOCS, trail_names
from app.irsystem.models.levenshtein import ranked_levs
import math

# initialize inverted index of descriptions/reviews for effiency
trails_tfidf_obj_desc = InvertedIndex(token_type="descriptions", vector_type='tf')
trails_tfidf_obj_reviews = InvertedIndex(token_type="reviews", vector_type='tf')


def get_rankings_by_query(query, a=0.5, b=0.3, c=0.2):
    """
    Returns a list of the top 3 rankings in the form (similarity_score, trail_name) given a query string.
    This serves as the main function that is called when a new query is made.

    a -> weight for descriptions similarity
    b -> weight for reviews similarity
    c -> weight for title similarity
    """
    sim_descriptions = get_cosine_similarity_ranking(query, 'descriptions')
    sim_reviews = get_cosine_similarity_ranking(query, 'reviews')
    sim_titles = ranked_levs(query, trail_names)

    # TODO
    # strict filter scores
    # jaccard scores

    final_sim = {}
    for name in trail_names:
        final_sim[name] = a * sim_descriptions.get(name, 0) + \
        b * sim_reviews.get(name, 0) + \
        c * sim_titles.get(name, 0)
    
    rankings = [(final_sim[name], name) for name in final_sim]
    rankings.sort(key = lambda x: (-x[0],x[1]))
    rankings = rankings[:3]

    print(rankings)
    return rankings
        

def get_cosine_similarity_ranking(query, token_type):
    # Create tfidf matrix object for trail documents with 200 features
    if token_type == 'descriptions':
        trails_tfidf_obj = trails_tfidf_obj_desc
    elif token_type == 'reviews':
        trails_tfidf_obj = trails_tfidf_obj_reviews

    inv_idx = trails_tfidf_obj.inv_idx
    idfs= trails_tfidf_obj.idfs
    doc_norms = trails_tfidf_obj.doc_norms
    # Create tfidf vector for query of size (1, 200)
    q_tfs = Counter(tokenize_string(query))
    q_norm = math.sqrt(sum([(q_tfs[tok] * idfs[tok])**2 for tok in q_tfs if tok in idfs]))
    
    nums = {}
    for tok in q_tfs:
        if tok in idfs:
            tf_idf_q = q_tfs[tok] * idfs[tok]
            for post in inv_idx[tok]:
                val = nums.get(post[0], 0)
                val += tf_idf_q * (post[1] * idfs[tok])
                nums[post[0]] = val

    rankings = {}
    for i in nums:
        rankings[idx_to_trail_name[i]] = nums[i]/(q_norm * doc_norms[i])
    return rankings

def tokenize_string(s):
    """
    Given an input string s, returns a list of tokens in the string.
    """
    tokenize = TreebankWordTokenizer().tokenize
    return tokenize(s.lower())


def tfidfize_query(q, features, idfs):
    """
    Given an input list of tokens q, returns a tfidf vector of size (1, [# of features]) representing q.
    If a term appears in q that is not in the given features, ignore it.
    """
    tfidf_vec = np.zeros(len(features))
    tf_q = { term:freq for term, freq in Counter(q).items() if term in idfs }

    for i, token in enumerate(features):
        tfidf_vec[i] = tf_q.get(token, 0) * idfs.get(token, 0)

    return tfidf_vec


def cosine_sim(query, trail):
    """
    Returns cosine similarity of query and a trail document.
    """
    num = np.dot(query, trail)
    denom = (np.sqrt(np.sum(np.linalg.norm(query))) * np.sqrt(np.sum(np.linalg.norm(trail))))
                 
    return num / denom
 

def cosine_sim_matrix(num_trails, query, tfidf, sim_method = cosine_sim):
    # trails_sims = np.zeros(num_trails)
    trails_sims = [0 for _ in range(num_trails)]
 
    # for each trail document find the cosine similarity with the query
    for i in range(0, num_trails):
        trails_sims[i] = (sim_method(query, tfidf[i]), idx_to_trail_name[i])
    
    # sorted list of all cosine similarity scores of query and trail documents
    ranked_trails = sorted(trails_sims, key= lambda x: -x[0])
    return ranked_trails

# STRICT FILTERS FOR ACCESSIBILITY

def get_filter_score(query, trail):
    """
    Given a boolean value for accessibility in query and accessibility in trail, return
    1 if (query, trail) == (1,1) or (query, trail) == (0,0).
    """
    return 1 if (query == 0 and trail == 0) or (query == 1 and trail == 1) else 0

def get_filter_scores(query):
    """
    Given a query, returns a dictionary of trail_name to accessibility filter scores.
    """
    pass