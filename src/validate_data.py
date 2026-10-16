import hashlib
import csv
import json
from preprocess import ROOT, CONFIG, VARIANTS, transform
from build_variants import sha

def read(path):
    with path.open(encoding='utf-8') as f: return [json.loads(line) for line in f]

def main():
    manifest=json.loads((ROOT/'reports/build_manifest.json').read_text(encoding='utf-8'))
    report={'passed':True,'datasets':{},'raw_and_canonical_unchanged':True,'full_transform_recheck':True,'recomputed_outputs_byte_identical':True}
    for name,expected in manifest['input_sha256'].items():
        assert sha(ROOT/name)==expected, name
    for name,expected in manifest['resource_sha256'].items(): assert sha(ROOT/name)==expected,name
    for name,expected in manifest['output_sha256'].items(): assert sha(ROOT/name)==expected,name
    assert json.loads((ROOT/'config.json').read_text(encoding='utf-8')) == manifest['config']
    for lang in CONFIG['languages']:
        canonical=ROOT/'data/canonical'/lang
        processed=ROOT/'data/processed'/lang
        assert sha(canonical/'qrels.csv')==sha(processed/'qrels.csv')
        corpus=read(canonical/'corpus.jsonl');queries=read(canonical/'queries.jsonl')
        dids={r['doc_id'] for r in corpus};qids={r['query_id'] for r in queries}
        with (processed/'qrels.csv').open(encoding='utf-8',newline='') as f:
            labels=list(csv.DictReader(f))
        assert all(r['doc_id'] in dids and r['query_id'] in qids for r in labels)
        result={}
        for variant in VARIANTS:
            result[variant]={}
            for kind,source,id_key in [('corpus',corpus,'doc_id'),('queries',queries,'query_id')]:
                actual=read(processed/variant/f'{kind}.jsonl')
                assert len(actual)==len(source)
                assert [r[id_key] for r in actual]==[r[id_key] for r in source]
                assert len({r[id_key] for r in actual})==len(actual)
                repeated_hash = hashlib.sha256()
                for index,(a,b) in enumerate(zip(actual,source),1):
                    assert set(a)=={id_key,'text'}
                    recomputed = {id_key:b[id_key], 'text':transform(b['text'],lang,variant)}
                    assert a == recomputed, (lang,variant,b[id_key])
                    repeated_hash.update((json.dumps(recomputed,ensure_ascii=False)+'\n').encode('utf-8'))
                    if index % 2000 == 0: print('Rechecking',lang,variant,kind,index,flush=True)
                assert repeated_hash.hexdigest()==sha(processed/variant/f'{kind}.jsonl')
                result[variant][kind]={'records':len(actual),'empty_ids':[r[id_key] for r in actual if not r['text'].strip()]}
            print('Validated',lang,variant,flush=True)
        report['datasets'][lang]=result
    (ROOT/'reports/validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Full validation passed')
if __name__=='__main__': main()
