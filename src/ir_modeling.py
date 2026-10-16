import os
import json
import time
import math
import numpy as np
from collections import defaultdict, Counter
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

# =====================================================================
# 1. TỰ ĐỘNG DÒ TÌM ĐƯỜNG DẪN FILE CỦA 5 CẤU HÌNH (DO TV1 TẠO RA)
# =====================================================================
def find_dataset_files(base_dir, lang, variant):
    """
    Tự động tìm đường dẫn corpus.jsonl và queries.jsonl của từng cấu hình
    bất kể TV1 lưu theo cấu trúc thư mục nào trong data/processed.
    """
    candidates = [
        # Kiểu 1: data/processed/vi/original/corpus.jsonl
        (os.path.join(base_dir, "data", "processed", lang, variant, "corpus.jsonl"),
         os.path.join(base_dir, "data", "processed", lang, variant, "queries.jsonl")),
        # Kiểu 2: data/processed/original/vi/corpus.jsonl
        (os.path.join(base_dir, "data", "processed", variant, lang, "corpus.jsonl"),
         os.path.join(base_dir, "data", "processed", variant, lang, "queries.jsonl")),
        # Kiểu 3: data/processed/vi/corpus_original.jsonl
        (os.path.join(base_dir, "data", "processed", lang, f"corpus_{variant}.jsonl"),
         os.path.join(base_dir, "data", "processed", lang, f"queries_{variant}.jsonl")),
        # Kiểu 4: data/processed/vi_original_corpus.jsonl
        (os.path.join(base_dir, "data", "processed", f"{lang}_{variant}_corpus.jsonl"),
         os.path.join(base_dir, "data", "processed", f"{lang}_{variant}_queries.jsonl")),
    ]
    
    # Nếu là cấu hình 'original' và chưa có trong processed thì lấy trực tiếp từ canonical
    if variant == "original":
        candidates.append((
            os.path.join(base_dir, "data", "canonical", lang, "corpus.jsonl"),
            os.path.join(base_dir, "data", "canonical", lang, "queries.jsonl")
        ))

    for c_path, q_path in candidates:
        if os.path.exists(c_path) and os.path.exists(q_path):
            return c_path, q_path

    raise FileNotFoundError(
        f"Không tìm thấy file dữ liệu cho [{lang} - {variant}]. "
        f"Hãy chắc chắn bạn đã chạy: python src/build_variants.py"
    )


# =====================================================================
# 2. ĐỌC DỮ LIỆU ĐÚNG SCHEMA CỦA TV1
# =====================================================================
def load_jsonl(filepath, id_key):
    """
    Đọc file JSONL theo đúng quy tắc của TV1:
    - Giữ nguyên thứ tự và toàn bộ ID (kể cả khi text bị rỗng sau khi lọc stopword).
    """
    ids = []
    texts = []
    empty_count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            item_id = str(obj[id_key])
            text = obj.get("text") or ""
            if not text.strip():
                empty_count += 1
            ids.append(item_id)
            texts.append(text)
    return ids, texts, empty_count


