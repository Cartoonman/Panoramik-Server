from threading import Thread, activeCount
from cloudsight import API, OAuth
import time
import os
import sys
from Queue import Queue
import glob
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


def fetch():
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
                q.task_done()
                return
            break
        process_result(image, status)
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
    num_files = len(glob.glob('/tmp/*.jpg'))
    print num_files
    count = 0
    try:
        for filename in glob.glob('/tmp/*.jpg'): #assuming gif
            time.sleep(3.1)
            q.put(filename)
            count = count + 1
            if count == 5:
                break
            #break ## REMOVE FOR FULL PROCESSING. RIGHT NOW ONLY 1 IMAGE WILL BE SENT.
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
