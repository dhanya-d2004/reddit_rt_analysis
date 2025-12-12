import logging
import torch
from transformers import pipeline
from utils import clean_text

logger = logging.getLogger(__name__)

class AIClassifier:
    def __init__(self, model_name="cross-encoder/nli-deberta-v3-small"):
        """
        Initialize the Zero-Shot Classification pipeline.
        Using cross-encoder/nli-deberta-v3-small as requested/planned.
        """
        self.device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Loading model {model_name} on device {'GPU' if self.device == 0 else 'CPU'}...")
        
        try:
            self.classifier = pipeline("zero-shot-classification", model=model_name, device=self.device)
            self.sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=self.device)
            self.candidate_labels = ["human", "ai"]
            logger.info("Models loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e

    def predict(self, text: str):
        """
        Predict whether the text is Human or AI generated.
        Returns a dictionary with 'label' and 'score'.
        """
        text = clean_text(text)
        if not text:
            return {'label': 'Unknown', 'score': 0.0}

        try:
            # Multi-class zero-shot classification
            result = self.classifier(text, self.candidate_labels)
            
            # Result contains 'labels' and 'scores' sorted by score descending
            top_label = result['labels'][0]
            top_score = result['scores'][0]
            
            
            # Sentiment Analysis
            sent_result = self.sentiment_analyzer(text)[0]
            sentiment_label = sent_result['label'] # POSITIVE or NEGATIVE
            sentiment_score = sent_result['score']

            # Map back to capitalized labels for UI
            label_map = {"human": "Human", "ai": "AI"}
            
            return {
                'label': label_map.get(top_label, top_label),
                'score': top_score,
                'sentiment': sentiment_label,
                'sentiment_score': sentiment_score
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {'label': 'Error', 'score': 0.0}

if __name__ == "__main__":
    # Simple test
    print("Loading model for test...")
    clf = AIClassifier()
    test_text = "As an AI language model, I cannot help with that."
    print(f"Test prediction for '{test_text}': {clf.predict(test_text)}")
