from __future__ import division
from threading import Thread
from cloudsight import API, OAuth
from math import ceil
import time
import os
import sys
from Queue import Queue
from glob import glob
from rq import get_current_job
from utils import update_progress


concurrent = 5
FLAG = False
BREAK = False
CLOUDSIGHT_API_KEY = os.environ.get("CLOUDSIGHT_API_KEY")
CLOUDSIGHT_API_SECRET = os.environ.get("CLOUDSIGHT_API_SECRET")

api = API(OAuth(CLOUDSIGHT_API_KEY, CLOUDSIGHT_API_SECRET))
q = Queue(concurrent * 2)
threads = []
result = {}
done = 0

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
                with open(image, 'rb') as f:
                    response = api.image_request(f, image, {
                    'image_request[locale]': 'en-US',})
                    while True:
                        status = api.wait(response['token'], timeout=30)
                        if status['status'] == 'not completed':
                            continue
                        break
                
            except Exception as e:
                print e
                if 'exceeded' in str(e):
                    time.sleep(3)
                    continue
                done = done + 1
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
        if a == 40:
            q.task_done()
            return


def process_result(image, status):
    print image , status
    if status['status'] == 'timeout':
        pass
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
    try:
        for filename in glob('/tmp/*.jpg'): 
            time.sleep(3.1)
            q.put(filename)
            break ## REMOVE FOR FULL PROCESSING. RIGHT NOW ONLY 1 IMAGE WILL BE SENT.
        FLAG = True  
        while True:
            if q.empty() == False:
                time.sleep(1)
            else:
                break
    except KeyboardInterrupt:
        print "Alas poor port scanner..."
        BREAK = True
        sys.exit(1)
    q.join()
    return result
