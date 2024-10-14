from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import openpyxl
from io import BytesIO  # For file handling

# Import your specific functions
from bulk import filter_fraud_transactions  # Ensure this function is defined in bulk.py
from single import *  # Ensure this function is defined in single.py

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/page_2', methods=['GET', 'POST'])
def page_2():
    if request.method == 'POST':
        file1 = request.files.get('bulk_transactions')
        file2 = request.files.get('single_transactions')

        try:
            if file1 and file1.filename.endswith('.csv'):
                df1 = pd.read_csv(file1)
                results1 = filter_fraud_transactions(df1)  # Call your function here
                return jsonify(results1)  # Return results as JSON
            elif file2 and file2.filename.endswith('.csv'):
                df2 = pd.read_csv(file2)
                results2 = your_single_function(df2)  # Call your single transaction function here
                return jsonify(results2)  # Return results as JSON
            else:
                return "Invalid file format. Please upload CSV files named 'Bulk Transactions' or 'Single Transactions'.", 400
        except Exception as e:
            return f"An error occurred: {str(e)}", 500  # Return the error message for debugging

    return render_template('page_2.html')  # Ensure this is rendering the correct template

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
