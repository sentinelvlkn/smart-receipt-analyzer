# Smart Receipt Analyzer

Python application for processing PDF invoices. It extracts invoice data using OCR and an LLM, stores the result in a PostgreSQL database and generates a PDF report with categorization and summary.

The app is containerized with Docker Compose and utilizes FastAPI.

## Features
- Supports digital and scanned PDF invoices
- Extracts embedded text from digital PDFs with PyMuPDF
- Extracts text from scanned invoices using Tesseract OCR
- Supports English and Bulgarian OCR
- Uses LLM for:
    - structured invoice extraction
    - OCR description correction
    - expense categorization
    - expense summary generation
- Validates extracted data with Pydantic
- Stores receipts and receipt items in PostgreSQL
- Stores both the raw response and parsed LLM result
- Generates PDF reports with:
    - invoice metadata
    - categorized receipt items
    - items total by category
    - invoice grand total
- Fully containerized with Docker Compose

## Tech stack

- Python 3.12
- Docker / Docker Compose
- PostgreSQL
- Pydantic
- PyMuPDF
- Tesseract OCR with pytesseract
- OpenAI Python SDK
- FastAPI
- pytest
- SQLAlchemy
- Psycopg
- ReportLab

## Architecture



## Setup

### 1. Clone the repo

```bash
git clone https://github.com/sentinelvlkn/smart-receipt-analyzer.git
cd smart-receipt-analyzer
```

### 2. Create .env
- Copy .env.example to .env

```bash
cp .env.example .env
```

- On Windows PowerShell

```bash
Copy-Item .env.example .env
```

- Enter your OpenAI API key

```bash
OPENAI_API_KEY= ...
OPENAI_MODEL=gpt-5-mini
```

### 3. Start the application

```bash
docker compose up --build
```
The application starts together with PostgreSQL

- API
```bash
http://localhost:8000
```

- Swagger documentation
```bash
http://localhost:8000/docs
```

- Health endpoint
```bash
http://localhost:8000/health
```

### 4. Process an invoice

```bash
http://localhost:8000/docs
POST /receipts
```

Upload a PDF. The application will:
1. detect whether the PDF contains embedded text and if so - extract the text
2. if it is scanned PDF and contains no embedded text, then OCR will be called
3. send the extracted information to the LLM
4. validate the structured result
5. persist the receipt and items in PostgreSQL
6. generate PDF report in reports/
7. return the structured receipt as JSON

### 5. List receipts

```bash
GET /receipts
```

### 6. Get a receipt

```bash
GET /receipts/{receipt_id}
```

### 7. Health check

```bash
GET /health
```

### OCR extraction approach

The pipeline can handle both digital and scanned files.

For digital PDFs, embedded text is extracted directly with PyMuPDF.

For scanned PDFs, pages are rendered at 300 DPI and processed with Tesseract using Bulgarian and English language data.

Word coordinates are retained and used to reconstruct text regions so as to preserve information from invoices with different layouts where fields and columns are positioned horizontally.

### LLM Processing 

The LLM receives the extracted document representation and returns structured invoice data.

The extraction schema includes:

* invoice number
* invoice date
* issuer name and identifier
* receiver name and identifier
* line items
* corrected item descriptions
* categories
* quantity
* unit price
* amount
* total amount
* currency
* expense summary

Missing information is represented as null.

The raw LLM response and the parsed structured result are both persisted for
auditability and debugging.

Financial values are converted to Decimal in the validated domain model.

### Database

PostgreSQL stores normalized receipt metadata and individual receipt items.

The main tables are receipts and receipt_items.

Receipt records also contain:

* extraction method
* LLM model
* raw LLM response
* parsed LLM result
* original source filename
* creation timestamp

### PDF reports

After a receipt is successfully persisted, a PDF report is generated in:

```bash
reports/
```

Reports contain:

* invoice number and date
* vendor and receiver information
* categorized line items
* quantities and prices
* item totals grouped by category
* invoice grand total
* LLM-generated expense summary

### Tests 

Run the complete test suite locally with:

```bash
python -m pytest -v
```

Tests cover:

* domain model validation
* PDF text detection
* OCR layout reconstruction
* document extraction
* LLM-to-domain mapping
* receipt processing orchestration
* repository persistence
* REST API endpoints
* PDF report generation

### Sample invoices

Sample PDFs are available under:

```bash
samples/digital_invoices
samples/scanned_invoices
```

### Configuration

See .env.example

Important variables:

```bash
OPENAI_API_KEY= ...
OPENAI_MODEL=gpt-5-mini

POSTGRES_DB=receipt_analyzer
POSTGRES_USER=receipt_user
POSTGRES_PASSWORD= ...
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### Limitations

* OCR quality depends on scan resolution and document quality
* Arbitrary invoice layouts are challenging 
* LLM output may vary between requests
* Not production-ready project - basic secrets management, no strict upload limits, no authentication