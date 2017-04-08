import os
from flask import Flask, request, flash, redirect, url_for, jsonify, render_template
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
        
        
def run_analysis(filename, DEBUG=False):
    j = q.enqueue(proc.run_process, filename, DEBUG)   
    utils.initialize_progress(j)     
    return j

@app.route("/")
def home():
    return render_template('home.html')


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
            if not request.form.getlist('cbox'):
                job = run_analysis(filename, True)
            else:
                job = run_analysis(filename, False)
            return redirect(url_for('.get_status', job_id=job.id, web="True"))

    else:
        return render_template('upload.html')
    
@app.route("/status", methods=['GET'])
def get_status():
    job_id = request.args.get("job_id")  
    web = request.args.get("web")  
    
    status = status_handler(job_id)
    if web:
        if 'DONE' in str(status.response[0]):
            return render_template('status.html', resp = str(status.response[0]), running=False, img_url = q.fetch_job(job_id).meta['url'])
        elif 'FAIL' in str(status.response[0]):
            return render_template('status.html', resp = str(status.response[0]), running=False)
        else:
            return render_template('status.html', resp = str(status.response[0]), running=True)

    else:
        return status
     
    
    
    
            
def status_handler(job_id):
    if job_id:    
        job = q.fetch_job(job_id)    
        if job is not None:
            job.refresh()
            status = job.status
            if (status == 'started'):
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
