from rq import get_current_job
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
job = get_current_job()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
               
def image_size(f):    
    size = reduce(lambda x,y: x*y, f.size)        
    f.close()
    return size   
           
def initialize_progress(j):
    j.meta['progress'] = 0
    j.meta['state'] = "Ready"
    j.save()
           
def update_progress(state=None, cs=0):    
    if job is None:
        print "Warning, non-job object detected, if this is running on Worker instance, investigate immediately"
        return
    job.meta['progress'] = job.meta['progress'] + 10 if cs == 0 else job.meta['progress'] + cs
    if state is not None:
        job.meta['state'] = state
    job.save()
    
    
def set_finished():
    job.set_status('finished') 
    job.save()      
    
def set_failed():
    job.set_status('failed') 
    job.save()  
 
def is_failed():
    return job.is_failed
    
def mapx(c):
    return c[0][0]

def mapy(c):
    return c[0][1]
