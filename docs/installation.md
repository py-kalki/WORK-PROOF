Installation
------------

Prerequisites:
- Python 3.9+
- Windows or Linux
- Optional for PDF: WeasyPrint or wkhtmltopdf (see packaging.md)

Steps:
1) Create venv and install:
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2) Initialize DB and run:
```bash
python -m workproof.main
```
3) Generate a report:
```bash
python -m workproof.report_generator --date today --out reports/today.html
```



