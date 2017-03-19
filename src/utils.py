from rq import get_current_job
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
job = get_current_job()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
           
def str2hex(x):
    scale = 16 ## equals to hexadecimal
    num_of_bits = 64
    return bin(int(x, scale))[2:].zfill(num_of_bits)


def hamming(p1,p2):
    x = str2hex(str(p1.x))
    y = str2hex(str(p2.x))
    """Calculate the Hamming distance between two bit strings"""
    assert len(x) == len(y)
    count,z = 0,int(x,2)^int(y,2)
    while z:
        count += 1
        z &= z-1 # magic!
    return count           
           
def initialize_progress():
    job.meta['progress'] = 0
    job.meta['state'] = "Starting"
    job.save()
           
def update_progress(state=None, cs=0):    
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
