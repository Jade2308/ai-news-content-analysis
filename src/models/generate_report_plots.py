import json
import matplotlib.pyplot as plt
from pathlib import Path

def generate_plots(history_path, output_dir):
    # Load data
    with open(history_path, 'r') as f:
        history = json.load(f)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    epochs = range(1, len(history['train_loss']) + 1)
    
    # 1. Plot Training & Validation Loss
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, history['train_loss'], 'b-o', label='Training Loss')
    plt.plot(epochs, history['val_loss'], 'r-o', label='Validation Loss')
    plt.title('Training and Validation Loss', fontsize=14, fontweight='bold')
    plt.xlabel('Epochs', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(output_path / 'loss_chart.png', dpi=300, bbox_inches='tight')
    print(f"✅ Đã lưu biểu đồ Loss tại: {output_path / 'loss_chart.png'}")
    
    # 2. Plot Metrics (F1, Precision, Recall)
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, history['val_f1'], 'g-s', label='F1-Score')
    plt.plot(epochs, history['val_precision'], 'c-^', label='Precision')
    plt.plot(epochs, history['val_recall'], 'm-d', label='Recall')
    plt.title('Validation Metrics over Epochs', fontsize=14, fontweight='bold')
    plt.xlabel('Epochs', fontsize=12)
    plt.ylabel('Score', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(output_path / 'metrics_chart.png', dpi=300, bbox_inches='tight')
    print(f"✅ Đã lưu biểu đồ Metrics tại: {output_path / 'metrics_chart.png'}")

if __name__ == "__main__":
    # Đường dẫn file trên máy bạn
    history_file = "models/phobert_clickbait/training_history.json"
    save_dir = "results/evaluation_results"
    
    try:
        generate_plots(history_file, save_dir)
        print("\n🚀 Hoàn tất! Bạn có thể lấy các file ảnh trong thư mục results/evaluation_results để dán vào báo cáo.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print("Đảm bảo bạn đã chạy 'pip install matplotlib' trước khi chạy script này.")
