from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd 
import openpyxl
from bulk import *  # Ensure this file exists and is correctly defined
from single import *  # Ensure this file exists and is correctly defined

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file1 = request.files.get('bulk_transactions')
        file2 = request.files.get('single_transactions')

        if file1 and file1.filename.endswith('.csv'):
            df1 = pd.read_csv(file1)
            results1 = your_ml_function1(df1)  # Replace with your actual function
            return jsonify(results1)
        elif file2 and file2.filename.endswith('.csv'):
            df2 = pd.read_csv(file2)
            results2 = your_ml_function2(df2)  # Replace with your actual function
            return jsonify(results2)
        else:
            return "Invalid file format. Please upload CSV files named 'Bulk Transactions' or 'Single Transactions'."
    return render_template('index.html')

@app.route('/download_results', methods=['POST'])
def download_results():
    results = request.json['results']
    df = pd.DataFrame(results)
    csv_file = BytesIO()
    df.to_csv(csv_file, index=False)
    csv_file.seek(0)
    return send_file(csv_file, attachment_filename="results.csv", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
