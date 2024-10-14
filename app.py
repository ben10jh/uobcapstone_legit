from flask import Flask, render_template, request, send_file
import pandas as pd
from io import BytesIO
from bulk import filter_fraud_transactions  # Import your bulk processing function
from single import *  # Import your single transaction processing function

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []  # Initialize results
    if request.method == 'POST':
        file1 = request.files.get('bulk_transactions')
        file2 = request.files.get('single_transactions')

        try:
            if file1 and file1.filename.endswith('.csv'):
                df1 = pd.read_csv(file1)
                results = filter_fraud_transactions(df1)  # Call your function here
            elif file2 and file2.filename.endswith('.csv'):
                df2 = pd.read_csv(file2)
                results = your_single_function(df2)  # Call your single transaction function here
            else:
                return "Invalid file format. Please upload valid CSV files.", 400
        except Exception as e:
            return f"An error occurred: {str(e)}", 500  # Return the error message for debugging

    print("Results:", results)  # Debug output

    return render_template('index.html', results=results)  # Pass results to the template

@app.route('/download_results', methods=['POST'])
def download_results():
    results = request.form['results']  # Use request.form instead of request.json
    df = pd.DataFrame(eval(results))  # Convert the string back to a list
    csv_file = BytesIO()
    df.to_csv(csv_file, index=False)
    csv_file.seek(0)
    return send_file(csv_file, attachment_filename="results.csv", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