# =====================================================================
# 3. XÂY DỰNG INVERTED INDEX & MA TRẬN SPARSE CHO TF-IDF VÀ BM25
# =====================================================================
class IRSystem:
    def __init__(self, doc_ids, doc_texts):
        self.doc_ids = np.array(doc_ids)
        self.doc_texts = doc_texts
        self.num_docs = len(doc_ids)
        
        # Khởi tạo Vectorizer giữ nguyên 100% token theo khoảng trắng của TV1
        # Không tự ý lowercase hay bỏ dấu câu để tôn trọng tuyệt đối 5 cấu hình của TV1
        self.vectorizer = TfidfVectorizer(
            tokenizer=str.split,
            lowercase=False,
            token_pattern=None,
            norm='l2',
            use_idf=True,
            smooth_idf=True
        )
        
        # Count matrix (TF) & TF-IDF matrix
        self.tfidf_matrix = self.vectorizer.fit_transform(doc_texts)
        self.vocab = self.vectorizer.vocabulary_
        self.idf_diag = self.vectorizer.idf_
        
        # Xây dựng cấu trúc Inverted Index tường minh để thống kê báo cáo
        self.inverted_index_stats = self._compute_index_stats()
        
        # Tiền tính toán ma trận BM25 dạng Sparse (Giúp chạy 10,000 queries chỉ mất 1 giây!)
        self.bm25_matrix, self.bm25_idf = self._build_bm25_sparse_matrix(k1=1.5, b=0.75)

    def _compute_index_stats(self):
        # Đếm số tài liệu chứa mỗi từ (Document Frequency) từ ma trận thưa
        csc = self.tfidf_matrix.tocsc()
        posting_lengths = np.diff(csc.indptr)
        return {
            "num_documents": int(self.num_docs),
            "vocabulary_size": int(len(self.vocab)),
            "total_postings": int(csc.nnz),
            "avg_posting_list_length": round(float(np.mean(posting_lengths)) if len(posting_lengths) > 0 else 0.0, 2),
            "max_posting_list_length": int(np.max(posting_lengths)) if len(posting_lengths) > 0 else 0
        }

    def _build_bm25_sparse_matrix(self, k1=1.5, b=0.75):
        """
        Biểu diễn công thức Okapi BM25 dưới dạng ma trận thưa (Sparse Matrix CSR).
        Nhờ vậy phép truy vấn BM25 biến thành phép nhân ma trận siêu tốc trên Inverted Index.
        """
        # Lấy tần suất từ thô (Raw Term Frequency) bằng cách dùng CountVectorizer cùng từ điển
        from sklearn.feature_extraction.text import CountVectorizer
        cv = CountVectorizer(tokenizer=str.split, lowercase=False, token_pattern=None, vocabulary=self.vocab)
        tf_matrix = cv.transform(self.doc_texts).tocsr().astype(np.float32)
        
        # Độ dài của từng tài liệu (số lượng token)
        doc_lengths = np.array(tf_matrix.sum(axis=1)).flatten()
        avgdl = float(np.mean(doc_lengths)) if self.num_docs > 0 else 1.0
        
        # Tính IDF chuẩn của BM25: log((N - df + 0.5) / (df + 0.5) + 1)
        df = np.diff(tf_matrix.tocsc().indptr)
        bm25_idf = np.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0).astype(np.float32)
        
        # Tính trọng số BM25 cho từng phần tử khác 0 trong ma trận TF
        rows, cols = tf_matrix.nonzero()
        tf_vals = tf_matrix.data
        dl_vals = doc_lengths[rows]
        
        norm_factor = k1 * (1.0 - b + b * (dl_vals / (avgdl + 1e-9)))
        bm25_weights = (tf_vals * (k1 + 1.0)) / (tf_vals + norm_factor)
        
        # Nhân với BM25 IDF
        bm25_weights = bm25_weights * bm25_idf[cols]
        
        bm25_CSR = csr_matrix((bm25_weights, (rows, cols)), shape=tf_matrix.shape, dtype=np.float32)
        return bm25_CSR, bm25_idf

    def search_batch(self, query_ids, query_texts, model_type="tfidf", top_k=50, batch_size=1000):
        """
        Chạy truy vấn theo từng batch để không bao giờ bị tràn RAM với bộ TVPL (9,985 queries).
        Giữ nguyên mọi query_id (kể cả query rỗng theo yêu cầu trong config.json của TV1).
        """
        results = {}
        num_queries = len(query_ids)
        
        if model_type == "tfidf":
            q_All_vec = self.vectorizer.transform(query_texts)
            doc_Mat_T = self.tfidf_matrix.T
        elif model_type == "bm25":
            from sklearn.feature_extraction.text import CountVectorizer
            cv = CountVectorizer(tokenizer=str.split, lowercase=False, token_pattern=None, vocabulary=self.vocab)
            q_All_vec = cv.transform(query_texts).astype(np.float32)
            doc_Mat_T = self.bm25_matrix.T
        else:
            raise ValueError("model_type phải là 'tfidf' hoặc 'bm25'")

        for start_idx in range(0, num_queries, batch_size):
            end_idx = min(start_idx + batch_size, num_queries)
            q_batch = q_All_vec[start_idx:end_idx]
            
            # Nhân ma trận thưa: (batch_queries x vocab) * (vocab x num_docs)
            scores_batch = (q_batch * doc_Mat_T).toarray()
            
            for i in range(end_idx - start_idx):
                q_id = query_ids[start_idx + i]
                scores = scores_batch[i]
                
                # Dùng argpartition để lấy Top-K cực nhanh O(N) thay vì sắp xếp toàn bộ O(N log N)
                if len(scores) > top_k:
                    top_k_unsorted = np.argpartition(scores, -top_k)[-top_k:]
                    top_indices = top_k_unsorted[np.argsort(scores[top_k_unsorted])[::-1]]
                else:
                    top_indices = np.argsort(scores)[::-1]
                
                # Chỉ giữ các tài liệu có điểm > 0 (nếu query rỗng hoặc không khớp từ nào thì trả về list rỗng [])
                ranked_docs = []
                rank = 1
                for doc_idx in top_indices:
                    sc = float(scores[doc_idx])
                    if sc <= 0.0:
                        break
                    ranked_docs.append({
                        "doc_id": str(self.doc_ids[doc_idx]),
                        "rank": rank,
                        "score": round(sc, 6)
                    })
                    rank += 1
                    
                results[q_id] = ranked_docs
                
        return results


