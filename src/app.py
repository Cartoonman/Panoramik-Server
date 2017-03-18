import os
from flask import Flask, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import proc 
from rq import Queue
from boto3 import client
import utils
import redis

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
conn = redis.from_url(os.environ.get("REDIS_URL"))
q = Queue(connection=conn) #redis rq queue 

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.debug = True

def s3_upload(filename):
    s3 = client('s3')
    s3.upload_file(os.path.join(UPLOAD_FOLDER, filename), os.environ.get("S3_BUCKET"), filename)        
        
        
def run_analysis(filename):
    return q.enqueue(proc.run_process, filename, UPLOAD_FOLDER, BASE_DIR)        

@app.route("/")
def home():
    return "PANORAMIK API ENDPOINT"


@app.route("/upload", methods=['GET', 'POST'])
def upload(): #DEBUG ONLY
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
        if file and utils.allowed_file(file.filename):
            filename = secure_filename(file.filename) # filename here serves as key for now
            file.save(os.path.join(UPLOAD_FOLDER, filename))
                
            s3_upload(filename)
                         
            job = run_analysis(filename)
            return redirect(url_for('.get_status', job_id=job.id))
            #jsonify({"job_id":job.id})

    else:
        return '''
        <!doctype HTML>
        <html>
        <head>
        <title>Upload new File</title>
        </head>
        <body>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data>
          <p><input type=file name=file>
             <input type=submit value=Upload>
        </form>
        </body>
        </html>
        '''
    
@app.route("/status", methods=['GET'])
def get_status():
    print request.args.get("job_id")  
    job_id = request.args.get("job_id")  
    if job_id:      
        job = q.fetch_job(job_id)    
        if job is not None:
            status = job.status
            if (status == 'started'):
                print status
                print job.meta
                return jsonify({'status':"RUNNING",'message':"Please wait, processing",'progress':job.meta['progress'], 'state':job.meta['state']})
            elif status == 'queued':
                return jsonify({'status':"WAIT",'message':"Please wait, queued"})
            elif status == 'finished':
                return jsonify({'status':"DONE",'message':"Processing Completed. Data is attached.", 'data':job.result})
            elif status == 'failed':
                return jsonify({'status':"FAIL", 'message': "Failed, error occured. Please check logs"})
        else:
            return jsonify({'status':"NOT_EXIST", 'message':"Job " + job_id + " not found!"})
    else:
        return jsonify({'status':"INVALID", 'message':"Invalid request. Must use job_id query."})
            

@app.route("/uploadImage", methods=['POST'])
def uploadImage():
    encodedData = request.form['file']
    if encodedData:
        filename = "imageToSave.jpg"
        with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as fh:
            fh.write(encodedData.decode('base64'))
            
        s3_upload(filename)
                     
        job = run_analysis(filename)
        return jsonify({"job_id":job.id})
    else:
        return jsonify({"Result": "Failed, could not find files"})
        
if __name__ == "__main__":
    app.run(host='0.0.0.0')
