"""
=============================================================================
app.py – Web Demo: Nghiên cứu ảnh hưởng Tiền xử lý văn bản đến IR
=============================================================================
Chế độ hoạt động: Tra cứu tĩnh (Static Lookup)
  - Đọc các file kết quả đã chạy sẵn để hiển thị trực quan.
  - Không tính toán live.

Cách chạy:
  streamlit run app.py
=============================================================================
"""

import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# ─────────────────────────────────────────────────────────────────────────────
# CẤU HÌNH ĐƯỜNG DẪN VÀ HẰNG SỐ
# ─────────────────────────────────────────────────────────────────────────────

# Thư mục gốc của dự án (cùng cấp với app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR       = os.path.join(BASE_DIR, "data")
CANONICAL_DIR  = os.path.join(DATA_DIR, "canonical")
RETRIEVAL_DIR  = os.path.join(DATA_DIR, "retrieval_outputs")
EVAL_CSV_PATH  = os.path.join(BASE_DIR, "reports", "evaluation", "evaluation_results.csv")

# Ánh xạ tên hiển thị → giá trị nội bộ (key)
LANG_OPTIONS = {
    "🇬🇧 Tiếng Anh": "en",
    "🇻🇳 Tiếng Việt": "vi",
}

VARIANT_OPTIONS = {
    "Gốc (Original)":            "original",
    "Lọc Stopword":              "stopword",
    "Chuẩn hóa (Normalize)":    "normalize",
    "Tách từ (Tokenize)":        "tokenize",
    "Kết hợp (Combined)":        "combined",
}

MODEL_OPTIONS = {
    "TF-IDF": "tfidf",
    "BM25":   "bm25",
}

TOP_K = 10  # Số lượng tài liệu hiển thị

# ─────────────────────────────────────────────────────────────────────────────
# CÁC HÀM ĐỌC DỮ LIỆU – DÙNG @st.cache_data ĐỂ NẠP 1 LẦN DUY NHẤT
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Đang tải danh sách truy vấn...")
def load_queries(lang: str) -> dict[str, str]:
    """
    Đọc file queries.jsonl và trả về dict {query_id: text}.

    Args:
        lang: 'en' hoặc 'vi'

    Returns:
        Dict ánh xạ query_id → text, hoặc dict rỗng nếu file không tồn tại.
    """
    path = os.path.join(CANONICAL_DIR, lang, "queries.jsonl")
    result = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                result[obj["query_id"]] = obj["text"]
    except FileNotFoundError:
        st.warning(f"⚠️ Không tìm thấy file queries: `{path}`")
    except json.JSONDecodeError as e:
        st.error(f"❌ Lỗi parse JSON trong queries.jsonl: {e}")
    return result


@st.cache_data(show_spinner="Đang tải kho ngữ liệu (corpus)...")
def load_corpus(lang: str) -> dict[str, str]:
    """
    Đọc file corpus.jsonl và trả về dict {doc_id: text}.

    Args:
        lang: 'en' hoặc 'vi'

    Returns:
        Dict ánh xạ doc_id → text, hoặc dict rỗng nếu file không tồn tại.
    """
    path = os.path.join(CANONICAL_DIR, lang, "corpus.jsonl")
    result = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                result[obj["doc_id"]] = obj["text"]
    except FileNotFoundError:
        st.warning(f"⚠️ Không tìm thấy file corpus: `{path}`")
    except json.JSONDecodeError as e:
        st.error(f"❌ Lỗi parse JSON trong corpus.jsonl: {e}")
    return result


@st.cache_data(show_spinner="Đang tải nhãn đánh giá (qrels)...")
def load_qrels(lang: str) -> dict[str, set[str]]:
    """
    Đọc file qrels.csv và trả về dict {query_id: set(doc_id_relevant)}.
    Chỉ lấy các tài liệu có relevance > 0.

    Args:
        lang: 'en' hoặc 'vi'

    Returns:
        Dict ánh xạ query_id → tập hợp các doc_id liên quan.
    """
    path = os.path.join(CANONICAL_DIR, lang, "qrels.csv")
    result: dict[str, set[str]] = {}
    try:
        df = pd.read_csv(path, dtype=str)
        # Chuẩn hóa tên cột (phòng trường hợp có khoảng trắng thừa)
        df.columns = df.columns.str.strip()
        for _, row in df.iterrows():
            qid = str(row["query_id"]).strip()
            did = str(row["doc_id"]).strip()
            rel = float(row.get("relevance", 1))
            if rel > 0:
                result.setdefault(qid, set()).add(did)
    except FileNotFoundError:
        st.warning(f"⚠️ Không tìm thấy file qrels: `{path}`")
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc qrels.csv: {e}")
    return result


