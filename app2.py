from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import SubmitField
from pymongo import MongoClient
import csv
import random
import string
import hcaptcha

app = Flask(__name__)

app.secret_key = '55bdf9cb64e6e6ffe47ab98654f77e4e'
app.config['HCAPTCHA_SECRET_KEY'] = 'ES_c8ae137714704200b37681d785cc9afb'
app.config['HCAPTCHA_SITE_KEY'] = "6d28789a-a14d-4f89-8e27-a0b9d363fa86"  # Replace with your hCaptcha secret key

client = MongoClient('mongodb://localhost:27017/')
db = client['csv_importer']

def generate_random_collection_name():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

class DeleteForm(FlaskForm):
    hcaptcha = RecaptchaField()
    submit_continue = SubmitField('Continue')
    submit_delete_all = SubmitField('Delete All')

@app.route('/')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
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

@app.route('/display/<collection_name>', methods=['GET', 'POST'])
def display(collection_name):
    # No need to retrieve collection_name from session, use it directly
    collection = db[collection_name]
    data = list(collection.find())

    form = DeleteForm()

    if request.method == 'POST':
        hcaptcha_response = request.form.get('hcaptcha')

        if not verify_hcaptcha(hcaptcha_response):
            flash('hCaptcha verification failed. Please try again.', 'error')
            return render_template('display.html', data=data, collection_name=collection_name, form=form)

        # Perform actions based on the clicked button
        if form.submit_continue.data:
            flash('Continue action performed!', 'success')
            return redirect(url_for('success'))

        elif form.submit_delete_all.data:
            # Delete the entire collection from MongoDB
            db.drop_collection(collection_name)
            flash('Collection deleted successfully!', 'success')
            return redirect(url_for('removed'))

    return render_template('display.html', data=data, collection_name=collection_name, form=form)

def verify_hcaptcha(response_token):
    try:
        client = hcaptcha.Client(app.config['HCAPTCHA_SECRET_KEY'])
        verification = client.verify(response_token)
        return verification['success']
    except Exception as e:
        print(f"Error during hCaptcha verification: {e}")
        return False

@app.route('/success', methods=['GET', 'POST'])
def success():
    return render_template('success.html')

@app.route('/removed/<collection_name>', methods=['GET', 'POST'])
def removed(collection_name):
    return render_template('removed.html', collection_name=collection_name)



if __name__ == '__main__':
    app.run(debug=True)
