import os
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def compare_models(results_dirs, output_path='model_comparison.png'):
    models = []
    f1_scores = []
    precisions = []
    recalls = []
    roc_aucs = []

    for dir_path in results_dirs:
        json_path = Path(dir_path) / 'evaluation_results.json'
        if not json_path.exists():
            print(f"File not found: {json_path}")
            continue

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Tên mô hình (lấy từ tên thư mục)
            model_name = Path(dir_path).name
            models.append(model_name)
            
            # Lấy metrics
            f1_scores.append(data['weighted_metrics']['f1'])
            precisions.append(data['weighted_metrics']['precision'])
            recalls.append(data['weighted_metrics']['recall'])
            
            roc_auc = data['other_metrics'].get('roc_auc')
            roc_aucs.append(roc_auc if roc_auc is not None else 0.0)

    if not models:
        print("No data to plot.")
        return

    # Vẽ biểu đồ
    x = np.arange(len(models))
    width = 0.2

    fig, ax = plt.subplots(figsize=(10, 6))
    
    rects1 = ax.bar(x - width*1.5, precisions, width, label='Precision')
    rects2 = ax.bar(x - width*0.5, recalls, width, label='Recall')
    rects3 = ax.bar(x + width*0.5, f1_scores, width, label='F1-Score')
    rects4 = ax.bar(x + width*1.5, roc_aucs, width, label='ROC-AUC')

    ax.set_ylabel('Scores')
    ax.set_title('So sánh hiệu suất giữa các mô hình')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend(loc='lower right')
    ax.set_ylim(0, 1.1)

    # Hiển thị số trên đầu cột
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.4f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8)

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)
    autolabel(rects4)

    fig.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Saved comparison plot to {output_path}")

if __name__ == '__main__':
    dirs_to_check = [
        'results/evaluation/phobert',
        'results/evaluation/visobert',
        'results/evaluation/xlm_roberta'
    ]
    compare_models(dirs_to_check, 'results/evaluation/model_comparison.png')
