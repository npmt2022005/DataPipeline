# 📋 BÁO CÁO THÀNH VIÊN 2 — IR MODELING
## Đề tài: Nghiên cứu ảnh hưởng của tiền xử lý văn bản đến kết quả truy xuất

---

## ✅ KIỂM TRA HOÀN THÀNH CÔNG VIỆC TV2

| Nhiệm vụ | Trạng thái | Chi tiết |
|---|---|---|
| Xây dựng 2 mô hình truy xuất (TF-IDF, BM25) | ✅ **XONG** | `src/ir_modeling.py` — class `IRSystem` |
| Indexing (Inverted Index / Sparse Matrix) | ✅ **XONG** | Tích hợp trong `IRSystem.__init__()` |
| Chạy truy vấn: 2 ngôn ngữ × 5 cấu hình × 2 mô hình = **20 kịch bản** | ✅ **XONG** | 20 file `.jsonl` trong `data/retrieval_outputs/` |
| Xuất Top-50 kết quả mỗi query | ✅ **XONG** | `TOP_K = 50` |
| Bàn giao file kết quả cho TV3 | ✅ **XONG** | 20 file `.jsonl` + manifest `reports/tv2_retrieval_manifest.json` |

> **Kết luận: Thành viên 2 đã HOÀN TẤT 100% nhiệm vụ được giao.** Đầu ra gồm 20 file kết quả truy xuất bàn giao cho TV3, đủ cả tiếng Việt và tiếng Anh, đủ 5 cấu hình tiền xử lý, đủ 2 mô hình.

---

## 📌 PHẦN 1 — DANH SÁCH CÁC TASK ĐÃ THỰC HIỆN

1. **Task 1 — Cài đặt môi trường & kiểm tra dữ liệu đầu vào từ TV1**
2. **Task 2 — Xây dựng mô hình TF-IDF** (dùng `sklearn.TfidfVectorizer` với Inverted Index dạng Sparse Matrix)
3. **Task 3 — Xây dựng mô hình BM25 (Okapi BM25)** (tính trọng số BM25 dạng Sparse Matrix CSR)
4. **Task 4 — Indexing: Nạp 5 phiên bản dữ liệu × 2 ngôn ngữ vào 2 mô hình**
5. **Task 5 — Chạy truy vấn Batch: 20 kịch bản** (Top-50 tài liệu/query)
6. **Task 6 — Xuất kết quả & tạo báo cáo Manifest bàn giao TV3**

---

## 📖 PHẦN 2 — MÔ TẢ CHI TIẾT TỪNG TASK

---

### 🔧 TASK 1 — Cài đặt môi trường & kiểm tra dữ liệu đầu vào

**Mục đích:** Chuẩn bị môi trường Python và xác nhận đã nhận đủ dữ liệu từ TV1.

#### Bước 1.1 — Tạo môi trường ảo (Virtual Environment)

```powershell
cd "D:\CSDL DPT\DataPipeline-main"
python -m venv .venv
```

> Tạo thư mục `.venv` chứa môi trường Python độc lập cho dự án.

#### Bước 1.2 — Kích hoạt môi trường ảo

```powershell
.\.venv\Scripts\Activate.ps1
```

> Sau lệnh này, terminal hiển thị `(.venv)` ở đầu dòng lệnh.

#### Bước 1.3 — Cài đặt thư viện

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> Cài đặt các thư viện cần thiết: `scikit-learn`, `numpy`, `scipy`, `underthesea`, `nltk`, v.v.

#### Bước 1.4 — Kiểm tra dữ liệu đầu vào từ TV1

```powershell
.\.venv\Scripts\python.exe src\check_samples.py
```

**Cấu trúc dữ liệu nhận từ TV1 (`data/processed/`):**

```
data/
├── processed/
│   ├── en/
│   │   ├── original/corpus.jsonl  queries.jsonl
│   │   ├── stopword/corpus.jsonl  queries.jsonl
│   │   ├── normalize/corpus.jsonl queries.jsonl
│   │   ├── tokenize/corpus.jsonl  queries.jsonl
│   │   └── combined/corpus.jsonl  queries.jsonl
│   └── vi/
│       ├── original/corpus.jsonl  queries.jsonl
│       ├── stopword/corpus.jsonl  queries.jsonl
│       ├── normalize/corpus.jsonl queries.jsonl
│       ├── tokenize/corpus.jsonl  queries.jsonl
│       └── combined/corpus.jsonl  queries.jsonl
```

