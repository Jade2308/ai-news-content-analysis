# Phương án bổ sung XLM-RoBERTa và ViSoBERT để so sánh với PhoBERT

Để so sánh độ chính xác của 3 mô hình ngôn ngữ (**PhoBERT**, **XLM-RoBERTa**, **ViSoBERT**) trong bài toán phân loại Clickbait, cấu trúc source code hiện tại của bạn đã sử dụng các thư viện từ Hugging Face (`AutoTokenizer`, `AutoModelForSequenceClassification`). Điều này rất thuận lợi vì chúng ta chỉ cần tinh chỉnh một số tham số và luồng chạy thay vì phải viết lại kiến trúc model từ đầu.

Dưới đây là phương án chi tiết từng bước để thực hiện:

## Bước 1: Cập nhật script huấn luyện (`src/models/train_clickbait.py`)

Hiện tại, biến `model_name = "vinai/phobert-base"` đang được hardcode trong hàm `train_phobert`. Chúng ta cần biến nó thành một tham số truyền vào (argument).

**Thay đổi cần thiết:**
1. Thêm tham số `--model-name` vào `argparse`.
2. Thay đổi tên thư mục output mặc định sao cho linh hoạt theo tên mô hình (ví dụ: `models/phobert_clickbait`, `models/visobert_clickbait`, `models/xlm_roberta_clickbait`).

```python
# Trong src/models/train_clickbait.py
def train_model(
    csv_path: str,
    model_name: str = "vinai/phobert-base", # Thêm tham số này
    output_dir: str = None,
    # ... các tham số khác
):
    if output_dir is None:
        # Tự động tạo tên thư mục dựa trên model_name
        model_short_name = model_name.split('/')[-1]
        output_dir = f'models/{model_short_name}_clickbait'
        
    # Thay thế model_name = "vinai/phobert-base" bằng biến model_name được truyền vào
```

## Bước 2: Cập nhật class dự đoán (`src/models/phobert_classifier.py`)

Class `PhoBERTClickbaitClassifier` có tham số `model_name` nhưng lại sử dụng `FALLBACK_MODEL_NAME = "vinai/phobert-base"`. Nếu bạn tải một model khác mà thiếu file weight tạm thời, nó có thể tự động fallback về PhoBERT và gây nhầm lẫn.

**Thay đổi cần thiết:**
1. Đổi tên file và class (tuỳ chọn) thành `ClickbaitClassifier` cho tổng quát.
2. Xóa logic `FALLBACK_MODEL_NAME` để đảm bảo khi load model nào thì bắt buộc phải chạy đúng model đó (raise Error nếu lỗi thay vì fallback im lặng).

## Bước 3: Huấn luyện 3 mô hình riêng biệt

Sau khi cập nhật script ở Bước 1, bạn sẽ có thể khởi chạy huấn luyện cho từng mô hình qua terminal (sử dụng môi trường conda hiện tại).

**1. Huấn luyện PhoBERT:**
```bash
python src/models/train_clickbait.py --model-name "vinai/phobert-base" --output-dir "models/phobert_clickbait"
```

**2. Huấn luyện ViSoBERT:**
```bash
python src/models/train_clickbait.py --model-name "uitnlp/visobert" --output-dir "models/visobert_clickbait"
```

**3. Huấn luyện XLM-RoBERTa:**
```bash
python src/models/train_clickbait.py --model-name "xlm-roberta-base" --output-dir "models/xlm_roberta_clickbait"
```

## Bước 4: Đánh giá và lưu kết quả (`src/models/evaluate.py`)

Hiện tại script đánh giá sẽ lưu vào thư mục `evaluation_results`. Bạn cần đánh giá từng mô hình và lưu vào các thư mục riêng rẽ để tiện so sánh.

**Chạy đánh giá:**
```bash
python src/models/evaluate.py --model-path "models/phobert_clickbait" --output-dir "evaluation_results/phobert"
python src/models/evaluate.py --model-path "models/visobert_clickbait" --output-dir "evaluation_results/visobert"
python src/models/evaluate.py --model-path "models/xlm_roberta_clickbait" --output-dir "evaluation_results/xlm_roberta"
```

## Bước 5: Viết script so sánh (`src/models/compare_models.py`)

Tạo một script mới chuyên dùng để đọc 3 file `evaluation_results.json` từ 3 thư mục trên.

Script này sẽ:
1. Trích xuất các metric: `F1-score` (weighted), `Precision`, `Recall`, và `ROC-AUC`.
2. Dùng `matplotlib` hoặc `seaborn` để vẽ biểu đồ cột (Bar Chart) gộp, hiển thị trực quan các mô hình đứng cạnh nhau.
3. Xuất một file ảnh `model_comparison.png` để bạn có thể chèn trực tiếp vào báo cáo đồ án.
