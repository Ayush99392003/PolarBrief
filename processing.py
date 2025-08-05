import json
import re
import nltk
from typing import List, Dict
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize
def downloads_nltk():
    nltk.download('punkt')
    nltk.download('punkt_tab')
    nltk.download('stopwords')
    nltk.download('wordnet')
def processing(chunks: List[Dict]) -> List[Dict]:
    downloads_nltk()
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()
    def clean_ocr_artifacts(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'[\.\-]{3,}', ' ', text)
        text = re.sub(r'[a-zA-Z0-9]{1,}[a-zA-Z0-9\s]{0,}$', '', text)
        text = re.sub(r'([a-zA-Z0-9]){15,}', '', text)
        text = re.sub(r'\s{2,}', ' ', text).strip()
        return text
    def preprocess_text(text: str) -> str:
        text = clean_ocr_artifacts(text)
        text = text.lower()
        text = re.sub(r'[^a-z\s]', ' ', text) 
        tokens = word_tokenize(text)
        tokens = [word for word in tokens if word not in stop_words]
        tokens = [stemmer.stem(lemmatizer.lemmatize(word)) for word in tokens]
        return ' '.join(tokens)
    for entry in chunks:
        if "text" in entry:  
            entry["text"] = preprocess_text(entry["text"])

    return chunks