**Schema file nhận (chuẩn TV1):**
- `corpus.jsonl`: `{"doc_id": "...", "text": "..."}`
- `queries.jsonl`: `{"query_id": "...", "text": "..."}`

**Thống kê dữ liệu đầu vào:**

| Ngôn ngữ | Corpus (docs) | Queries | Cấu hình |
|---|---|---|---|
| Tiếng Việt (TVPL) | 10,576 | 9,985 | 5 phiên bản |
| Tiếng Anh (NFCorpus) | 3,633 | 323 | 5 phiên bản |

---

### 🔧 TASK 2 — Xây dựng mô hình TF-IDF

**File:** [`src/ir_modeling.py`](file:///d:/CSDL%20DPT/DataPipeline-main/src/ir_modeling.py) — class `IRSystem`, phương thức `__init__()`

**Nguyên lý:**
TF-IDF (Term Frequency – Inverse Document Frequency) đo mức độ quan trọng của một từ trong tài liệu so với toàn bộ corpus.

```
TF-IDF(t, d) = TF(t,d) × IDF(t)
IDF(t) = log((1+N)/(1+df(t))) + 1   [smooth_idf=True]
```

#### Bước 2.1 — Khởi tạo TfidfVectorizer

```python
# Trong class IRSystem.__init__():
self.vectorizer = TfidfVectorizer(
    tokenizer=str.split,   # Tách bằng khoảng trắng, giữ nguyên token của TV1
    lowercase=False,       # KHÔNG tự lowercase — tôn trọng 5 cấu hình của TV1
    token_pattern=None,    # Vô hiệu regex mặc định
    norm='l2',             # Chuẩn hóa L2
    use_idf=True,
    smooth_idf=True
)
self.tfidf_matrix = self.vectorizer.fit_transform(doc_texts)
```

> **Lý do `lowercase=False`:** TV1 đã xử lý chữ hoa/thường theo từng cấu hình riêng. TV2 phải giữ nguyên 100% token để không làm lộn xộn kết quả so sánh.

#### Bước 2.2 — Xây dựng Inverted Index (tự động qua Sparse Matrix)

```python
# Thống kê Inverted Index từ ma trận thưa CSC
def _compute_index_stats(self):
    csc = self.tfidf_matrix.tocsc()
    posting_lengths = np.diff(csc.indptr)
    return {
        "vocabulary_size": len(self.vocab),
        "total_postings": csc.nnz,
        "avg_posting_list_length": np.mean(posting_lengths)
    }
```

**Ma trận TF-IDF dạng Sparse (CSR):**
- Hàng = tài liệu, Cột = từ trong từ điển
- Giá trị ≠ 0 chỉ khi từ xuất hiện trong tài liệu → tiết kiệm RAM

---

### 🔧 TASK 3 — Xây dựng mô hình BM25 (Okapi BM25)

**File:** [`src/ir_modeling.py`](file:///d:/CSDL%20DPT/DataPipeline-main/src/ir_modeling.py) — phương thức `_build_bm25_sparse_matrix()`

**Nguyên lý:**
BM25 là phiên bản nâng cao của TF-IDF, có tính đến độ dài tài liệu để tránh ưu tiên tài liệu dài.

```
BM25(t, d) = IDF(t) × [TF(t,d) × (k1+1)] / [TF(t,d) + k1×(1 - b + b×(|d|/avgdl))]
```

Tham số: `k1 = 1.5`, `b = 0.75` (giá trị tiêu chuẩn)

#### Bước 3.1 — Tính Raw Term Frequency

```python
from sklearn.feature_extraction.text import CountVectorizer
cv = CountVectorizer(tokenizer=str.split, lowercase=False,
                     token_pattern=None, vocabulary=self.vocab)
tf_matrix = cv.transform(self.doc_texts).tocsr().astype(np.float32)
```

#### Bước 3.2 — Tính độ dài tài liệu và avgdl

```python
doc_lengths = np.array(tf_matrix.sum(axis=1)).flatten()
avgdl = float(np.mean(doc_lengths))
```

#### Bước 3.3 — Tính IDF chuẩn BM25

```python
df = np.diff(tf_matrix.tocsc().indptr)
bm25_idf = np.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)
```

#### Bước 3.4 — Tính trọng số BM25 và lưu vào Sparse Matrix CSR

```python
norm_factor = k1 * (1.0 - b + b * (dl_vals / avgdl))
bm25_weights = (tf_vals * (k1 + 1.0)) / (tf_vals + norm_factor)
bm25_weights = bm25_weights * bm25_idf[cols]
bm25_CSR = csr_matrix((bm25_weights, (rows, cols)), shape=tf_matrix.shape)
```

> **Tối ưu hóa:** Tiền tính ma trận BM25 dạng Sparse CSR → phép tìm kiếm trở thành phép nhân ma trận, giúp xử lý 9,985 queries trong ~3-5 giây thay vì hàng giờ.

---

### 🔧 TASK 4 — Indexing: Nạp dữ liệu vào 2 mô hình

**File:** [`src/ir_modeling.py`](file:///d:/CSDL%20DPT/DataPipeline-main/src/ir_modeling.py) — hàm `main()`

#### Bước 4.1 — Đọc cấu hình từ `config.json`

```powershell
# Kiểm tra config
type config.json
```

```json
{
  "languages": ["vi", "en"],
  "variants": ["original", "stopword", "normalize", "tokenize", "combined"]
}
```

#### Bước 4.2 — Tự động tìm file dữ liệu (hàm `find_dataset_files`)

```python
# Hỗ trợ nhiều kiểu cấu trúc thư mục TV1 có thể dùng:
# Kiểu 1: data/processed/vi/original/corpus.jsonl
# Kiểu 2: data/processed/original/vi/corpus.jsonl
# Kiểu 3: data/processed/vi/corpus_original.jsonl
# Kiểu 4: data/processed/vi_original_corpus.jsonl
# Fallback: data/canonical/vi/corpus.jsonl (chỉ cho variant "original")
```

#### Bước 4.3 — Chạy lệnh Indexing + Retrieval

```powershell
.\.venv\Scripts\python.exe src\ir_modeling.py
```

**Vòng lặp indexing (10 lần Index, 20 lần Search):**

```
for lang in ["vi", "en"]:           # 2 ngôn ngữ
    for variant in [5 cấu hình]:    # 5 cấu hình
        ir_sys = IRSystem(docs)     # → Xây dựng Index TF-IDF + BM25
        for model in ["tfidf", "bm25"]:
            results = ir_sys.search_batch(queries)   # → Truy xuất
```

**Thống kê Inverted Index sau khi nạp (ví dụ):**

| Lang | Variant | Vocab Size | Total Postings | Avg Posting Len | Index Time |
|---|---|---|---|---|---|
| VI | original | 23,388 | 1,102,081 | 47.12 | 1.9s |
| VI | normalize | 6,513 | 970,596 | 149.02 | 1.12s |
| VI | combined | 16,373 | 470,179 | 28.72 | 0.94s |
| EN | original | 72,545 | 520,631 | 7.18 | 1.46s |
| EN | normalize | 26,469 | 478,351 | 18.07 | 1.09s |
| EN | combined | 26,338 | 383,282 | 14.55 | 0.69s |

---

### 🔧 TASK 5 — Chạy truy vấn Batch: 20 kịch bản

**File:** [`src/ir_modeling.py`](file:///d:/CSDL%20DPT/DataPipeline-main/src/ir_modeling.py) — phương thức `search_batch()`

#### Bước 5.1 — Kỹ thuật Batch Search (tránh tràn RAM)

```python
def search_batch(self, query_ids, query_texts, model_type="tfidf",
                  top_k=50, batch_size=1000):
    # Xử lý 1000 queries mỗi lần → không bao giờ tràn RAM
    # với bộ TVPL 9,985 queries
```

#### Bước 5.2 — TF-IDF Search

```python
q_vec = self.vectorizer.transform(query_texts)   # query → vector TF-IDF
scores = (q_vec * self.tfidf_matrix.T).toarray() # dot product
```

#### Bước 5.3 — BM25 Search

```python
q_vec = CountVectorizer(...).transform(query_texts)  # query → vector TF thô
scores = (q_vec * self.bm25_matrix.T).toarray()      # dot product với BM25 matrix
```

#### Bước 5.4 — Lấy Top-K nhanh bằng `argpartition`

```python
# O(N) thay vì O(N log N) của argsort toàn bộ
top_k_unsorted = np.argpartition(scores, -top_k)[-top_k:]
top_indices = top_k_unsorted[np.argsort(scores[top_k_unsorted])[::-1]]
```

**Thời gian chạy truy vấn (từ Manifest):**

| Lang | Variant | TF-IDF Time | BM25 Time |
|---|---|---|---|
| VI | original | 5.44s | 4.66s |
| VI | stopword | 3.16s | 2.52s |
| VI | normalize | 4.21s | 3.71s |
| VI | tokenize | 3.63s | 3.58s |
| VI | combined | 3.98s | 2.64s |
| EN | original | 0.14s | 0.09s |
| EN | stopword | 0.07s | 0.09s |
| EN | normalize | 0.10s | 0.07s |
| EN | tokenize | 0.07s | 0.09s |
| EN | combined | 0.10s | 0.09s |

---

### 🔧 TASK 6 — Xuất kết quả & Tạo Manifest bàn giao TV3

#### Bước 6.1 — Format file kết quả JSONL

Mỗi file output có định dạng: **một dòng = một query**

```json
{"query_id": "1", "results": [
    {"doc_id": "vbpl_abc", "rank": 1, "score": 0.854321},
    {"doc_id": "vbpl_xyz", "rank": 2, "score": 0.741200},
    ...
]}
```

#### Bước 6.2 — Quy tắc đặt tên file output

```
run_{lang}_{variant}_{model}.jsonl

Ví dụ:
  run_vi_original_tfidf.jsonl
  run_vi_combined_bm25.jsonl
  run_en_normalize_tfidf.jsonl
```

#### Bước 6.3 — Tạo Manifest JSON cho TV3

```powershell
# Lệnh chạy toàn bộ:
.\.venv\Scripts\python.exe src\ir_modeling.py
```

File manifest được tự động tạo tại `reports/tv2_retrieval_manifest.json`.

---

## 🏆 PHẦN 3 — THÀNH QUẢ

### 3.1 — 20 File Kết Quả Truy Xuất (Bàn giao cho TV3)

| STT | File | Ngôn ngữ | Cấu hình | Mô hình | Kích thước |
|---|---|---|---|---|---|
| 1 | `run_vi_original_tfidf.jsonl` | Việt | Gốc | TF-IDF | ~42 MB |
| 2 | `run_vi_original_bm25.jsonl` | Việt | Gốc | BM25 | ~42 MB |
| 3 | `run_vi_stopword_tfidf.jsonl` | Việt | Loại SW | TF-IDF | ~42 MB |
| 4 | `run_vi_stopword_bm25.jsonl` | Việt | Loại SW | BM25 | ~42 MB |
| 5 | `run_vi_normalize_tfidf.jsonl` | Việt | Chuẩn hóa | TF-IDF | ~42 MB |
| 6 | `run_vi_normalize_bm25.jsonl` | Việt | Chuẩn hóa | BM25 | ~42 MB |
| 7 | `run_vi_tokenize_tfidf.jsonl` | Việt | Tách từ | TF-IDF | ~42 MB |
| 8 | `run_vi_tokenize_bm25.jsonl` | Việt | Tách từ | BM25 | ~42 MB |
| 9 | `run_vi_combined_tfidf.jsonl` | Việt | Kết hợp | TF-IDF | ~42 MB |
| 10 | `run_vi_combined_bm25.jsonl` | Việt | Kết hợp | BM25 | ~42 MB |
| 11 | `run_en_original_tfidf.jsonl` | Anh | Gốc | TF-IDF | ~580 KB |
| 12 | `run_en_original_bm25.jsonl` | Anh | Gốc | BM25 | ~580 KB |
| 13 | `run_en_stopword_tfidf.jsonl` | Anh | Loại SW | TF-IDF | ~478 KB |
| 14 | `run_en_stopword_bm25.jsonl` | Anh | Loại SW | BM25 | ~477 KB |
| 15 | `run_en_normalize_tfidf.jsonl` | Anh | Chuẩn hóa | TF-IDF | ~630 KB |
| 16 | `run_en_normalize_bm25.jsonl` | Anh | Chuẩn hóa | BM25 | ~629 KB |
| 17 | `run_en_tokenize_tfidf.jsonl` | Anh | Tách từ | TF-IDF | ~604 KB |
| 18 | `run_en_tokenize_bm25.jsonl` | Anh | Tách từ | BM25 | ~603 KB |
| 19 | `run_en_combined_tfidf.jsonl` | Anh | Kết hợp | TF-IDF | ~614 KB |
| 20 | `run_en_combined_bm25.jsonl` | Anh | Kết hợp | BM25 | ~613 KB |

**Vị trí:** [`data/retrieval_outputs/`](file:///d:/CSDL%20DPT/DataPipeline-main/data/retrieval_outputs)

### 3.2 — Manifest Bàn Giao TV3

**File:** [`reports/tv2_retrieval_manifest.json`](file:///d:/CSDL%20DPT/DataPipeline-main/reports/tv2_retrieval_manifest.json)

Chứa thông tin chi tiết 20 kịch bản:
- Số docs, số queries, số docs/queries rỗng
- Kích thước từ điển (vocab_size)
- Tổng posting (total_postings)
- Thời gian indexing & search
- Đường dẫn file output

### 3.3 — Thống kê Inverted Index theo Cấu hình (Tiếng Việt)

```
Cấu hình         | Vocab Size | Avg Posting | Nhận xét
-----------------|------------|-------------|----------------------------------
original         |   23,388   |   47.12     | Từ điển lớn, nhiều nhiễu
stopword         |   21,074   |   34.97     | Giảm ~10% vocab, giảm nhiễu
normalize        |    6,513   |  149.02     | Vocab nhỏ nhất, posting dài nhất
tokenize         |   21,631   |   38.01     | Tách từ ghép tiếng Việt
combined         |   16,373   |   28.72     | Posting ngắn nhất → tìm kiếm chính xác nhất
```

### 3.4 — File Source Code TV2

| File | Vai trò |
|---|---|
| [`src/ir_modeling.py`](file:///d:/CSDL%20DPT/DataPipeline-main/src/ir_modeling.py) | **CHÍNH** — Toàn bộ logic TF-IDF, BM25, Indexing, Retrieval |
| [`config.json`](file:///d:/CSDL%20DPT/DataPipeline-main/config.json) | Cấu hình ngôn ngữ và variants |
| [`reports/tv2_retrieval_manifest.json`](file:///d:/CSDL%20DPT/DataPipeline-main/reports/tv2_retrieval_manifest.json) | Báo cáo thống kê 20 kịch bản |

---

## 📊 SƠ ĐỒ LUỒNG CÔNG VIỆC TV2

```
TV1 bàn giao 10 thư mục JSONL
         │
         ▼
[TASK 1] Kiểm tra cấu trúc & schema dữ liệu
         │
         ▼
[TASK 2] Xây dựng TF-IDF Model (Sparse Matrix L2-norm)
         │
[TASK 3] Xây dựng BM25 Model (Sparse CSR Matrix, k1=1.5, b=0.75)
         │
         ▼
[TASK 4] for lang in {vi, en}:
           for variant in {original, stopword, normalize, tokenize, combined}:
             → IRSystem(corpus) = Inverted Index + TF-IDF matrix + BM25 matrix
         │
         ▼
[TASK 5] for model in {tfidf, bm25}:
           → search_batch(queries, top_k=50) — Batch 1000 queries/lần
           → Xuất run_{lang}_{variant}_{model}.jsonl
         │
         ▼
[TASK 6] Lưu 20 file JSONL + tv2_retrieval_manifest.json
         │
         ▼
    Bàn giao TV3 ✅
```

---

*Báo cáo được tạo tự động — Thành Viên 2 | IR Modeling*
