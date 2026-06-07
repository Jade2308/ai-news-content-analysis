import json
from pathlib import Path

import matplotlib.pyplot as plt


def generate_plots(history_path, output_dir):
    with open(history_path, 'r') as f:
        history = json.load(f)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    epochs = range(1, len(history['train_loss']) + 1)

    plt.figure(figsize=(10, 6))
    plt.plot(epochs, history['train_loss'], 'b-o', label='Training Loss')
    plt.plot(epochs, history['val_loss'], 'r-o', label='Validation Loss')
    plt.title('Training and Validation Loss', fontsize=14, fontweight='bold')
    plt.xlabel('Epochs', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(output_path / 'loss_chart.png', dpi=300, bbox_inches='tight')
    print(f"Saved loss chart to: {output_path / 'loss_chart.png'}")

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
    print(f"Saved metrics chart to: {output_path / 'metrics_chart.png'}")


if __name__ == "__main__":
    history_file = "results/models/phobert_clickbait/training_history.json"
    save_dir = "results/evaluation"

    try:
        generate_plots(history_file, save_dir)
        print("\nDone. Use the generated images from results/evaluation in your report.")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure matplotlib is installed before running this script.")