@st.cache_data(show_spinner="Đang tải kết quả truy xuất...")
def load_run_file(lang: str, variant: str, model: str) -> dict[str, list[dict]]:
    """
    Đọc file kết quả truy xuất run_{lang}_{variant}_{model}.jsonl.
    Trả về dict {query_id: [{"doc_id": ..., "rank": ..., "score": ...}, ...]}.

    Args:
        lang:    'en' hoặc 'vi'
        variant: 'original', 'stopword', 'normalize', 'tokenize', 'combined'
        model:   'tfidf' hoặc 'bm25'

    Returns:
        Dict ánh xạ query_id → danh sách kết quả đã sắp xếp theo rank.
    """
    filename = f"run_{lang}_{variant}_{model}.jsonl"
    path = os.path.join(RETRIEVAL_DIR, filename)
    result = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                qid = obj["query_id"]
                # Sắp xếp theo rank để đảm bảo thứ tự đúng
                docs = sorted(obj.get("results", []), key=lambda x: x.get("rank", 9999))
                result[qid] = docs
    except FileNotFoundError:
        st.error(
            f"❌ Không tìm thấy file kết quả: `{filename}`\n\n"
            f"Đường dẫn đầy đủ: `{path}`"
        )
    except json.JSONDecodeError as e:
        st.error(f"❌ Lỗi parse JSON trong {filename}: {e}")
    return result


