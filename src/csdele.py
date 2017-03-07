from urlparse import urlparse
from threading import Thread, activeCount
import cloudsight
import time
import httplib, sys
from Queue import Queue
import glob
import pickle

concurrent = 5

global FLAG
FLAG = False
global BREAK
BREAK = False

auth = cloudsight.OAuth('yrrsdv08vD054qGNV710Sg', 'Qm7T0L8LqZgStVby1CT_4g')
api = cloudsight.API(auth)
result = {}

def doWork():
    while(True):
        try:
            image = q.get(True,1)
        except:
            if FLAG and q.empty() or BREAK:
                return
            else:
                continue
        try:
            with open(image, 'rb') as f:
                response = api.image_request(f, image, {
                'image_request[locale]': 'en-US',
            })
            status = api.wait(response['token'], timeout=30)
        except Exception as e:
            print e
            q.task_done()
            return
        doSomethingWithResult(image, status)
        q.task_done()

def doSomethingWithResult(image, status):
    if status['status'] == 'completed':
        result[image] = (status['status'], status['name'])
    else:
        result[image] = (status['status'], status['reason'])

    print image , status
  
threads = []
q = Queue(concurrent * 2)
for i in range(concurrent):
    t = Thread(target=doWork)
    threads.append(t)
    t.start()
try:
    for filename in glob.glob('/tmp/*.jpg'): #assuming gif
        time.sleep(3.05)
        q.put(filename)
        break
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

print 'CYKABLYAD'

output = open('output.txt', 'w')
pickle.dump(result, output)
output.close()
