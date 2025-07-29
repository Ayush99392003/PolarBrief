import os
import json
import re
from typing import List, Dict
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import pdfplumber
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize


nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')


# Constants
POLARBRIEF_VERSION = "PolarBrief v1.0"

class ArgumentAnalysis(BaseModel):
    heading: str
    contains_argument: str
    summary: str
    polarity: str = Field(default="N/A")
    score: float = Field(ge=0, le=100)

class DocumentProcessor:
    def __init__(self):
        self.llm = ChatGroq(
            model_name="llama3-8b-8192",
            temperature=0,
        )
        
    def clean_text(self, text: str) -> str:
        text = re.sub(r"[•·●♦▪•∙]", "", text)
        text = re.sub(r"[^\w\s,.:;()\"'-]", "", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()

    def is_noisy(self, text: str, threshold: float = 0.6) -> bool:
        if not text:
            return True
        non_alpha = sum(1 for c in text if not c.isalnum())
        return (non_alpha / len(text)) > threshold

    def has_repeated_characters(self, text: str, repeat_threshold: int = 4) -> bool:
        return bool(re.search(r'(.)\1{' + str(repeat_threshold) + ',}', text))

    def extract_text_with_fallback(self, pdf_path: str, poppler_path: str) -> List[Dict]:
        final_output = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages, start=1):
                    page_line_no = 1
                    text = page.extract_text()
                    lines = text.split("\n") if text else []

                    if lines and sum(len(l.strip()) for l in lines) > 20:
                        for line in lines:
                            cleaned = line.strip()
                            if cleaned:
                                final_output.append({
                                    "text": cleaned,
                                    "page_no": f"[p{page_num} {page_line_no}]",
                                    "method": "pdfplumber"
                                })
                                page_line_no += 1
                        continue
                    images = convert_from_path(
                        pdf_path, dpi=300, first_page=page_num, 
                        last_page=page_num, poppler_path=poppler_path
                    )
                    img = images[0]
                    gray = img.convert("L")
                    bw = gray.point(lambda x: 0 if x < 180 else 255, '1')

                    ocr_text = pytesseract.image_to_string(bw, lang='eng')
                    lines = ocr_text.strip().split("\n")
                    line_no = 1

                    for line in lines:
                        cleaned_line = self.clean_text(line)
                        if (cleaned_line and not self.is_noisy(cleaned_line) and 
                            not self.has_repeated_characters(cleaned_line)):
                            final_output.append({
                                "text": cleaned_line,
                                "page_no": f"[p{page_num} {line_no}]",
                                "method": "ocr"
                            })
                            line_no += 1

        except Exception as e:
            print(f"[ERROR] Failed during PDF processing: {e}")

        return final_output

    def count_tokens_simple(self, text: str) -> int:
        return len(text.split())

    def chunk_lines_simple_tokenizer(self, lines: List[Dict], max_tokens: int = 250) -> List[Dict]:
        chunks = []
        current_lines = []
        current_tokens = 0
        citation_line = None
        citation_page = None

        for line in lines:
            text = line["text"].strip()
            tokens = self.count_tokens_simple(text)

            if current_tokens + tokens > max_tokens and current_lines:
                chunk_text = "\n".join([l["text"] for l in current_lines])
                chunks.append({
                    "page": citation_page,
                    "citation": citation_line,
                    "text": chunk_text
                })
                current_lines = []
                current_tokens = 0
                citation_line = None
                citation_page = None

            if not current_lines and text:
                citation_line = text
                citation_page = line["page_no"]

            current_lines.append(line)
            current_tokens += tokens

        if current_lines:
            chunk_text = "\n".join([l["text"] for l in current_lines])
            chunks.append({
                "page": citation_page,
                "citation": citation_line,
                "text": chunk_text
            })

        return chunks

        # Initialize tools
        stop_words = set(stopwords.words('english'))
        lemmatizer = WordNetLemmatizer()
        stemmer = PorterStemmer()

        def clean_ocr_artifacts(text: str) -> str:
            if not text:
                return ""
            text = re.sub(r'[\.\-]{3,}', ' ', text)
            text = re.sub(r'[a-zA-Z0-9]{3,}[a-zA-Z0-9\s]{0,}$', '', text)
            text = re.sub(r'([a-zA-Z0-9])\1{3,}', '', text)
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



    def get_argument_analysis(self, text: str) -> ArgumentAnalysis:
        system_prompt = """You are a legal assistant AI.

Given the paragraph below from a legal brief:

1. Please summarize the paragraph <<<
    Your summary must:
            1. Do not hallucinate Your summary must be based **only** on paragraph. Do not add, infer, or interpret anything beyond what is explicitly stated.
            2. Clearly and accurately capture the **main legal points or facts** in the text in points and then summarize those points in paragraph.
            3. the summary paragraph must be of >75 words .
            4. After writing the summary, **verify** that it fully aligns with the original text and does not introduce errors or hallucinations.>>>
            
2. Give a appropriate heading that the text is about.
3. Does it contain a legal argument? (yes/no)
4. if yes , Classify it as Pro (supports Plaintiffs) or Con (supports Defendants) , else "N/A"
5. Score the argument on a scale of 0 - 100 based on weight, clarity, relevance, and quality.
6. Do not fabricate content; if uncertain, answer contains_argument: "no"

Respond ONLY in Valid JSON , no prose:
{
  "heading" : "..." ,
  "contains_argument": "...",
  "summary": "...",
  "polarity": "Pro/Con",
  "score": <float 0-100>
}"""
        prompt = f'<<<Paragraph:\n"""{text}""">>>'

        response = self.llm([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ])
        
        try:
            match = re.search(r"\{[\s\S]+?\}", response.content.strip())
            if match:
                parsed = json.loads(match.group(0))
                return ArgumentAnalysis(**parsed)
        except (ValidationError, json.JSONDecodeError) as e:
            print("Error parsing LLM JSON:", e)
        
        return ArgumentAnalysis(
            heading="",
            contains_argument="error",
            summary=text,
            polarity="N/A",
            score=0
        )

    def normalize(self, arr: List[float]):
        arr = np.array(arr)
        return (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)

    def process_document(self, pdf_path: str, poppler_path: str, tesseract_path: str):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Step 1: Extract text
        extracted_text = self.extract_text_with_fallback(pdf_path, poppler_path)
        
        # Step 2: Chunk text
        chunks = self.chunk_lines_simple_tokenizer(extracted_text)
        
        # Step 3: Analyze arguments
        final_output = []
        texts = []
        llm_scores = []

        for chunk in chunks:
            parsed = self.get_argument_analysis(chunk["text"])
            
            llm_scores.append(parsed.score)
            texts.append(chunk["text"])

            def truncate_to_75_words(text):
                words = text.split()
                return ' '.join(words[:75]) + ('...' if len(words) > 75 else '')

            final_output.append({
                "page": chunk["page"],
                "citation": chunk["citation"],
                "text": chunk["text"],
                "heading": parsed.heading,
                "contains_argument": parsed.contains_argument,
                "summary": truncate_to_75_words(parsed.summary),
                "polarity": parsed.polarity,
                "source": POLARBRIEF_VERSION,
                "timestamp": datetime.now().isoformat()
            })

        # TF-IDF Centrality
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)
        centrality_scores = cosine_similarity(tfidf_matrix, tfidf_matrix).mean(axis=1)

        # Combine Scores
        llm_scores_norm = self.normalize(llm_scores)
        centrality_scores_norm = self.normalize(centrality_scores)
        combined_scores = 0.6 * llm_scores_norm + 0.4 * centrality_scores_norm

        # Add final_score
        for i, item in enumerate(final_output):
            item["final_score"] = round(combined_scores[i] * 100, 2)

        # Sort by final_score
        final_output_sorted = sorted(final_output, key=lambda x: x["final_score"], reverse=True)
        final_output_sorted = [item for item in final_output_sorted if item["contains_argument"].lower() == "yes"]
        
        # Take top 10
        top_10 = final_output_sorted[:10]
        
        return {
            "full_analysis": final_output,
            "top_arguments": top_10
        }
