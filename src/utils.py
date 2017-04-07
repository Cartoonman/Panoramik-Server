from __future__ import division
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
   
def region_filter(c, h, v):
    x1, y1, x2, y2 = c
    width = x2-x1
    height = y2-y1
        
    if (width > int(h *.45)) or (height > int(v *.45)):  
        """ 
        Filter for regions whose length/widths are too long 
        (threshold set at 45% of image's own horizontal/vertical dimensions) 
        """
        return False
        
    elif min(height, width)/max(height, width) < 0.25:
        """
        Filter for too low of a ratio of region width and region height 
        (too thin, not square-like enough.) Threshold set at 4:1 ratio.
        """
        return False
        
    else:
        # Otherwise, the region passes
        return True

def pad_box(c, h, v, p):
        x1, y1, x2, y2 = c
             
        width = x2-x1
        height = y2-y1
        
        new_width = width*p
        new_height = height*p
        
        w_delta = new_width - width
        h_delta = new_height - height
        delta = int(max(w_delta//2, h_delta//2))
        p_x1 = max(x1 - delta, 0)
        p_y1 = max(y1 - delta, 0)
        p_x2 = min(x2 + delta, h)
        p_y2 = min(y2 + delta, v)
        
        return (p_x1, p_y1, p_x2, p_y2)


           
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