@st.cache_data(show_spinner="Đang tải bảng đánh giá tổng hợp...")
def load_eval_results() -> pd.DataFrame | None:
    """
    Đọc file evaluation_results.csv để hiển thị bảng chỉ số tổng hợp.

    Returns:
        DataFrame hoặc None nếu file không tồn tại.
    """
    try:
        df = pd.read_csv(EVAL_CSV_PATH)
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        return None
    except Exception as e:
        st.warning(f"⚠️ Không thể tải bảng đánh giá: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# HÀM TIỆN ÍCH
# ─────────────────────────────────────────────────────────────────────────────

def truncate_text(text: str, max_chars: int = 500) -> str:
    """Cắt ngắn chuỗi và thêm '...' nếu vượt quá giới hạn."""
    if len(text) > max_chars:
        return text[:max_chars].rstrip() + "…"
    return text


def build_query_label(query_id: str, text: str, max_preview: int = 80) -> str:
    """Tạo nhãn hiển thị cho dropdown query: [ID] - Trích dẫn ngắn."""
    preview = truncate_text(text, max_preview)
    return f"[{query_id}] – {preview}"


# ─────────────────────────────────────────────────────────────────────────────
# CẤU HÌNH TRANG STREAMLIT
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="IR Demo – Tiền xử lý & Truy xuất",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS tùy chỉnh để làm đẹp các thẻ kết quả
st.markdown("""
<style>
    /* Card tài liệu kết quả */
    .doc-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .doc-card:hover {
        border-color: #6c757d;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    /* Badge liên quan */
    .badge-relevant {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
    }
    .badge-irrelevant {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
    }

    /* Header của mỗi card */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .rank-score {
        font-size: 0.9em;
        color: #495057;
    }
    .doc-id {
        font-weight: 700;
        font-size: 1.0em;
        color: #212529;
    }
    .doc-text {
        font-size: 0.92em;
        color: #343a40;
        line-height: 1.55;
    }
    /* Thanh tiêu đề trang */
    .page-title {
        font-size: 1.6em;
        font-weight: 700;
        color: #1a1a2e;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR – THANH ĐIỀU KHIỂN
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Cấu hình tra cứu")
    st.divider()

    # 1. Chọn ngôn ngữ
    lang_label = st.radio(
        "🌐 Ngôn ngữ",
        options=list(LANG_OPTIONS.keys()),
        index=0,
        help="Chọn tập dữ liệu ngôn ngữ để tra cứu.",
    )
    lang = LANG_OPTIONS[lang_label]

    st.divider()

    # 2. Chọn biến thể tiền xử lý
    variant_label = st.selectbox(
        "🔧 Cấu hình tiền xử lý",
        options=list(VARIANT_OPTIONS.keys()),
        index=0,
        help=(
            "Chọn pipeline tiền xử lý:\n"
            "- **Gốc**: Không tiền xử lý\n"
            "- **Lọc Stopword**: Loại bỏ từ dừng\n"
            "- **Chuẩn hóa**: Lowercasing, stemming/lemmatization\n"
            "- **Tách từ**: Tokenization\n"
            "- **Kết hợp**: Áp dụng tất cả"
        ),
    )
    variant = VARIANT_OPTIONS[variant_label]

    st.divider()

    # 3. Chọn mô hình
    model_label = st.radio(
        "🤖 Mô hình truy xuất",
        options=list(MODEL_OPTIONS.keys()),
        index=0,
        help="TF-IDF hoặc BM25.",
    )
    model = MODEL_OPTIONS[model_label]

    st.divider()

    # Thông tin file đang dùng
    run_filename = f"run_{lang}_{variant}_{model}.jsonl"
    st.caption(f"📂 File kết quả: `{run_filename}`")

    # Hiển thị chỉ số tổng hợp của cấu hình đang chọn
    eval_df = load_eval_results()
    if eval_df is not None:
        mask = (
            (eval_df["Language"].str.upper() == lang.upper())
            & (eval_df["Model"].str.upper() == model.upper())
            & (eval_df["Variant"].str.lower() == variant.lower())
        )
        row = eval_df[mask]
        if not row.empty:
            st.markdown("### 📊 Chỉ số đánh giá")
            r = row.iloc[0]
            col_m, col_p = st.columns(2)
            col_m.metric("MAP", f"{float(r['MAP']):.4f}")
            col_p.metric("P@10", f"{float(r['P@10']):.4f}")
        else:
            st.caption("_(Không có số liệu đánh giá cho cấu hình này)_")


# ─────────────────────────────────────────────────────────────────────────────
# NẠP DỮ LIỆU CHO NGÔN NGỮ ĐANG CHỌN
# ─────────────────────────────────────────────────────────────────────────────

queries_map = load_queries(lang)
corpus_map  = load_corpus(lang)
qrels_map   = load_qrels(lang)
run_data    = load_run_file(lang, variant, model)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT – NỘI DUNG CHÍNH
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    "<div class='page-title'>🔍 Demo Hệ thống Truy xuất Thông tin (IR)</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "*Nghiên cứu ảnh hưởng của Tiền xử lý Văn bản đến kết quả Truy xuất – Chế độ Tra cứu Tĩnh*"
)
st.divider()

# ── Kiểm tra dữ liệu đã tải thành công chưa ──────────────────────────────────
if not queries_map:
    st.error(
        "❌ Không tải được danh sách truy vấn. "
        "Vui lòng kiểm tra lại đường dẫn thư mục `data/canonical/`."
    )
    st.stop()

# ── Hai Tab chính ─────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔎 Tra cứu Truy vấn", "📊 Biểu đồ Tổng hợp"])

# =============================================================================
# TAB 1 – TRA CỨU TRUY VẤN (logic cũ, giữ nguyên)
# =============================================================================
with tab1:
    # ── Dropdown chọn Query ───────────────────────────────────────────────────
    st.markdown("### 📝 Chọn câu truy vấn (Query)")

    # Xây dựng danh sách nhãn cho dropdown
    query_ids     = list(queries_map.keys())
    query_labels  = [build_query_label(qid, queries_map[qid]) for qid in query_ids]
    label_to_id   = dict(zip(query_labels, query_ids))

    selected_label = st.selectbox(
        "Chọn câu truy vấn:",
        options=query_labels,
        index=0,
        label_visibility="collapsed",
    )

    selected_query_id   = label_to_id[selected_label]
    selected_query_text = queries_map[selected_query_id]

    # Hiển thị toàn bộ nội dung query đã chọn
    with st.container(border=True):
        st.markdown(f"**🔎 Query ID:** `{selected_query_id}`")
        st.markdown(f"**Nội dung:** {selected_query_text}")

    st.divider()

    # ── Kết quả truy xuất Top-K ───────────────────────────────────────────────
    st.markdown(f"### 📋 Top {TOP_K} tài liệu truy xuất")
    st.caption(
        f"Cấu hình: **{lang_label}** | **{variant_label}** | **{model_label}**"
    )

    # Lấy danh sách kết quả của query đang chọn
    if not run_data:
        st.warning(
            "⚠️ Không có dữ liệu kết quả truy xuất. "
            "Kiểm tra lại file `data/retrieval_outputs/`."
        )
    else:
        query_results = run_data.get(selected_query_id, [])

        if not query_results:
            st.info(
                f"ℹ️ Không tìm thấy kết quả nào cho query `{selected_query_id}` "
                f"trong file `{run_filename}`."
            )
        else:
            # Tập hợp các doc_id liên quan với query đang chọn (từ qrels)
            relevant_doc_ids: set[str] = qrels_map.get(selected_query_id, set())

            # Thống kê nhanh số lượng relevant trong Top-K
            top_k_results   = query_results[:TOP_K]
            relevant_in_top = sum(
                1 for r in top_k_results if r["doc_id"] in relevant_doc_ids
            )

            # Hiển thị tóm tắt
            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng tài liệu liên quan (qrels)", len(relevant_doc_ids))
            col2.metric(f"Relevant trong Top {TOP_K}", relevant_in_top)
            col3.metric(f"P@{TOP_K}", f"{relevant_in_top / TOP_K:.2f}")

            st.markdown("---")

            # ── Render từng thẻ tài liệu ─────────────────────────────────────
            for item in top_k_results:
                doc_id  = item.get("doc_id", "N/A")
                rank    = item.get("rank", "?")
                score   = item.get("score", 0.0)

                # Kiểm tra tính liên quan
                is_relevant = doc_id in relevant_doc_ids

                # Lấy nội dung tài liệu từ corpus
                doc_text_full = corpus_map.get(doc_id, "")
                if doc_text_full:
                    doc_text_display = truncate_text(doc_text_full, max_chars=500)
                else:
                    doc_text_display = "_⚠️ Không tìm thấy nội dung tài liệu này trong corpus._"

                # Chọn badge tương ứng
                if is_relevant:
                    badge_html = (
                        '<span class="badge-relevant">✅ Relevant – Có liên quan</span>'
                    )
                else:
                    badge_html = (
                        '<span class="badge-irrelevant">❌ Non-relevant – Không liên quan</span>'
                    )

                # Render card bằng HTML + Streamlit container
                with st.container():
                    st.markdown(
                        f"""
<div class="doc-card">
    <div class="card-header">
        <span class="doc-id">#{rank} &nbsp; {doc_id}</span>
        <span>{badge_html}</span>
    </div>
    <div class="rank-score">📊 Score: <strong>{score:.6f}</strong></div>
    <hr style="margin: 8px 0; border-color: #e9ecef;">
    <div class="doc-text">{doc_text_display}</div>
</div>
                        """,
                        unsafe_allow_html=True,
                    )


# =============================================================================
# TAB 2 – BIỂU ĐỒ SO SÁNH TỔNG HỢP (tính năng mới)
# =============================================================================
with tab2:
    st.markdown("### 📊 So sánh chỉ số đánh giá theo cấu hình tiền xử lý")

    # Thứ tự cố định của các variant trên trục X
    VARIANT_ORDER = ["original", "stopword", "normalize", "tokenize", "combined"]
    VARIANT_LABEL_MAP = {
        "original":  "Gốc (Original)",
        "stopword":  "Lọc Stopword",
        "normalize": "Chuẩn hóa (Normalize)",
        "tokenize":  "Tách từ (Tokenize)",
        "combined":  "Kết hợp (Combined)",
    }

    # Màu sắc chuẩn mực cho từng mô hình
    MODEL_COLOR_MAP = {
        "TFIDF": "#1f77b4",   # Xanh dương
        "BM25":  "#d62728",   # Đỏ
    }

    # ── Kiểm tra eval_df có dữ liệu không ────────────────────────────────────
    if eval_df is None or eval_df.empty:
        st.warning(
            "⚠️ Không tải được dữ liệu đánh giá tổng hợp. "
            "Kiểm tra file `reports/evaluation/evaluation_results.csv`."
        )
    else:
        try:
            # ── Bộ điều khiển (Controls) ──────────────────────────────────────
            ctrl_col1, ctrl_col2 = st.columns([1, 2])

            with ctrl_col1:
                selected_metric = st.selectbox(
                    "📈 Chọn chỉ số (Metric)",
                    options=["MAP", "P@10", "P@50"],
                    index=0,
                    help="MAP: Mean Average Precision | P@10: Precision tại 10 | P@50: Precision tại 50",
                )

            with ctrl_col2:
                selected_chart_lang = st.radio(
                    "🌐 Chọn ngôn ngữ hiển thị",
                    options=["EN", "VI"],
                    index=0,
                    horizontal=True,
                    help="Lọc biểu đồ theo ngôn ngữ của tập dữ liệu.",
                )

            st.divider()

            # ── Lọc dataframe theo ngôn ngữ đã chọn ──────────────────────────
            df_plot = eval_df[
                eval_df["Language"].str.upper() == selected_chart_lang.upper()
            ].copy()

            if df_plot.empty:
                st.info(
                    f"ℹ️ Không có dữ liệu cho ngôn ngữ **{selected_chart_lang}**."
                )
            else:
                # Chuẩn hóa cột Variant và Model để đảm bảo nhất quán
                df_plot["Variant"] = df_plot["Variant"].str.lower().str.strip()
                df_plot["Model"]   = df_plot["Model"].str.upper().str.strip()

                # Ánh xạ Variant key → nhãn hiển thị thân thiện
                df_plot["Variant_Label"] = df_plot["Variant"].map(VARIANT_LABEL_MAP)

                # Chuyển cột metric sang float (phòng trường hợp dạng string)
                df_plot[selected_metric] = pd.to_numeric(
                    df_plot[selected_metric], errors="coerce"
                )

                # Sắp xếp theo thứ tự cố định của variant
                df_plot["Variant_Order"] = df_plot["Variant"].map(
                    {v: i for i, v in enumerate(VARIANT_ORDER)}
                )
                df_plot = df_plot.sort_values(["Variant_Order", "Model"])

                # Thêm cột text nhãn làm tròn 4 chữ số
                df_plot["text_label"] = df_plot[selected_metric].apply(
                    lambda v: f"{v:.4f}" if pd.notna(v) else ""
                )

                # ── Vẽ Grouped Bar Chart bằng Plotly ─────────────────────────
                lang_display = "Tiếng Anh (EN)" if selected_chart_lang == "EN" else "Tiếng Việt (VI)"

                fig = px.bar(
                    df_plot,
                    x="Variant_Label",
                    y=selected_metric,
                    color="Model",
                    barmode="group",
                    text="text_label",
                    color_discrete_map=MODEL_COLOR_MAP,
                    category_orders={
                        "Variant_Label": [VARIANT_LABEL_MAP[v] for v in VARIANT_ORDER],
                        "Model": ["TFIDF", "BM25"],
                    },
                    title=(
                        f"So sánh <b>{selected_metric}</b> theo cấu hình tiền xử lý "
                        f"– {lang_display}"
                    ),
                    labels={
                        "Variant_Label": "Cấu hình tiền xử lý",
                        selected_metric: selected_metric,
                        "Model": "Mô hình",
                    },
                )

                # Cấu hình layout & text
                fig.update_traces(
                    textposition="outside",
                    textfont_size=11,
                    cliponaxis=False,
                )
                fig.update_layout(
                    font=dict(family="Arial, sans-serif", size=13),
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    xaxis=dict(
                        title="Cấu hình tiền xử lý",
                        tickangle=-15,
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title=selected_metric,
                        showgrid=True,
                        gridcolor="#e9ecef",
                        zeroline=True,
                        zerolinecolor="#dee2e6",
                    ),
                    legend=dict(
                        title="Mô hình",
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                    ),
                    bargap=0.2,
                    bargroupgap=0.05,
                    margin=dict(t=80, b=60, l=60, r=40),
                )

                # Hiển thị biểu đồ
                st.plotly_chart(fig, use_container_width=True)

                # ── Bảng số liệu đầy đủ (collapsible) ───────────────────────
                with st.expander("📋 Xem bảng số liệu chi tiết"):
                    display_cols = ["Model", "Variant_Label", selected_metric]
                    st.dataframe(
                        df_plot[display_cols]
                        .rename(columns={"Variant_Label": "Cấu hình tiền xử lý"})
                        .reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True,
                    )

                # ── Tự động sinh Insights ─────────────────────────────────────
                st.markdown("#### 💡 Nhận xét tự động")

                if selected_chart_lang == "EN" and selected_metric == "MAP":
                    st.info(
                        "**🔬 Nhận xét – Tiếng Anh / MAP:**\n\n"
                        "Cấu hình **Chuẩn hóa (Normalize)** mang lại cải thiện đáng kể về MAP so với "
                        "bản Gốc. Việc áp dụng stemming/lemmatization giúp gom nhóm các biến thể "
                        "hình thái của thuật ngữ y khoa phức tạp (vd: *\"carcinoma\"*, *\"carcinomas\"*, "
                        "*\"carcinomatous\"*) về cùng một dạng chuẩn, giúp mô hình truy xuất đúng tài "
                        "liệu liên quan hơn dù query và corpus dùng hình thức khác nhau của cùng một từ."
                    )
                elif selected_chart_lang == "VI" and selected_metric == "MAP":
                    st.warning(
                        "**⚠️ Nhận xét – Tiếng Việt / MAP:**\n\n"
                        "Cấu hình **Lọc Stopword** cho thấy xu hướng làm **giảm điểm MAP** so với "
                        "bản Gốc trong tập dữ liệu Tiếng Việt. Nguyên nhân có thể do danh sách "
                        "stopword tiếng Việt loại bỏ một số từ nối và trợ từ có vai trò pháp lý quan "
                        "trọng (vd: *\"của\"*, *\"về\"*, *\"theo\"*) – những từ này thực chất mang "
                        "ngữ nghĩa phân biệt quan trọng trong các văn bản hành chính, pháp luật, "
                        "khiến câu truy vấn sau lọc trở nên mơ hồ hơn."
                    )
                else:
                    # Insight mặc định: tìm cấu hình tốt nhất
                    try:
                        best_row = df_plot.loc[df_plot[selected_metric].idxmax()]
                        best_variant = best_row["Variant_Label"]
                        best_model   = best_row["Model"]
                        best_val     = best_row[selected_metric]
                        lang_note    = "Tiếng Anh (EN)" if selected_chart_lang == "EN" else "Tiếng Việt (VI)"
                        st.info(
                            f"**📌 Cấu hình tốt nhất – {lang_note} / {selected_metric}:**\n\n"
                            f"Mô hình **{best_model}** với pipeline **{best_variant}** đạt "
                            f"{selected_metric} cao nhất là **{best_val:.4f}**."
                        )
                    except Exception:
                        st.info("Chọn **MAP** để xem nhận xét chuyên sâu.")

        except Exception as e:
            st.error(
                f"❌ Đã xảy ra lỗi khi vẽ biểu đồ: `{e}`\n\n"
                "Vui lòng kiểm tra lại định dạng file `evaluation_results.csv`."
            )

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption(
    "📚 Đồ án: *Nghiên cứu ảnh hưởng của Tiền xử lý Văn bản đến kết quả Truy xuất (IR)* &nbsp;|&nbsp; "
    "Nhóm 8 &nbsp;|&nbsp; Streamlit Static Demo"
)

