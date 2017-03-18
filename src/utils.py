from rq import get_current_job
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
job = get_current_job()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
def initialize_progress():
    job.meta['progress'] = 0
    job.meta['state'] = "Starting"
    job.save()
           
def update_progress(state=None, cs=0):    
    job.meta['progress'] = job.meta['progress'] + 10 if cs == 0 else job.meta['progress'] + cs
    if state is not None:
        job.meta['state'] = state
    job.save()
    
def set_failed():
    job.set_status('failed')   
 
def is_failed():
    return job.is_failed
    
def mapx(c):
    return c[0][0]

def mapy(c):
    return c[0][1]
