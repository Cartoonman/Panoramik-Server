import os

from flask import Flask, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import subprocess
import processimage

from utils import allowed_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.debug = True


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        print file
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

            if os.path.isfile(os.path.join(UPLOAD_FOLDER, filename)):
                return jsonify({"Filename": filename})
            else:
                return jsonify({"Error": "Could not save image properly"})

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.route("/uploaded_file")
def uploaded_file():
    return "uploaded file successfully"

@app.route("/uploadImage", methods=['GET', 'POST'])
def uploadImage():
    if request.method == 'POST':
        encodedData = request.form['file']
        if encodedData:
            filename = "imageToSave.png"
            with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as fh:
                fh.write(encodedData.decode('base64'))
            print os.path.isfile(os.path.join(UPLOAD_FOLDER, filename))
            result = processimage.run(os.path.join(UPLOAD_FOLDER, filename)], BASE_DIR)
            
            return jsonify(result)
            #return jsonify({"Result": "Succeeded"})
        else:
            return jsonify({"Result": "Failed, could not find files"})
    else:
        return jsonify({"Error": "POST Request Only"})

if __name__ == "__main__":
    app.run(host="0.0.0.0")
