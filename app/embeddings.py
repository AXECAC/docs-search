from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# Глобальная переменная для модели (загружается один раз при старте)
_model = None

def load_model():
    """Загружает модель эмбеддингов (ленивая загрузка)"""
    global _model
    if _model is None:
        logger.info("Loading embedding model: cointegrated/rubert-tiny2")
        _model = SentenceTransformer('cointegrated/rubert-tiny2')
        logger.info("Model loaded successfully")
    return _model

def get_embedding(text: str) -> list[float]:
    """
    Возвращает вектор эмбеддинга для текста.
    Размерность: 312.
    """
    model = load_model()
    # convert_to_numpy=True возвращает numpy array, .tolist() превращает в list
    embedding = model.encode(text, convert_to_numpy=True).tolist()
    return embedding

def get_embedding_dimension() -> int:
    """Возвращает размерность эмбеддинга (312 для rubert-tiny2)"""
    return 312