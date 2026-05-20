"""PhoBERT-based Clickbait Classifier"""
import torch
import logging
from typing import Dict, List, Tuple
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)


def _has_model_weights(model_dir: Path) -> bool:
    """Return True when a local Hugging Face model directory has weight files."""
    required_files = {
        "model.safetensors",
        "pytorch_model.bin",
        "tf_model.h5",
        "flax_model.msgpack",
    }
    if any((model_dir / filename).is_file() for filename in required_files):
        return True

    if any(model_dir.glob("model-*.safetensors")):
        return True
    if any(model_dir.glob("pytorch_model-*.bin")):
        return True
    if any(model_dir.glob("*.index.json")):
        return True

    return False


class PhoBERTClickbaitClassifier:
    """PhoBERT model for Vietnamese clickbait detection.
    
    Binary classification: clickbait (1) vs non-clickbait (0)
    """
    
    def __init__(self, model_name: str = "vinai/phobert-base", device: str = None):
        """Initialize PhoBERT model for clickbait classification.
        
        Args:
            model_name: HuggingFace model identifier or path to saved model
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"📱 Loading model: {model_name}")
        logger.info(f"📍 Device: {self.device}")
        model_source = model_name
        tokenizer_source = model_name

        local_model_path = Path(model_name)
        if local_model_path.exists() and local_model_path.is_dir() and not _has_model_weights(local_model_path):
            raise ValueError(f"Local model directory {model_name} has no weight files.")

        if not local_model_path.exists() and "/" not in model_name and "\\" not in model_name:
            # It might be a Hugging Face hub model identifier, let it pass
            pass
        elif not local_model_path.exists():
            # If it looks like a path but doesn't exist
            pass

        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_source)
        except Exception as tokenizer_error:
            logger.error(f"Failed to load tokenizer {tokenizer_source}: {tokenizer_error}")
            raise

        try:
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_source,
                num_labels=2
            )
        except Exception as model_error:
            logger.error(f"Failed to load model {model_source}: {model_error}")
            raise
        
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"✅ Model loaded successfully")
    
    def predict(self, text: str, return_probs: bool = False) -> Tuple[int, float]:
        """Predict clickbait label and confidence score.
        
        Args:
            text: Article title or headline
            return_probs: If True, return probabilities for both classes
            
        Returns:
            (label, confidence_score) where label=1 is clickbait, 0 is non-clickbait
            If return_probs=True: (label, {0: prob_non_clickbait, 1: prob_clickbait})
        """
        try:
            inputs = self.tokenizer(
                text,
                truncation=True,
                max_length=256,
                padding='max_length',
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=1)
                label = torch.argmax(probs, dim=1).item()
                confidence = probs[0][label].item()
                
                if return_probs:
                    prob_dict = {
                        0: probs[0][0].item(),
                        1: probs[0][1].item()
                    }
                    return label, prob_dict
                else:
                    return label, confidence
        except Exception as e:
            logger.error(f"Error predicting: {e}")
            return 0, 0.5
    
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """Predict clickbait labels for multiple texts.
        
        Args:
            texts: List of article titles/headlines
            
        Returns:
            List of dicts with 'label' and 'confidence' keys
        """
        results = []
        for text in texts:
            label, confidence = self.predict(text)
            results.append({
                'label': label,
                'confidence': confidence,
                'label_name': 'clickbait' if label == 1 else 'non-clickbait'
            })
        return results
    
    def predict_batch_with_text(self, texts: List[str]) -> List[Dict]:
        """Predict with original text included.
        
        Args:
            texts: List of texts to classify
            
        Returns:
            List of dicts with text, label, confidence, and label_name
        """
        results = []
        for text in texts:
            label, confidence = self.predict(text)
            results.append({
                'text': text,
                'label': label,
                'confidence': confidence,
                'label_name': 'clickbait' if label == 1 else 'non-clickbait'
            })
        return results
    
    def save(self, save_path: str) -> None:
        """Save fine-tuned model and tokenizer.
        
        Args:
            save_path: Directory to save model
        """
        Path(save_path).mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)
        logger.info(f"✅ Model saved to {save_path}")
    
    def load(self, model_path: str) -> None:
        """Load fine-tuned model and tokenizer.
        
        Args:
            model_path: Path to saved model directory
        """
        logger.info(f"Loading model from {model_path}")
        model_source = model_path
        tokenizer_source = model_path
        local_model_path = Path(model_path)

        if local_model_path.exists() and local_model_path.is_dir() and not _has_model_weights(local_model_path):
            raise ValueError(f"Local model directory {model_path} has no weight files.")

        self.model = AutoModelForSequenceClassification.from_pretrained(model_source)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_source)
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"✅ Model loaded from {model_path}")
