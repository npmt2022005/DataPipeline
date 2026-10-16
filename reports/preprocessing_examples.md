# Preprocessing examples

Actual outputs of the five configurations. Empty strings are shown as "".

## vi sample 0

```json
{
  "original": "Sinh viên có thể học tập!!!",
  "stopword": "Sinh viên học tập!!!",
  "normalize": "sinh viên có thể học tập",
  "tokenize": "Sinh_viên có_thể học_tập ! ! !",
  "combined": "sinh_viên học_tập"
}
```

## vi sample 1

```json
{
  "original": "HỌC,tập!!!  123",
  "stopword": "HỌC,tập!!! 123",
  "normalize": "học tập 123",
  "tokenize": "HỌC , tập ! ! ! 123",
  "combined": "học_tập 123"
}
```

## vi sample 2

```json
{
  "original": "và là",
  "stopword": "",
  "normalize": "và là",
  "tokenize": "và là",
  "combined": ""
}
```

## vi sample 3

```json
{
  "original": "",
  "stopword": "",
  "normalize": "",
  "tokenize": "",
  "combined": ""
}
```

## vi sample 4

```json
{
  "original": "!!!",
  "stopword": "!!!",
  "normalize": "",
  "tokenize": "! ! !",
  "combined": ""
}
```

## vi sample 5

```json
{
  "original": "URL https://example.vn 😀",
  "stopword": "URL https://example.vn 😀",
  "normalize": "url https example vn",
  "tokenize": "URL https://example.vn 😀",
  "combined": "url https example vn"
}
```

## vi sample 6

```json
{
  "original": "ĐÂY   là VĂN BẢN.",
  "stopword": "VĂN .",
  "normalize": "đây là văn bản",
  "tokenize": "ĐÂY là VĂN_BẢN .",
  "combined": "văn_bản"
}
```

## vi sample 7

```json
{
  "original": "Người lao động được gia hạn trả nợ vay vốn để đi làm việc ở nước ngoài theo hợp đồng trong thời gian bao lâu?",
  "stopword": "lao động gia hạn nợ vay vốn đi hợp đồng ?",
  "normalize": "người lao động được gia hạn trả nợ vay vốn để đi làm việc ở nước ngoài theo hợp đồng trong thời gian bao lâu",
  "tokenize": "Người lao_động được gia_hạn trả nợ vay vốn để đi làm_việc ở nước_ngoài theo hợp_đồng trong thời_gian bao_lâu ?",
  "combined": "lao_động gia_hạn nợ vay vốn đi làm_việc nước_ngoài hợp_đồng"
}
```

## vi sample 8

```json
{
  "original": "Nghĩa vụ của hội viên Hiệp hội Công nghiệp ghi âm Việt Nam là gì?",
  "stopword": "Nghĩa vụ hội viên Hiệp hội Công nghiệp ghi âm Việt Nam ?",
  "normalize": "nghĩa vụ của hội viên hiệp hội công nghiệp ghi âm việt nam là gì",
  "tokenize": "Nghĩa_vụ của hội_viên Hiệp_hội Công_nghiệp ghi_âm Việt_Nam là gì ?",
  "combined": "nghĩa_vụ hội_viên hiệp_hội công_nghiệp ghi_âm việt_nam"
}
```

## en sample 0

```json
{
  "original": "THE theater and CAT!",
  "stopword": "theater CAT!",
  "normalize": "the theater and cat",
  "tokenize": "THE theater and CAT !",
  "combined": "theater cat"
}
```

## en sample 1

```json
{
  "original": "Students cannot study.",
  "stopword": "Students cannot study.",
  "normalize": "students cannot study",
  "tokenize": "Students can not study .",
  "combined": "students study"
}
```

## en sample 2

```json
{
  "original": "and the",
  "stopword": "",
  "normalize": "and the",
  "tokenize": "and the",
  "combined": ""
}
```

## en sample 3

```json
{
  "original": "",
  "stopword": "",
  "normalize": "",
  "tokenize": "",
  "combined": ""
}
```

## en sample 4

```json
{
  "original": "!!!",
  "stopword": "!!!",
  "normalize": "",
  "tokenize": "! ! !",
  "combined": ""
}
```

## en sample 5

```json
{
  "original": "URL https://example.org 😀 123",
  "stopword": "URL https://example.org 😀 123",
  "normalize": "url https example org 123",
  "tokenize": "URL https : //example.org 😀 123",
  "combined": "url https example org 123"
}
```

## en sample 6

```json
{
  "original": "Mixed   CASE, punctuation!!!",
  "stopword": "Mixed CASE, punctuation!!!",
  "normalize": "mixed case punctuation",
  "tokenize": "Mixed CASE , punctuation ! ! !",
  "combined": "mixed case punctuation"
}
```

## en sample 7

```json
{
  "original": "Do Cholesterol Statin Drugs Cause Breast Cancer?",
  "stopword": "Cholesterol Statin Drugs Cause Breast Cancer?",
  "normalize": "do cholesterol statin drugs cause breast cancer",
  "tokenize": "Do Cholesterol Statin Drugs Cause Breast Cancer ?",
  "combined": "cholesterol statin drugs cause breast cancer"
}
```

## en sample 8

```json
{
  "original": "Exploiting Autophagy to Live Longer",
  "stopword": "Exploiting Autophagy Live Longer",
  "normalize": "exploiting autophagy to live longer",
  "tokenize": "Exploiting Autophagy to Live Longer",
  "combined": "exploiting autophagy live longer"
}
```
