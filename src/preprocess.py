import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from nltk.tokenize import TreebankWordTokenizer
from underthesea import word_tokenize

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
VARIANTS = tuple(CONFIG['variants'])
EN_TOKENIZER = TreebankWordTokenizer()
END = None

def normalize(text):
    lowered = text.lower()
    cleaned = ''.join(c if unicodedata.category(c)[0] in ('L','M') or c.isdigit() else ' ' for c in lowered)
    return ' '.join(cleaned.split())

def tokenize(text, language):
    if not text.strip(): return []
    if language == 'vi': return word_tokenize(text, format='text', use_token_normalize=False).split()
    if language == 'en': return EN_TOKENIZER.tokenize(text)
    raise ValueError(language)

@lru_cache(maxsize=2)
def stopwords(language):
    return sorted({line.strip().lower() for line in (ROOT / 'resources/stopwords' / f'{language}.txt').read_text(encoding='utf-8-sig').splitlines() if line.strip()})

def trie_insert(trie, sequence):
    node = trie
    for part in sequence: node = node.setdefault(part, {})
    node[END] = True

@lru_cache(maxsize=4)
def stop_trie(language, token_mode=False):
    trie = {}
    for phrase in stopwords(language):
        sequence = tokenize(normalize(phrase), language) if token_mode else phrase.split()
        if sequence: trie_insert(trie, [s.lower() for s in sequence])
    return trie

def remove_stopwords(text, language):
    # Use lexical spans only for phrase recognition, not a language tokenizer.
    # Punctuation and all nonmatched original characters are preserved.
    spans = list(re.finditer(r'[^\W_]+', text, flags=re.UNICODE))
    trie = stop_trie(language)
    removals = []
    i = 0
    while i < len(spans):
        node = trie
        best = None
        j = i
        # Do not match inside underscore-connected lexical units.
        if spans[i].start() > 0 and text[spans[i].start()-1] == '_':
            i += 1; continue
        while j < len(spans):
            if j > i and not text[spans[j-1].end():spans[j].start()].isspace(): break
            value = spans[j].group().lower()
            if value not in node: break
            node = node[value]
            end = spans[j].end()
            if END in node and (end == len(text) or text[end] != '_'): best = j
            j += 1
        if best is None: i += 1
        else:
            removals.append((spans[i].start(),spans[best].end()))
            i = best + 1
    chunks = []
    position = 0
    for start,end in removals:
        chunks.append(text[position:start]); position = end
    chunks.append(text[position:])
    return ' '.join(''.join(chunks).split())

def remove_stopwords_from_tokens(tokens, language):
    trie = stop_trie(language, True)
    output = []
    i = 0
    while i < len(tokens):
        node = trie; best = None; j = i
        while j < len(tokens) and tokens[j].lower() in node:
            node = node[tokens[j].lower()]
            if END in node: best = j
            j += 1
        if best is None: output.append(tokens[i]); i += 1
        else: i = best + 1
    return output

def transform(text, language, variant):
    if not isinstance(text,str): raise TypeError('Expected string')
    if language not in CONFIG['languages']: raise ValueError(language)
    if variant == 'original': return text
    if variant == 'normalize': return normalize(text)
    if variant == 'stopword': return remove_stopwords(text,language)
    if variant == 'tokenize': return ' '.join(tokenize(text,language))
    if variant == 'combined': return ' '.join(remove_stopwords_from_tokens(tokenize(normalize(text),language),language))
    raise ValueError(variant)
