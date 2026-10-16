import csv
import hashlib
import importlib.metadata
import json
import shutil
import sys
import time
from pathlib import Path
from preprocess import ROOT, CONFIG, VARIANTS, transform, stop_trie

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def input_hashes():
    return {str(p.relative_to(ROOT)):sha(p) for folder in ('data/raw','data/canonical') for p in sorted((ROOT/folder).rglob('*')) if p.is_file()}

def main():
    before = input_hashes()
    rows = []
    for language in CONFIG['languages']:
        source = ROOT/'data/canonical'/language
        destination = ROOT/'data/processed'/language
        destination.mkdir(parents=True,exist_ok=True)
        # Prepare phrase matchers once per language.
        stop_trie(language); stop_trie(language,True)
        for variant in VARIANTS:
            target = destination/variant
            target.mkdir(parents=True,exist_ok=True)
            for kind in ('corpus','queries'):
                started = time.perf_counter()
                count = length = empty = 0
                with (source/f'{kind}.jsonl').open(encoding='utf-8') as inp, (target/f'{kind}.jsonl').open('w',encoding='utf-8',newline='\n') as out:
                    for line in inp:
                        record = json.loads(line)
                        record['text'] = transform(record['text'],language,variant)
                        out.write(json.dumps(record,ensure_ascii=False)+'\n')
                        count += 1; length += len(record['text']); empty += not record['text'].strip()
                        if count % 2000 == 0: print(language,variant,kind,count,flush=True)
                rows.append({'language':language,'variant':variant,'kind':kind,'records':count,'empty_records':empty,'mean_characters':round(length/count,3) if count else 0,'seconds':round(time.perf_counter()-started,3)})
                print(language,variant,kind,'done',count,flush=True)
        shutil.copyfile(source/'qrels.csv',destination/'qrels.csv')
    if input_hashes() != before: raise ValueError('Raw/canonical changed')
    reports = ROOT/'reports'
    with (reports/'dataset_summary.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader();writer.writerows(rows)
    manifest={'config':CONFIG,'versions':{p:importlib.metadata.version(p) for p in ('underthesea','nltk','pyarrow','pandas')},'input_sha256':before,'resource_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'resources/stopwords').glob('*.txt')},'output_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'data/processed').rglob('*')) if p.is_file()},'length_unit':'Unicode code points, not tokens'}
    (reports/'build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
