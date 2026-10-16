import csv
import json
from preprocess import ROOT, VARIANTS, normalize, tokenize, transform, remove_stopwords, remove_stopwords_from_tokens

def main():
    samples = {
      'vi': ['Sinh vi\u00ean c\u00f3 th\u1ec3 h\u1ecdc t\u1eadp!!!','H\u1eccC,t\u1eadp!!!  123','v\u00e0 l\u00e0','', '!!!', 'URL https://example.vn \U0001f600','\u0110\u00c2Y   l\u00e0 V\u0102N B\u1ea2N.'],
      'en': ['THE theater and CAT!', 'Students cannot study.', 'and the', '', '!!!', 'URL https://example.org \U0001f600 123', 'Mixed   CASE, punctuation!!!']}
    checks = []
    def expect(name, condition):
        if not condition: raise AssertionError(name)
        checks.append(name)
    expect('Unicode accents and punctuation spacing', normalize('H\u1eccC,t\u1eadp!!!')=='h\u1ecdc t\u1eadp')
    expect('Substring and retained case',remove_stopwords('THE theater and CAT!','en')=='theater CAT!')
    expect('Longest Vietnamese phrase',remove_stopwords('c\u00f3 th\u1ec3 H\u1eccC','vi')=='H\u1eccC')
    expect('Vietnamese compound token','sinh_vi\u00ean' in tokenize('sinh vi\u00ean','vi'))
    expect('Combined multi-syllable stopword',transform('c\u00f3 th\u1ec3','vi','combined')=='')
    expect('Underscore boundary',remove_stopwords('the_cat','en')=='the_cat')
    rows=[]
    md=['# Preprocessing examples','', 'Actual outputs of the five configurations. Empty strings are shown as "".', '']
    for language,texts in samples.items():
        # Also include two real query records from each dataset.
        with (ROOT/'data/canonical'/language/'queries.jsonl').open(encoding='utf-8') as f:
            texts.extend(json.loads(next(f))['text'] for _ in range(2))
        for index,text in enumerate(texts):
            values={v:transform(text,language,v) for v in VARIANTS}
            expect(f'{language}/{index}: original unchanged',values['original']==text)
            expect(f'{language}/{index}: normalization idempotent',normalize(values['normalize'])==values['normalize'])
            tokens=values['combined'].split()
            expect(f'{language}/{index}: combined stopwords removed',remove_stopwords_from_tokens(tokens,language)==tokens)
            rows.append({'language':language,'sample':index,**values})
            md.extend([f'## {language} sample {index}', '', '```json',json.dumps(values,ensure_ascii=False,indent=2),'```',''])
    with (ROOT/'reports/preprocessing_examples.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (ROOT/'reports/preprocessing_examples.md').write_text('\n'.join(md),encoding='utf-8')
    (ROOT/'reports/sample_validation.json').write_text(json.dumps({'passed':True,'checks':checks},indent=2),encoding='utf-8')
    print(len(checks),'sample checks passed')
if __name__=='__main__': main()
