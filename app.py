from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
import csv
import random
import string

app = Flask(__name__)

app.secret_key = '55bdf9cb64e6e6ffe47ab98654f77e4e'
client = MongoClient('mongodb://localhost:27017/')
db = client['csv_importer']

def generate_random_collection_name():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

@app.route('/')
def upload_page():
    return render_template('upload.html')
@ app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('upload_page'))

    file = request.files['file']

    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('upload_page'))

   
    collection_name = generate_random_collection_name()
    collection = db[collection_name]

    # Read CSV file and insert into MongoDB collection
    csv_data = csv.DictReader(file.read().decode('utf-8').splitlines())
    for row in csv_data:
        collection.insert_one(row)

    flash('File successfully uploaded', 'success')
    session['collection_name'] = collection_name

    return redirect(url_for('display', collection_name=collection_name))

    





@ app.route('/display/<collection_name>', methods=['GET', 'POST'])
def display(collection_name):
    
    
    collection_name = session.get('collection_name')

    if not collection_name:
        # Redirect to the upload page if the collection name is not found in the session
        return redirect(url_for('upload_page'))

    collection = db[collection_name]
    data = list(collection.find())


    if request.method == 'POST':
        # Delete the entire collection from MongoDB
        db.drop_collection(collection_name)
        return redirect(url_for('upload_page'))
    return render_template('display.html', data=data, collection_name=collection_name)




@app.route('/success', methods=['GET', 'POST'])
def success():
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)
