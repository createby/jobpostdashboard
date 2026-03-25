from flask import Flask, request, jsonify, send_file, render_template
import openpyxl
import json
import os
import io
from generate_pdf import generate_company_pdf

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload_excel", methods=["POST"])
def upload_excel():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "파일 없음"}), 400
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    companies = []
    headers = None
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            headers = [str(c).strip() if c else "" for c in row]
            continue
        if not any(row):
            continue
        company = {}
        for j, val in enumerate(row):
            if j < len(headers):
                company[headers[j]] = str(val).strip() if val is not None else ""
        companies.append(company)
    return jsonify({"headers": headers, "companies": companies})

@app.route("/generate_pdf", methods=["POST"])
def generate_pdf_route():
    data = request.json
    filename = f"{data.get('부스번호', 'X')}_{data.get('기업명', 'company')}.pdf"
    output_path = os.path.join(OUTPUT_FOLDER, filename)

    # 채용계획 파싱 (문자열이면 JSON 파싱)
    if isinstance(data.get("채용계획"), str):
        try:
            data["채용계획"] = json.loads(data["채용계획"])
        except:
            data["채용계획"] = []

    generate_company_pdf(data, output_path)
    return send_file(output_path, as_attachment=True, download_name=filename)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
