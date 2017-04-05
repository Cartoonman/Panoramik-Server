from __future__ import division
from threading import Thread
from cloudsight import API, OAuth
from math import ceil
import time
import os
from Queue import Queue
from glob import glob
from utils import update_progress, set_failed, is_failed


concurrent = 5
FLAG = False
BREAK = False
JOB_DONE = False
CLOUDSIGHT_API_KEY = os.environ.get("CLOUDSIGHT_API_KEY")
CLOUDSIGHT_API_SECRET = os.environ.get("CLOUDSIGHT_API_SECRET")

api = API(OAuth(CLOUDSIGHT_API_KEY, CLOUDSIGHT_API_SECRET))
q = Queue(concurrent * 2)
threads = []
result = {}
done = 0


class MultiThreadException(Exception):
    pass

def fail_check():
    if is_failed():
        BREAK = True
        raise MultiThreadException("Critical Error, Cannot Continue")
        
def fetch():
    global done
    while(True):
        try:
            image = q.get(True,1)
        except:
            if FLAG and q.empty() or BREAK:
                return
            else:
                continue
        while True:
            try:
                status = None
                with open(image, 'rb') as f:
                    response = api.image_request(f, image, {
                    'image_request[locale]': 'en-US',})
                    while True:
                        status = api.wait(response['token'], timeout=30)
                        if status['status'] == 'not completed':
                            continue
                        break
                break
            except Exception as e:
                print e
                if 'exceeded' in str(e):
                    time.sleep(3)
                    continue
                set_failed()
                q.task_done()
                return
            break
        process_result(image, status)
        done = done + 1
        q.task_done()

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


def process_result(image, status):
    if status is None or status['status'] == 'timeout':
        return
    print image , status
    if status['status'] == 'completed':
        result[image] = (status['status'], status['name'])
    else:
        result[image] = (status['status'], status['reason'])

def get_results():
    update_progress('Fetching Object Recognition from Cloudsight')
    for i in range(concurrent):
        t = Thread(target=fetch)
        threads.append(t)
        t.start()
    t = Thread(target=monitor, args=(len(glob('/tmp/*.jpg')),))
    threads.append(t)
    t.start()
    
    for filename in glob('/tmp/*.jpg'): 
        fail_check()
        time.sleep(3.1)
        q.put(filename)
        #break ## REMOVE FOR FULL PROCESSING. RIGHT NOW ONLY 1 IMAGE WILL BE SENT.
    FLAG = True  
    while True:
        if q.empty() == False:
            fail_check()
            time.sleep(1)
        else:
            break
    q.join()
    JOB_DONE = True
    return result
