#Library to be overwritten
from tmtoolkit.corpus import Corpus

#Used to make overwritten update method. needed for accurate progress bar
from typing import Dict, Union, Sequence, ValuesView, Iterator, Generator
from spacy.tokens import Doc
from tmtoolkit.corpus._document import Document
import logging

def textOutput(s : str):
    pass

#copied from tmtoolkit.corpus._corpus.py
logger = logging.getLogger('tmtoolkit')
#used to overwrite tmtoolkit.corpus._corpus.py to add progressbar
def update(self, new_docs: Union[Dict[str, Union[str, Doc, Document]], Sequence[Document]]):
    if isinstance(new_docs, Sequence):
        new_docs = {d.label: d for d in new_docs}

    logger.debug(f'updating Corpus instance with {len(new_docs)} new documents')

    new_docs_text = {}
    for lbl, d in new_docs.items():
        textOutput("working on " + lbl)
        if isinstance(d, str):
            new_docs_text[lbl] = d
        else:
            if isinstance(d, Doc):
                d = self._init_document(d, label=lbl)
            elif not isinstance(d, Document):
                raise ValueError('one or more documents in `new_docs` are neither raw text documents, nor SpaCy '
                                    'documents nor tmtoolkit Documents')

            self._docs[lbl] = d

    if new_docs_text:
        self._init_docs(new_docs_text)
    textOutput("bimap")
    self._update_bimaps(new_docs.keys())
    textOutput("workers")
    self._update_workers_docs()
    textOutput("done")

def _nlppipe(self, docs):
    """
    Helper method to set up the SpaCy pipeline.
    """
    if self.max_workers > 1:   # pipeline for parallel processing
        logger.debug(f'using parallel processing NLP pipeline with {self.max_workers} workers')
        return self.nlp.pipe(docs, n_process=self.max_workers)
    else:   # serial processing
        logger.debug('using serial processing NLP pipeline')
        ret : Iterator[Doc] = []
        for txt in docs:
            textOutput(str(len(ret)))
            ret.append(self.nlp(txt))
        return ret

Corpus.update = update
Corpus._nlppipe = _nlppipe