# =====================================================================
# 4. CHƯƠNG TRÌNH CHÍNH: CHẠY TOÀN BỘ 20 KỊCH BẢN & XUẤT BÁO CÁO
# =====================================================================
def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config.json")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    languages = config.get("languages", ["vi", "en"])
    variants = config.get("variants", ["original", "stopword", "normalize", "tokenize", "combined"])
    
    output_dir = os.path.join(base_dir, "data", "retrieval_outputs")
    report_dir = os.path.join(base_dir, "reports")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    
    TOP_K = 50 # Xuất Top 50 tài liệu liên quan nhất (TV3 có thể cắt lấy Top 10, 20, 50 tùy ý)
    summary_stats = []

    print("=" * 75)
    print("🚀 BẮT ĐẦU CHẠY IR MODELING (THÀNH VIÊN 2): 2 NGÔN NGỮ x 5 CẤU HÌNH x 2 MÔ HÌNH")
    print("=" * 75)

    for lang in languages:
        for variant in variants:
            t0 = time.time()
            print(f"\n📌 Đang xử lý: Ngôn ngữ [{lang.upper()}] | Cấu hình [{variant}]")
            
            # 1. Tìm và đọc dữ liệu
            corpus_path, queries_path = find_dataset_files(base_dir, lang, variant)
            doc_ids, doc_texts, empty_docs = load_jsonl(corpus_path, "doc_id")
            query_ids, query_texts, empty_queries = load_jsonl(queries_path, "query_id")
            print(f"   - Đã nạp: {len(doc_ids):,} docs (rỗng: {empty_docs}) | {len(query_ids):,} queries (rỗng: {empty_queries})")
            
            # 2. Xây dựng Inverted Index + Mô hình
            t_idx_start = time.time()
            ir_sys = IRSystem(doc_ids, doc_texts)
            idx_time = round(time.time() - t_idx_start, 2)
            stats = ir_sys.inverted_index_stats
            print(f"   - Lập chỉ mục xong ({idx_time}s): Từ điển = {stats['vocabulary_size']:,} terms | TB Posting = {stats['avg_posting_list_length']}")
            
            # 3. Chạy truy vấn TF-IDF vàBM25
            for model_name in ["tfidf", "bm25"]:
                t_search_start = time.time()
                results = ir_sys.search_batch(query_ids, query_texts, model_type=model_name, top_k=TOP_K)
                search_time = round(time.time() - t_search_start, 2)
                
                # Lưu kết quả ra định dạng JSONL (mỗi dòng 1 query_id kèm danh sách top docs) để nhẹ và chuẩn như TV1
                out_file = os.path.join(output_dir, f"run_{lang}_{variant}_{model_name}.jsonl")
                with open(out_file, "w", encoding="utf-8") as out_f:
                    for q_id in query_ids:
                        line_obj = {
                            "query_id": q_id,
                            "results": results[q_id]
                        }
                        out_f.write(json.dumps(line_obj, ensure_ascii=False) + "\n")
                        
                print(f"   - [{model_name.upper()}] Truy xuất xong {len(query_ids):,} queries trong {search_time}s -> Lưu tại: {os.path.basename(out_file)}")
                
                summary_stats.append({
                    "language": lang,
                    "variant": variant,
                    "model": model_name,
                    "num_docs": len(doc_ids),
                    "num_queries": len(query_ids),
                    "empty_docs": empty_docs,
                    "empty_queries": empty_queries,
                    "vocab_size": stats["vocabulary_size"],
                    "total_postings": stats["total_postings"],
                    "avg_posting_len": stats["avg_posting_list_length"],
                    "index_time_sec": idx_time,
                    "search_time_sec": search_time,
                    "output_file": f"data/retrieval_outputs/run_{lang}_{variant}_{model_name}.jsonl"
                })

    # Lưu báo cáo tổng hợp của TV2 vào thư mục reports/
    manifest_path = os.path.join(report_dir, "tv2_retrieval_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 75)
    print(f"🎉 HOÀN TẤT TOÀN BỘ 20 KỊCH BẢN!")
    print(f"📂 Thư mục chứa 20 file kết quả bàn giao cho TV3: {output_dir}")
    print(f"📊 File thống kê Inverted Index & thời gian chạy: {manifest_path}")
    print("=" * 75)

if __name__ == "__main__":
    main()