import pdfplumber
import json
from typing import List, Dict
from openai import OpenAI
import os
from fpdf import FPDF
from io import BytesIO
from unidecode import unidecode 
import zipfile

os.environ["GROQ_API_KEY"] = "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"  

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

class UnicodePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_font( size=12)
        self.set_auto_page_break(auto=True, margin=15)

def create_pdf_from_dict(data: List[Dict], title: str = "Document") -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=unidecode(title), ln=True, align='C')
    pdf.ln(10)

    for i, item in enumerate(data, 1):
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 10, txt=f"{i}.")
        pdf.set_font("Arial", size=12)

        for key, value in item.items():
            if isinstance(value, str) and value.strip():
                pdf.multi_cell(0, 10, txt=unidecode(value.strip()))
                pdf.ln(2)

        pdf.ln(5)

    output = BytesIO()
    output.write(pdf.output(dest='S').encode('latin1'))
    output.seek(0)
    return output

def create_pdf_from_top10(top_10_dict: Dict) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_auto_page_break(auto=True, margin=15)

    # Pro Arguments
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Top 5 Pro Arguments", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    for i, arg in enumerate(top_10_dict.get("top_5_pro", []), 1):
        summary = arg.get("summary", "").strip()
        if summary:
            pdf.multi_cell(0, 10, txt=f"{i}. {unidecode(summary)}")
            pdf.ln(5)

    # Con Arguments
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Top 5 Con Arguments", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    for i, arg in enumerate(top_10_dict.get("top_5_con", []), 1):
        summary = arg.get("summary", "").strip()
        if summary:
            pdf.multi_cell(0, 10, txt=f"{i}. {unidecode(summary)}")
            pdf.ln(5)

    output = BytesIO()
    output.write(pdf.output(dest='S').encode('latin1'))
    output.seek(0)
    return output


def extract_pdf_lines(uploaded_file) -> List[Dict]:
    output = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line_num, line in enumerate(lines, start=1):
                cleaned_line = line.strip()
                if cleaned_line:
                    output.append({
                        "page": page_num,
                        "line": line_num,
                        "text": cleaned_line
                    })
    return output

def create_zip_archive(file_dict: dict) -> BytesIO:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in file_dict.items():
            if isinstance(content, str):
                content = content.encode("utf-8")
            zip_file.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer


def chunk_lines_into_paragraphs(lines: List[Dict], max_gap: int = 1) -> List[Dict]:
    paragraphs = []
    current_para = {"page": None, "start_line": None, "end_line": None, "text": []}
    for i, line in enumerate(lines):
        content = line["text"].strip()
        if not content:
            continue
        if current_para["text"] == []:
            current_para["page"] = line["page"]
            current_para["start_line"] = line["line"]
        current_para["text"].append(content)
        current_para["end_line"] = line["line"]
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            same_page = next_line["page"] == line["page"]
            line_gap = next_line["line"] - line["line"]
            if not same_page or line_gap > max_gap:
                paragraphs.append({
                    "page": current_para["page"],
                    "start_line": current_para["start_line"],
                    "end_line": current_para["end_line"],
                    "text": " ".join(current_para["text"])
                })
                current_para = {"page": None, "start_line": None, "end_line": None, "text": []}
    if current_para["text"]:
        paragraphs.append({
            "page": current_para["page"],
            "start_line": current_para["start_line"],
            "end_line": current_para["end_line"],
            "text": " ".join(current_para["text"])
        })
    return paragraphs


def get_argument_analysis(paragraph: str):
    prompt = f"""
You are a legal assistant AI.

Given the paragraph below from a legal brief:
1. Does it contain a legal argument? (yes/no)
2. If yes, summarize it in ≤75 words.
3. Classify it as Pro (supports Plaintiffs) or Con (supports Defendants).
4. Score the argument on a scale of 0 - 100 based on weight ,clarity, relevance, and quality etc and other aspects .

Respond in JSON like this:
{{
  "contains_argument": "...",
  "summary": "...",
  "polarity": "Pro/Con",
  "start line": "..",
  "end line":"...",
  "score":"..."
}}

Paragraph:
\"\"\"{paragraph}\"\"\"
"""
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a legal assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=512
    )
    return response.choices[0].message.content.strip()


def parse_argument_results(paragraphs: List[Dict]) -> List[Dict]:
    results = []
    for para in paragraphs:
        raw = get_argument_analysis(para['text'])
        try:
            json_part = raw[raw.index("{"):raw.rindex("}")+1]
            data = json.loads(json_part)
            if data.get("contains_argument", "").lower() == "yes":
                results.append({
                    "summary": data.get("summary", ""),
                    "polarity": data.get("polarity", ""),
                    "score": float(data.get("score", 0)),
                    "start_line": int(data.get("start line", 0)),
                    "end_line": int(data.get("end line", 0)),
                    "page": para["page"]
                })
        except Exception as e:
            continue
    return results
