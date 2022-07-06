import re
import string
from collections import Counter
import numpy as np

def convert_totuple(tok):
    token_tuple = []
    for i in range(0,len(tok)):
        token_list = [x.lower() for x in list(tok.values())[i]['token']]
        iob_list = list(tok.values())[i]['ent_iob']
        iob_list = [x.replace('IS_DIGIT','B') for x in iob_list]
        iob_list = [x.replace('IS_ALPHA','I') for x in iob_list]
        iob_list = [x.replace('IS_ASCII','O') for x in iob_list]
        ent_list = list(tok.values())[i]['ent_type']
        iob_ent = list(map('-'.join, zip(iob_list, ent_list)))
        token_tuple.append(list(zip(token_list, list(tok.values())[i]['tag'], iob_ent)))
    return(token_tuple)
def count_tokens(tok, non_punct):
    token_list = []
    p = re.compile('^[a-z]+$')
    for i in range(0,len(tok)):
        tokens = [x[0] for x in tok[i]]
        # strip punctuation
        tokens = [x.translate(str.maketrans('', '', string.punctuation)) for x in tokens]
        # return only alphabetic strings
        tokens = [x for x in tokens if p.match(x)]
        token_list.append(tokens)
    token_range = []
    for i in range(0,len(tok)):
        token_range.append(list(set(token_list[i])))
    token_range = [x for xs in token_range for x in xs]
    token_range = Counter(token_range)
    token_range = sorted(token_range.items(), key=lambda pair: pair[0], reverse=False)
    token_list = [x for xs in token_list for x in xs]
    token_list = Counter(token_list)
    token_list = sorted(token_list.items(), key=lambda pair: pair[0], reverse=False)
    tokens = np.array([x[0] for x in token_list])
    token_freq = np.array([x[1] for x in token_list])
    total_tokens = sum(token_freq)
    # Note: using non_punct for normalization
    token_prop = np.array(token_freq)/non_punct*1000000
    token_prop = token_prop.round(decimals=2)
    token_range = np.array([x[1] for x in token_range])/len(tok)*100
    token_range = token_range.round(decimals=2)
    token_counts = list(zip(tokens.tolist(), token_freq.tolist(), token_prop.tolist(), token_range.tolist()))
    token_counts = list(token_counts)
    return(token_counts)
def count_tags(tok, non_punct):
    tag_list = []
    # remove tags for puct, unidentified, and multitoken units
    remove_starttags = ('Y', 'FU')
    remove_endtags = ('21', '22', '31', '32', '33', '41', '42', '43', '44')
    #[x for x in listB for a in listA if a in x]
    for i in range(0,len(tok)):
        tags = [x[1] for x in tok[i]]
        tags = [x for x in tags if not x.startswith(remove_starttags)]
        tags = [x for x in tags if not x.endswith(remove_endtags)]
        tag_list.append(tags)
    tag_range = []
    for i in range(0,len(tok)):
        tag_range.append(list(set(tag_list[i])))
    tag_range = [x for xs in tag_range for x in xs]
    tag_range = Counter(tag_range)
    tag_range = sorted(tag_range.items(), key=lambda pair: pair[0], reverse=False)
    tag_list = [x for xs in tag_list for x in xs]
    tag_list = Counter(tag_list)
    tag_list = sorted(tag_list.items(), key=lambda pair: pair[0], reverse=False)
    tags = np.array([x[0] for x in tag_list])
    tag_freq = np.array([x[1] for x in tag_list])
    tag_prop = np.array(tag_freq)/non_punct*100
    tag_prop = tag_prop.round(decimals=2)
    tag_range = np.array([x[1] for x in tag_range])/len(tok)*100
    tag_range = tag_range.round(decimals=2)
    tag_counts = list(zip(tags.tolist(), tag_freq.tolist(), tag_prop.tolist(), tag_range.tolist()))
    tag_counts = list(tag_counts)
    return(tag_counts)
def count_ds(tok, corpus_total):
    ds_list = []
    for i in range(0,len(tok)):
        ds_cats = [x[2] for x in tok[i]]
        # filter for benning entity tags
        ds_cats = [x for x in ds_cats if x.startswith('B-')]
        ds_list.append(ds_cats)
    ds_range = []
    for i in range(0,len(tok)):
        ds_range.append(list(set(ds_list[i])))
    ds_range = [x for xs in ds_range for x in xs]
    ds_range = Counter(ds_range)
    ds_range = sorted(ds_range.items(), key=lambda pair: pair[0], reverse=False)
    ds_list = [x for xs in ds_list for x in xs]
    ds_list = Counter(ds_list)
    ds_list = sorted(ds_list.items(), key=lambda pair: pair[0], reverse=False)
    ds_cats = [x[0] for x in ds_list]
    ds_cats = [x.replace('B-', '') for x in ds_cats]
    ds_cats = [re.sub(r'([a-z])([A-Z])', '\\1 \\2', x) for x in ds_cats]
    ds_cats = np.array(ds_cats)
    ds_freq = np.array([x[1] for x in ds_list])
    ds_prop = np.array(ds_freq)/corpus_total*100
    ds_prop = ds_prop.round(decimals=2)
    ds_range = np.array([x[1] for x in ds_range])/len(tok)*100
    ds_range = ds_range.round(decimals=2)
    ds_counts = zip(ds_cats.tolist(), ds_freq.tolist(), ds_prop.tolist(), ds_range.tolist())
    ds_counts = list(ds_counts)
    return(ds_counts)