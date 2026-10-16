import csv
import hashlib
import json
import sys
from pathlib import Path
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
OUT = ROOT / 'data/canonical'
REPORTS = ROOT / 'reports'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_jsonl(path):
    with path.open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]

def identifier(value):
    if value is None or not str(value).strip():
        raise ValueError('Missing ID')
    return str(value)

def text(value):
    if value is None:
        return ''
    if not isinstance(value, str):
        raise ValueError('Text must be a string')
    return value

def joined(row):
    # Preserve characters; only insert one newline between nonempty parts.
    return '\n'.join(v for v in (text(row.get('title')), text(row['text'])) if v != '')

def convert(docs, queries, labels, id_field):
    corpus = [{'doc_id': identifier(r[id_field]), 'text': joined(r)} for r in docs]
    questions = [{'query_id': identifier(r[id_field]), 'text': text(r['text'])} for r in queries]
    qrels = [{'query_id': identifier(r['query-id']), 'doc_id': identifier(r['corpus-id']), 'relevance': r['score']} for r in labels]
    return corpus, questions, qrels

def check(corpus, queries, qrels):
    docs = {r['doc_id']: r for r in corpus}
    questions = {r['query_id']: r for r in queries}
    if len(docs) != len(corpus) or len(questions) != len(queries):
        raise ValueError('Duplicate document/query IDs')
    pairs = set()
    for row in qrels:
        if row['doc_id'] not in docs or row['query_id'] not in questions:
            raise ValueError(f'Unresolved qrel: {row}')
        pair = (row['query_id'], row['doc_id'])
        if pair in pairs:
            raise ValueError(f'Duplicate qrel pair: {pair}')
        pairs.add(pair)
        if not isinstance(row['relevance'], (int, float)):
            raise ValueError('Relevance must be numeric')
    return {
        'documents': len(corpus), 'queries': len(queries), 'qrels': len(qrels),
        'empty_document_ids': [r['doc_id'] for r in corpus if not r['text'].strip()],
        'empty_query_ids': [r['query_id'] for r in queries if not r['text'].strip()],
        'relevance_values': sorted({r['relevance'] for r in qrels}),
        'unique_ids': True, 'qrels_references_valid': True,
    }

def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    input_paths = sorted(p for p in RAW.rglob('*') if p.is_file())
    before = {str(p.relative_to(ROOT)): digest(p) for p in input_paths}
    vi_tables = {part: pq.read_table(RAW / 'vi' / f'{part}.parquet') for part in ('corpus','queries','qrels')}
    vi = convert(vi_tables['corpus'].to_pylist(), vi_tables['queries'].to_pylist(), vi_tables['qrels'].to_pylist(), 'id')
    en_dir = RAW / 'en/nfcorpus'
    en_docs = read_jsonl(en_dir / 'corpus.jsonl')
    en_all_queries = read_jsonl(en_dir / 'queries.jsonl')
    with (en_dir / 'qrels/test.tsv').open(encoding='utf-8', newline='') as f:
        en_labels = list(csv.DictReader(f, delimiter='\t'))
    for row in en_labels:
        row['score'] = int(row['score'])
    selected = {r['query-id'] for r in en_labels}
    en_queries = [r for r in en_all_queries if identifier(r['_id']) in selected]
    en = convert(en_docs, en_queries, en_labels, '_id')
    datasets = {'vi': vi, 'en': en}
    # Validate both datasets before writing either.
    report = {'datasets': {lang: check(*data) for lang, data in datasets.items()},
              'input_sha256': before,
              'vi_schema': {part: str(table.schema) for part, table in vi_tables.items()},
              'english_all_split_queries': len(en_all_queries)}
    examples = ['# Canonical examples', '', 'Actual records: query -> qrel -> document. Text is truncated for display only.', '']
    output_hashes = {}
    for lang, (corpus, queries, qrels) in datasets.items():
        destination = OUT / lang
        destination.mkdir(parents=True, exist_ok=True)
        write_jsonl(destination / 'corpus.jsonl', corpus)
        write_jsonl(destination / 'queries.jsonl', queries)
        with (destination / 'qrels.csv').open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['query_id','doc_id','relevance'])
            writer.writeheader()
            writer.writerows(qrels)
        assert read_jsonl(destination / 'corpus.jsonl') == corpus
        assert read_jsonl(destination / 'queries.jsonl') == queries
        with (destination / 'qrels.csv').open(encoding='utf-8', newline='') as f:
            actual = list(csv.DictReader(f))
        assert actual == [{k: str(v) for k,v in row.items()} for row in qrels]
        for path in destination.iterdir():
            if path.is_file(): output_hashes[str(path.relative_to(ROOT))] = digest(path)
        lookup_docs = {r['doc_id']: r for r in corpus}
        lookup_queries = {r['query_id']: r for r in queries}
        positive = next(r for r in qrels if r['relevance'] > 0)
        sample = {'query': lookup_queries[positive['query_id']], 'qrel': positive,
                  'document_excerpt': lookup_docs[positive['doc_id']]['text'][:1200]}
        examples.extend([f'## {lang}', '', '```json', json.dumps(sample, ensure_ascii=False, indent=2), '```', ''])
        print(lang, report['datasets'][lang])
    after = {str(p.relative_to(ROOT)): digest(p) for p in input_paths}
    if before != after: raise ValueError('Raw files changed')
    report.update(raw_unchanged=True, output_roundtrip_verified=True, output_sha256=output_hashes)
    (REPORTS / 'canonical_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (REPORTS / 'canonical_examples.md').write_text('\n'.join(examples), encoding='utf-8')

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
