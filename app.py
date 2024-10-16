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
        #file2 = request.files.get('single_transactions')

        try:
            if file1 and file1.filename.endswith('.csv'):
                df1 = pd.read_csv(file1)
                results = filter_fraud_transactions(df1)  # Call your function here
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

# Load the random forest model
loaded_rf = joblib.load("fraud_detection_random_forest_smote.joblib")

@app.route('/single')
def single():
    return render_template('single.html')

@app.route('/process', methods=['POST'])
def process_transaction():
    # Get the form data for all transactions
    transaction_types = request.form.getlist('transaction_type[]')
    amounts = request.form.getlist('amount[]')
    nameOrigs = request.form.getlist('nameOrig[]')
    oldBalanceOrigs = request.form.getlist('oldBalanceOrig[]')
    newBalanceOrigs = request.form.getlist('newBalanceOrig[]')
    nameDests = request.form.getlist('nameDest[]')
    oldBalanceDests = request.form.getlist('oldBalanceDest[]')
    newBalanceDests = request.form.getlist('newBalanceDest[]')

    # Prepare a DataFrame to hold all transactions
    data_entry = pd.DataFrame(columns=['amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig', 
                                       'nameDest', 'oldbalanceDest', 'newbalanceDest', 'type_CASH_IN', 
                                       'type_CASH_OUT', 'type_DEBIT', 'type_PAYMENT', 'type_TRANSFER'])

    # Loop through each transaction entry and append it to the dataframe
    for i in range(len(transaction_types)):
        # Add data to the dataframe
        data_entry.loc[i] = [
            float(amounts[i]), nameOrigs[i], float(oldBalanceOrigs[i]), float(newBalanceOrigs[i]),
            nameDests[i], float(oldBalanceDests[i]), float(newBalanceDests[i]), 0, 0, 0, 0, 0
        ]
        
        # Set the appropriate transaction type flag
        if transaction_types[i] == 'CASH_IN':
            data_entry.loc[i, 'type_CASH_IN'] = 1
        elif transaction_types[i] == 'CASH_OUT':
            data_entry.loc[i, 'type_CASH_OUT'] = 1
        elif transaction_types[i] == 'DEBIT':
            data_entry.loc[i, 'type_DEBIT'] = 1
        elif transaction_types[i] == 'PAYMENT':
            data_entry.loc[i, 'type_PAYMENT'] = 1
        elif transaction_types[i] == 'TRANSFER':
            data_entry.loc[i, 'type_TRANSFER'] = 1

    # Drop columns not needed for prediction
    data_pred = data_entry.drop(['nameOrig', 'nameDest'], axis=1)

    # Predict fraud for all transactions
    predictions = loaded_rf.predict(data_pred)

    # Add predictions back to the original data
    data_entry['prediction'] = predictions

    # Extract high-risk (fraudulent) transactions
    high_risk_transactions = data_entry[data_entry['prediction'] == 1]

    # If there are any high-risk transactions, save them to a CSV and make it downloadable
    if not high_risk_transactions.empty:
        # Define CSV file path
        csv_file_path = 'high_risk_transactions.csv'
        
        # Save the high-risk transactions to a CSV file
        high_risk_transactions.to_csv(csv_file_path, index=False)

        # Create a list of tuples with (nameOrig, nameDest)
        high_risk_accounts = list(zip(high_risk_transactions['nameOrig'], high_risk_transactions['nameDest']))

        # Render the template with the list of high-risk accounts
        return render_template('single.html', high_risk_accounts=high_risk_accounts)
    else:
        return "<h2>All transactions processed successfully. No fraud detected.</h2>"

@app.route('/download')
def download_file():
    # Check if the file exists before attempting to send it
    file_path = 'high_risk_transactions.csv'
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "<h2>Error: No file available for download.</h2>"
    
@app.route('/return')
def return_to_main():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
