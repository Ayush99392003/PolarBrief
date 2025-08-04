import os
import json
from typing import List, Dict
from datetime import datetime
from pdf_extraction import pdf_extraction
from chunking import chunk_lines
from processing import processing
from llm_analysis import llm_analysis
import pytesseract
from output_files import output_files
class DocumentProcessor:
    def __init__(self, poppler_path=None, tesseract_path=None):
        self.POLARBRIEF_VERSION = "PolarBrief v1.0"
        if poppler_path:
            self.poppler_path = poppler_path
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    def process_document(self, pdf_path: str, poppler_path: str, tesseract_path: str , groq_api_key:str) -> Dict:
        try:      
            extracted_lines = pdf_extraction(pdf_path)
            # Step 2: Chunk lines into paragraphs
            chunks = chunk_lines(extracted_lines)
            print("chunked")
            # Step 3: Preprocess text
            processed_chunks = processing(chunks)
            print("processed")
            # Step 4: Analyze with LLM
            final_output = llm_analysis(processed_chunks,groq_api_key )
            print("analysed")          
            # Step 5: Sort and prepare outputs
            final_output_sorted = sorted(
                final_output, 
                key=lambda x: x["final_score"], 
                reverse=True
            )
            # Step 6: Build top/balanced lists
            final_pro = [item for item in final_output_sorted if item["polarity"].lower() == "pro"][:5]
            final_con = [item for item in final_output_sorted if item["polarity"].lower() == "con"][:5]
            balanced_args = final_con + final_pro
            return {
                "full_analysis": final_output,
                "balanced_arguments": balanced_args,
                "timestamp": datetime.now().isoformat(),
                "version": self.POLARBRIEF_VERSION
            }
        except Exception as e:
            print(f"Processing error: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "version": self.POLARBRIEF_VERSION
            }
   