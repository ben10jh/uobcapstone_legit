from flask import Flask, render_template
import pandas as pd 
import openpyxl
from bulk.py import bulk.py #change this to pritika's bulk ml model
from single.py import single.py #change this to single ml model   


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/second_page')
def second_page():
    return render_template('page2.html')

#(remove if needed) if __name__ == '__main__':
#(remove if needed)    app.run(debug=True)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file1 = request.files.get('bulk_transactions')  # Access the first file upload
        file2 = request.files.get('single_transactions')  # Access the second file upload

        if file1 and file1.filename.endswith('.csv'):
            # Process the 'Bulk Transactions' CSV file
            df1 = pd.read_csv(file1)
            results1 = your_ml_function1(df1)
            return jsonify(results1)
        elif file2 and file2.filename.endswith('.csv'):
            # Process the 'Single Transactions' CSV file
            df2 = pd.read_csv(file2)
            results2 = your_ml_function2(df2)
            return jsonify(results2)
        else:
            return "Invalid file format. Please upload CSV files named 'Bulk Transactions' or 'Single Transactions'."
    return render_template('index.html')


#Returning results back to downloadable csv file
@app.route('/download_results', methods=['POST'])
def download_results():
    results = request.json['results']
    df = pd.DataFrame(results)
    csv_file = "results.csv"
    df.to_csv(csv_file, index=False)
    return send_file(csv_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
