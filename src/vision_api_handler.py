from __future__ import division
from threading import Thread
from cloudsight import API, OAuth
from math import ceil
import time
import os
from Queue import Queue
from glob import glob
from utils import update_progress, set_failed, is_failed

# Number of Max Concurrent Threads
concurrent = 5

#Semaphores
FLAG = False
BREAK = False
JOB_DONE = False
done = 0

# Queue Objects
cs_q = Queue(concurrent * 2)
ibm_q = Queue(concurrent * 2)
msft_q = Queue(concurrent * 2)
google_q = Queue(concurrent * 2)

# API Keys and Secrets
## Cloudsight
CLOUDSIGHT_API_KEY = os.environ.get("CLOUDSIGHT_API_KEY")
CLOUDSIGHT_API_SECRET = os.environ.get("CLOUDSIGHT_API_SECRET")
cs_api = API(OAuth(CLOUDSIGHT_API_KEY, CLOUDSIGHT_API_SECRET))

## Microsoft

## IBM

## Google

# Thread List
threads = []

# Result Dictionary
resultdict = {}



class MultiThreadException(Exception):
    pass
# Used to detect errors and to prevent hangups
def fail_check():
    if is_failed():
        BREAK = True
        raise MultiThreadException("Critical Error, Cannot Continue")
        
def cloudsight_fetch():
    global done
    while(True):
        try:
            # Retrieve a 'job' from the queue
            image = cs_q.get(True,1)
        except: # Occurs if q is empty
            if FLAG and cs_q.empty() or BREAK:
                # If FLAG is high (no more items being fed to queue) 
                # and q is empty or BREAK is high due to error, quit
                return
            else:
                # Go back to the top and try to fetch object
                continue
                
        # At this point, var image now contains the filepath for our subimage
        while True:
            try:
                # Initialize result object which will hold result from api call
                result = None
                # Loading file as f
                with open(image, 'rb') as f:
                    # Call the api with image and store response object to retrieve response
                    response = cs_api.image_request(f, image, {
                    'image_request[locale]': 'en-US',})
                    # While Cloudsight is still processing our image
                    while True:
                        result = cs_api.wait(response['token'], timeout=30)
                        # Check to see if the status is finished or not
                        if result['status'] == 'not completed':
                            continue
                        break
                # At this point we have our result
                break
            # If any API issue occurs, it will be handled here
            except Exception as e:
                print e # Document the issue in logs
                # If the api request count has exceeded Cloudsight's limit
                if 'exceeded' in str(e):
                    # Wait a bit and try the api call again
                    time.sleep(3)
                    continue
                # Otherwise, this is a critical failure we cannot recover from.
                set_failed()
                cs_q.task_done()
                return
            print "THIS POINT NEVER SHOULD HAVE BEEN REACHED!"
            raise ValueError('Logic has somehow allowed code to reach this forbidden point.')
        # Process our result
        cloudsight_process_result(image, result)
        # Increment # of results done 
        done = done + 1
        # Declare to the queue that this task was finished, and loop back to the top to fetch another job
        cs_q.task_done()
        continue

# Used to monitor progress of fecthing results from API's
def monitor(files):
    global done
    a = 0
    while True:
        incr = int(ceil((40/files) * done))
        while a < incr:
            update_progress(None,1)   
            a = a + 1 
        if a == 40 or BREAK or JOB_DONE:
            return
        continue

# Process and store result retrieved from Cloudsight API
def cloudsight_process_result(image, result):
    if result is None or result['status'] == 'timeout':
        return
    print image , result
    if result['status'] == 'completed':
        resultdict[image] = (result['status'], result['name'])
    else:
        resultdict[image] = (result['status'], result['reason'])

def get_results():
    update_progress('Fetching Object Recognition Results')
    # Initialize up to concurrent number of threads
    for i in range(concurrent):
        t = Thread(target=cloudsight_fetch)
        threads.append(t)
        t.start()
    # Initialize our monitoring thread for progress reporting
    t = Thread(target=monitor, args=(len(glob('/tmp/*.jpg')),))
    threads.append(t)
    t.start()
    
    # Feed filenames into queue to be consumed by threads
    for filename in glob('/tmp/*.jpg'): 
        fail_check() 
        time.sleep(3.1) # Cloudsight Limit 1 req/3 sec
        cs_q.put(filename)
        break #!!!!!!! REMOVE FOR FULL PROCESSING. RIGHT NOW ONLY 1 IMAGE WILL BE SENT.!!!!!!!!!!!!!
    # We now announce to all threads that queue feeding has stopped.
    # If they see both FLAG = true and the queue is empty, thread will quit
    FLAG = True  
    
    # Keep checking until the queue is empty, and check for any errors
    while True:
        if cs_q.empty() == False:
            fail_check()
            time.sleep(1)
        else:
            break
    # Join all remaining threads from queue if not done so by now.
    cs_q.join()
    
    # Declare job is done to monitor thread so it may quit now
    JOB_DONE = True
    
    return resultdict
