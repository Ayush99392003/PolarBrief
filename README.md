
# 📚 PolarBrief AI - Legal Argument Analyzer

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Ayush99392003/PolarBrief
cd polarbrief-analyzer
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required Python packages include:
- `streamlit`
- `pdfplumber`
- `pytesseract`
- `fpdf`
- `scikit-learn`
- `pdf2image`
- `langchain`
- `langchain_groq`
- `openai`

### 🔐 3. Set Up Environment Variables (Windows CMD)

Before running the app, set your Groq API key in .env file:

```
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Install Tesseract & Poppler

- **Windows:**
  - Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
  - Install [Poppler for Windows](http://blog.alivate.com.au/poppler-windows/)

- **Linux/macOS:**

```bash
sudo apt install tesseract-ocr poppler-utils
```

Update `tesseract_path` and `poppler_path` accordingly in the .env file.

---

## 🧪 Run the App

```bash
streamlit run app.py
```

---


**PolarBrief AI** is a Streamlit-based web application that allows users to upload legal PDF documents and uses advanced AI (Groq's LLaMA 3 via LangChain) to:

- Extract and summarize legal arguments.
- Detect polarity (Pro/Con).
- Score arguments based on relevance, clarity, and weight.
- Provide downloadable results in JSON and PDF format.
- Visualize top arguments and citations directly in the UI.

---

## 🚀 Features

- 📄 Upload any legal PDF document.
- 🔍 Hybrid OCR (Tesseract) and native text extraction (pdfplumber).
- 🧠 AI-powered argument detection, heading generation, and summarization.
- ⚖️ Classify arguments as *Pro (Plaintiff)* or *Con (Defendant)*.
- 📈 Weighted scoring using LLM + TF-IDF centrality.
- 📥 Download ZIP bundle containing:
  - Ranked argument JSON
  - Top 10 arguments JSON
  - Minimal citation info
  - PDF reports



## 📁 Output Files

| File | Description |
|------|-------------|
| `all_arguments.json` | Full list of analyzed paragraphs |
| `top_10.json` | Top 10 scored legal arguments |
| `index.json` | Page, citation, and heading info only |
| `all_arguments.pdf` | Full PDF report |
| `index.pdf` | Index |
| `Docs.zip` | All above in a single ZIP |

---

## 🧠 AI Model & Prompting

- Uses `llama3-8b-8192` via `LangChain` and `ChatGroq`.
- Prompts the LLM to:
  - Summarize in 75+ words without hallucination.
  - Generate a legal heading.
  - Classify polarity (Pro/Con).
  - Score the argument 0–100.

---
