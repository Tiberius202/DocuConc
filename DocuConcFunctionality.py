import re
import string
from collections import Counter
import numpy as np

#TODO, remove. Purely for testing
import os
import spacy
from tmtoolkit.corpus import Corpus, print_summary, tokens_table, vocabulary_counts, vocabulary_size, doc_tokens, corpus_num_tokens
def pre_process(txt):
    txt = re.sub(r'\bits\b', 'it s', txt)
    txt = re.sub(r'\bIts\b', 'It s', txt)
    txt = " ".join(txt.split())
    return(txt)
#end testing code

def convert_totuple(tok):
    token_tuple = []
    is_punct = re.compile("[{}]+$".format(re.escape(string.punctuation)))
    is_digit = re.compile("[\d{}]+$".format(re.escape(string.punctuation)))
    for t in tok.values():
        token_list = [x.lower() for x in t['token']]
        iob_list = t['ent_iob']
        iob_list = [x.replace('IS_DIGIT','B') for x in iob_list]
        iob_list = [x.replace('IS_ALPHA','I') for x in iob_list]
        iob_list = [x.replace('IS_ASCII','O') for x in iob_list]
        ent_list = t['ent_type']
        iob_ent = list(map('-'.join, zip(iob_list, ent_list)))
        tag_list = t['tag']
        # correct some mistagging
        tag_list = ['Y' if bool(is_punct.match(token_list[i])) else v for i, v in enumerate(tag_list)]
        tag_list = ['MC' if bool(is_digit.match(token_list[i])) and tag_list[i] != 'Y' else v for i, v in enumerate(tag_list)]
        token_tuple.append(list(zip(token_list, tag_list, iob_ent)))
    return(token_tuple)
    
def count_tokens(tok, non_punct):
    token_list = []
    p = re.compile('^[a-z]+$')
    for t in tok:
        tokens = [x[0] for x in t]
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
    for t in tok:
        tags = [x[1] for x in t]
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

def count_ds(tok, non_punct):
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
    ds_prop = np.array(ds_freq)/non_punct*100
    ds_prop = ds_prop.round(decimals=2)
    ds_range = np.array([x[1] for x in ds_range])/len(tok)*100
    ds_range = ds_range.round(decimals=2)
    ds_counts = zip(ds_cats.tolist(), ds_freq.tolist(), ds_prop.tolist(), ds_range.tolist())
    ds_counts = list(ds_counts)
    return(ds_counts)

def merge_ds(tok, cluster):
    phrase_list = []
    for t in tok:
        df = [x for x in t if x[2].endswith(cluster)]
        #df = pd.DataFrame(df, columns=['token', 'ds_cat'])
        indices = df.loc[df['ds_cat'].str.contains('B-')].index.tolist()
        rows_ = dict.fromkeys(df.columns.tolist(),'')
        df = pd.DataFrame(np.insert(df.values, [x for x in indices[1:]],
                       values=list(rows_.values()), 
                       axis=0),columns=rows_.keys())
        m = df['ds_cat'].eq('')
        df = (df[~m].assign(ds_cat=lambda x: x['ds_cat'].str.replace('^[IB]-', '', regex=True))
                .groupby([m.cumsum(), 'ds_cat'])['token']
                .agg(' '.join)
                .droplevel(0)
                .reset_index()
                .reindex(df.columns, axis=1))
        ds_tokens = df['token'].tolist()
        phrase_list.append(ds_tokens)
    phrase_range = []
    for i in range(0,len(tok)):
        phrase_range.append(list(set(phrase_list[i])))
    phrase_range = [x for xs in phrase_range for x in xs]
    phrase_range = Counter(phrase_range)
    phrase_range = sorted(phrase_range.items(), key=lambda pair: pair[0], reverse=False)
    phrase_list = [x for xs in phrase_list for x in xs]
    phrase_list = Counter(phrase_list)
    phrase_list = sorted(phrase_list.items(), key=lambda pair: pair[0], reverse=False)
    phrases = np.array([x[0] for x in phrase_list])
    phrase_freq = np.array([x[1] for x in phrase_list])
    total_phrases = sum(phrase_freq)
    # Note: using non_punct for normalization
    phrase_prop = np.array(phrase_freq)/corpus_total*1000000
    phrase_prop = phrase_prop.round(decimals=2)
    phrase_range = np.array([x[1] for x in phrase_range])/len(tok)*100
    phrase_range = phrase_range.round(decimals=2)
    phrase_counts = list(zip(phrases.tolist(), phrase_freq.tolist(), phrase_prop.tolist(), phrase_range.tolist()))
    phrase_counts = list(phrase_counts)
    return(phrase_counts)

