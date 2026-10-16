# Data Pipeline: canonical data

## Muc tieu
Chuyen TVPL (tieng Viet) va NFCorpus (tieng Anh) ve cung schema de ban giao cho phan truy xuat. Chua lowercase, xoa dau cau, tach tu hay bo stopword.

## Nguon va pham vi
- TVPL: https://huggingface.co/datasets/GreenNode/TVPL-Retrieval-VN
  Dung corpus/test, queries/test, qrels/test. License tren dataset card: CC-BY-SA-4.0.
  Corpus 10,576; queries 9,985; qrels 11,158; relevance = 1.
- NFCorpus ban BEIR: https://github.com/beir-cellar/beir/wiki/Datasets-available
  Goi tai: https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/nfcorpus.zip
  Nguon goc: https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/
  Dung toan bo corpus va qrels/test.tsv. File queries goc co 3,237 query; chi giu 323 query co ID trong qrels test.
  Corpus 3,633; qrels test 12,334; relevance giu nguyen cac gia tri 1, 2.
  Tham khao dieu khoan cua nguon goc truoc khi phan phoi lai; chua xac minh giay phep NFCorpus trong buoc nay.
- Du lieu tai trong phien lam viec ngay 2026-10-08 (Asia/Bangkok).
- Khong lay tap con corpus, khong dung seed.
- Hai bo khac mien: phap luat va y sinh/dinh duong. So sanh nam cau hinh trong tung bo; khong quy chenh lech diem giua hai bo chi cho ngon ngu.

## Thu muc
- data/raw: file goc, giu nguyen.
- data/canonical/vi va en: corpus.jsonl, queries.jsonl, qrels.csv.
- src/prepare_data.py: chuong trinh chuyen doi va kiem tra.
- reports/canonical_validation.json: so luong, schema TVPL, ID rong, text rong, SHA256 dau vao/dau ra.
- reports/canonical_examples.md: vi du that noi query -> qrel -> document; doan tai lieu duoc cat ngan chi de hien thi.
- data/processed va resources/stopwords: danh cho buoc tien xu ly sau, hien chua su dung.

## Quy tac chuyen doi
- Tai lieu: title + mot dau xuong dong + text. Phan rong/null duoc bo qua; khong strip, lowercase hay thay doi ky tu cua phan con lai.
- Query: giu nguyen text. Gia tri null neu co duoc luu thanh chuoi rong va thong ke; khong tu xoa ban ghi.
- ID luu dang chuoi, giu gia tri goc. TVPL id va NFCorpus _id doi ten thanh doc_id/query_id.
- Qrels: query-id -> query_id, corpus-id -> doc_id, score -> relevance. Khong doi thang nhan.
- Khong loai tai lieu trung noi dung. Khong coi cap khong co trong qrels la nhan am da xac nhan.
- Corpus va queries giu thu tu dau vao; NFCorpus loc query test theo thu tu file queries goc.

## Schema
corpus.jsonl: {"doc_id":"...","text":"..."}
queries.jsonl: {"query_id":"...","text":"..."}
qrels.csv: query_id,doc_id,relevance
Tat ca luu UTF-8. Moi dong JSONL la mot doi tuong JSON; xuong dong trong text duoc JSON escape.

## Cai va chay (PowerShell)
```powershell
cd D:\DataPipeline
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\prepare_data.py
```
Moi lan chay ghi lai cac file canonical va bao cao. Khong ghi vao raw.
Neu ID trung/thieu, qrels khong khop hay cap qrels trung, chuong trinh dung va bao loi.

## Kiem tra da thuc hien
- Doc du ca hai bo; kiem tra schema va ban ghi mau.
- ID duy nhat, khong rong; moi qrel tham chieu ID ton tai.
- Khong co tai lieu/query rong trong dau ra hien tai.
- Doc lai JSONL/CSV va doi chieu voi du lieu chuyen doi trong bo nho.
- SHA256 raw truoc/sau giong nhau.
- Chay lai hai lan: ca sau file canonical giong nhau tung byte.

## Buoc tiep theo
Viet nam cau hinh original, stopword, normalize, tokenize, combined; ap dung cung quy tac cho corpus va queries, giu nguyen ID va qrels.

## Tien xu ly: nam cau hinh
Cau hinh duoc luu trong config.json; cac script doc file nay.
- original: giu nguyen canonical (da ghep title + text).
- normalize: lowercase; giu chu Unicode, dau ket hop Unicode va chu so; thay ky tu con lai bang khoang trang; gop khoang trang. URL khong bi xoa nguyen cum: dau phan cach bi thay bang khoang trang; emoji bi thay bang khoang trang.
- tokenize: VI dung Underthesea format=text, use_token_normalize=False; tu nhieu am tiet co dau _. EN dung NLTK TreebankWordTokenizer, khong can tai Punkt. Tokenizer EN co the tach contractions (cannot -> can not), thay doi bieu dien dau ngoac kep; day la hanh vi tokenizer, khong them lowercase/stopword.
- stopword: khop khong phan biet hoa thuong tren ranh gioi chu/so Unicode; cum nhieu tu chi khop qua khoang trang, uu tien cum dai nhat. Khong tach tu bang Underthesea/NLTK o cau hinh nay. Giu dau cau va chu hoa/thuong cua phan con lai; gop khoang trang sau khi loai. Khong khop ben trong tu hay don vi noi bang dau _.
- combined: normalize -> tokenize -> remove stopwords. Stopword cung duoc normalize va tokenize bang cung cong cu; so khop chuoi token dai nhat de ho tro tu nhieu am tiet va dau _.

Nguon stopword:
- VI: https://github.com/stopwords/vietnamese-stopwords (MIT); file goc va noi dung thong bao ban quyen trong resources/stopwords/vi_source_README.md.
- EN: stopwords/english tu NLTK data: https://github.com/nltk/nltk_data/tree/gh-pages/packages/corpora
- resources/stopwords/sources.json ghi URL, ngay tai, SHA256. Khong sua danh sach goc; khi doc, bo dong rong, deduplicate va lowercase de so khop. Danh sach VI rong va co the loai tu mang thong tin trong mien phap luat; day la gioi han can ghi nhan, khong sua danh sach theo diem test.

## Lenh tien xu ly (PowerShell)
```powershell
cd D:\DataPipeline
.\.venv\Scripts\python.exe src\check_samples.py
.\.venv\Scripts\python.exe src\build_variants.py
.\.venv\Scripts\python.exe src\validate_data.py
```
Cac lenh ghi lai processed va bao cao; khong sua raw/canonical. Nen chay validate sau moi lan build.
- src/preprocess.py: cac ham normalize, tokenize, remove_stopwords, transform.
- src/check_samples.py: kiem tra edge cases va query that, luu preprocessing_examples.csv/md va sample_validation.json.
- src/build_variants.py: tao 20 JSONL va 2 qrels.csv, giu thu tu/ID, luu dataset_summary.csv va build_manifest.json.
- src/validate_data.py: kiem tra tung ban ghi, ID, qrels, input/output hash, tinh lai toan bo transform va hash noi dung de doi chieu tinh lap lai; luu validation_report.json.
- Thong ke do dai theo so ky tu Unicode (code points), khong phai so token. Thoi gian tinh theo giay, bao gom doc/ghi.
- Build manifest ghi phien ban Underthesea/NLTK va thu vien, cau hinh va checksum.
