from flask import Flask, request, render_template
import pandas as pd

app = Flask(__name__)

@app.route('/')
def upload_file():
    return render_template('index.html')

@app.route('/uploader', methods=['POST'])
def uploader():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and file.filename.endswith('.csv'):
        df = pd.read_csv(file)
        return df.to_html()
    return 'Invalid file type'

if __name__ == '__main__':
    app.run(debug=True)