def groupby_consecutive(lst):
    for _, g in groupby(enumerate(lst), lambda x: x[0] - x[1]):
        yield list(map(itemgetter(1), g))

def merge_tags(tok, tags):
    phrase_list = []
    for i in range(0,len(tok)):
        df = [x for x in tok[i] if x[1].startswith(tags)]
        df = pd.DataFrame(df, columns=['token', 'tag', 'ds_cat'])
        df = df.drop(columns=['ds_cat'])
        # repair broken sequences
        tag_seq = df['tag'].tolist()
        tag_seq = [re.findall(r'\d\d$', x) for x in tag_seq]
        tag_seq = [x for sublist in tag_seq for x in (sublist or ['99'])]
        tag_seq = [int(x) for x in tag_seq]
        tag_seq = list(groupby_consecutive(lst=tag_seq))
        for x in tag_seq:
            x[0] = re.sub('\\d+', 'B-', str(x[0]))
        tag_seq = [x for xs in tag_seq for x in xs]
        tag_seq = ['I-' if isinstance(x, int) else x for x in tag_seq]
        df.insert(loc=1, column='iob_tag', value=pd.Series(tag_seq, dtype='str'))
        df['tag'].replace( { r"\d\d$" : '' }, inplace= True, regex = True)
        df['tag'] = df['iob_tag'].astype(str) + df['tag']
        df = df.drop(columns=['iob_tag'])
        # concatenate rows        
        indices = df.loc[df['tag'].str.contains('B-')].index.tolist()
        rows_ = dict.fromkeys(df.columns.tolist(),'')
        df = pd.DataFrame(np.insert(df.values, [x for x in indices[1:]],
                       values=list(rows_.values()), 
                       axis=0),columns=rows_.keys())
        m = df['tag'].eq('')
        df = (df[~m].assign(tag=lambda x: x['tag'].str.replace('^[IB]-', '', regex=True))
                .groupby([m.cumsum(), 'tag'])['token']
                .agg(' '.join)
                .droplevel(0)
                .reset_index()
                .reindex(df.columns, axis=1))
        ds_tokens = df['token'].tolist()
        phrase_list.append(ds_tokens)
    phrase_range = []
    for i in range(0,len(tok)):
        phrase_range.append(list(set(phrase_list[i])))
    phrase_range = [x for xs in phrase_range for x in xs]
    phrase_range = Counter(phrase_range)
    phrase_range = sorted(phrase_range.items(), key=lambda pair: pair[0], reverse=False)
    phrase_list = [x for xs in phrase_list for x in xs]
    phrase_list = Counter(phrase_list)
    phrase_list = sorted(phrase_list.items(), key=lambda pair: pair[0], reverse=False)
    phrases = np.array([x[0] for x in phrase_list])
    phrase_freq = np.array([x[1] for x in phrase_list])
    total_phrases = sum(phrase_freq)
    # Note: using non_punct for normalization
    phrase_prop = np.array(phrase_freq)/corpus_total*1000000
    phrase_prop = phrase_prop.round(decimals=2)
    phrase_range = np.array([x[1] for x in phrase_range])/len(tok)*100
    phrase_range = phrase_range.round(decimals=2)
    phrase_counts = list(zip(phrases.tolist(), phrase_freq.tolist(), phrase_prop.tolist(), phrase_range.tolist()))
    phrase_counts = list(phrase_counts)
    return(phrase_counts)
#TODO Remove Main. Only for testing
if __name__ == "__main__":
    print("nlp")
    nlp = spacy.load(os.path.join(os.path.dirname(__file__) , "model-new"))
    print("loading")
    corp = Corpus.from_folder(os.path.join(os.path.dirname(__file__) , "test_corpus"), spacy_instance=nlp, raw_preproc=pre_process, spacy_token_attrs=['tag', 'ent_iob', 'ent_type', 'is_punct'])
    print("basic stats")
    corpus_total = corpus_num_tokens(corp)
    corpus_types = vocabulary_size(corp)
    total_punct = []
    for i in range(0,len(corp)):
        total_punct.append(sum(corp[i]['is_punct']))
    total_punct = sum(total_punct)
    non_punct = corpus_total - total_punct
    docs = doc_tokens(corp, with_attr=True)
    tp = convert_totuple(docs)