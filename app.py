from flask import Flask, flash, redirect, render_template, request, send_file, url_for
import joblib
import pandas as pd
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        return "<h2>You do not have permission to add users.</h2>", 403

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            message = 'Username already exists'
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            message = 'User added successfully'
        
        return render_template('add_user.html', message=message)

    return render_template('add_user.html')


# Path to save uploaded and processed files
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        if 'bulk_transactions' not in request.files:
            return "No file part in the request."

        file = request.files['bulk_transactions']

        if file.filename == '':
            return "No file selected."

        # Save the uploaded file to the upload folder
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Process the file and filter transactions
        filtered_file_path = filter_fraud_transactions(file_path)

        # Redirect to the download page with the file path
        return redirect(url_for('download_file', filename=os.path.basename(filtered_file_path)))

    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    # Create the full path to the file
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    
    # Send the file as a download
    return send_file(file_path, as_attachment=True)

def filter_fraud_transactions(file_path):
    # Load the dataset
    df = pd.read_csv(file_path)

    # Filter transactions that are either TRANSFER or CASH_OUT
    transfer_cashout = df[df['type'].isin(['TRANSFER', 'CASH_OUT'])]

    # Sort by step and ensure we are looking for transactions where cash_out comes after transfer
    transfer_cashout = transfer_cashout.sort_values(by=['step', 'amount', 'type'])

    # Group by 'step' and 'amount' to find matching transactions
    def filter_matching_transactions(group):
        if 'TRANSFER' in group['type'].values and 'CASH_OUT' in group['type'].values:
            transfer_idx = group.index[group['type'] == 'TRANSFER'][0]
            cash_out_after_transfer = group[(group.index > transfer_idx) & (group['type'] == 'CASH_OUT')]

            transfer_cash_out_filtered = pd.concat([group.loc[[transfer_idx]], cash_out_after_transfer])
            amount_check = transfer_cash_out_filtered[
                transfer_cash_out_filtered['amount'] <= transfer_cash_out_filtered['oldbalanceOrg']
            ]

            zero_balance_check = group[
                (group['oldbalanceOrg'] == 0) & (group['newbalanceOrig'] == 0) |
                (group['oldbalanceDest'] == 0) & (group['newbalanceDest'] == 0)
            ]

            return pd.concat([amount_check, zero_balance_check]).drop_duplicates()

        return pd.DataFrame()

    matching_transactions_6 = transfer_cashout.groupby(['step', 'amount'], group_keys=False).apply(filter_matching_transactions)

    # Save the filtered dataset to a new CSV
    filtered_file_path = os.path.join(PROCESSED_FOLDER, 'filtered_transactions.csv')
    matching_transactions_6.to_csv(filtered_file_path, index=False)

    # Return the path to the filtered file
    return filtered_file_path

# Load the random forest model
loaded_rf = joblib.load("fraud_detection_random_forest_smote.joblib")

@app.route('/single')
@login_required
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

@app.route('/download_single')
def download_file_single():
    # Check if the file exists before attempting to send it
    file_path_1 = 'high_risk_transactions.csv'
    if os.path.exists(file_path_1):
        return send_file(file_path_1, as_attachment=True)
    else:
        return "<h2>Error: No file available for download.</h2>"
    
@app.route('/return')
def return_to_main():
    return render_template('index.html')

@app.cli.command('create-admin')
def create_admin():
    username = input('Enter admin username: ')
    password = input('Enter admin password: ')
    admin = User(username=username, password=generate_password_hash(password), is_admin=True)
    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully!')

if __name__ == '__main__':
    app.run(debug=True)
