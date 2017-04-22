from __future__ import division
from threading import Thread
from cloudsight import API, OAuth
from math import ceil
import time
import os
from Queue import Queue
from glob import glob
from utils import update_progress, set_failed, is_failed

import cv2
import operator
import numpy
import base64
import json
import requests
from collections import defaultdict


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
#https://github.com/Microsoft/Cognitive-Vision-Python/blob/master/Jupyter%20Notebook/Computer%20Vision%20API%20Example.ipynb
MICROSOFT_API_KEY = os.environ.get("MICROSOFT_API_KEY")

## IBM
IBM_API_KEY = os.environ.get("IBM_API_KEY")

## Google

# Thread List
threads = []

# Result Dictionary
resultdict = defaultdict(dict, {})

class MultiThreadException(Exception):
    pass
    
# Used to detect errors and to prevent hangups
def fail_check():
    if is_failed():
        BREAK = True
        raise MultiThreadException("Critical Error, Cannot Continue")

################################################################################   CLOUDSIGHT    ###############

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
        resultdict[image]['cloudsight'] = (result['status'], result['name'])
    else:
        resultdict[image]['cloudsight'] = (result['status'], result['reason'])

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
        resultdict[filename] = {"cloudsight": [],
                                "msft" : [],
                                "ibm": [], 
                                "google" : []}
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
  
############################################################################     main for cloudsight
#if __name__ == '__main__':
#    get_results()    

####################################################################################   MICROSOFT   #############
image = '2_birds.png'


def microsoft_fetch():
    global done
    #while(True):
    """try:
        # Retrieve a 'job' from the queue
        image = msft_q.get(True,1)
    except: # Occurs if q is empty
        if FLAG and msft_q.empty() or BREAK:
            # If FLAG is high (no more items being fed to queue) 
            # and q is empty or BREAK is high due to error, quit
            return
        else:
            # Go back to the top and try to fetch object
            continue"""

    
    # At this point, var image now contains the filepath for our subimage
    # Initialize result object which will hold result from api call
    result = None

    # Call the api with image and store response object to retrieve response
    result = microsoft_call_vision_api(image)
    # At this point we have our result
    microsoft_process_result(image,result)
        #cs_q.task_done()
        #continue

# Process and store result retrieved from Microsoft API
def microsoft_process_result(image, result):
    if result is None:
        return
    print image

    #print result['tags']
    #Process completed
    
    #we are going to create a default dictionary 
    
    resultdict[image] 
    resultdict[image]['msft'] = result['tags']

    print '11111111111111111111111111111111111111111111111'
    print resultdict[image]['msft']


def microsoft_call_vision_api(image_filename):
    api_key = 'e49d7545bfe84b619ce3d0e3f2a9046e'
    post_url = "https://api.projectoxford.ai/vision/v1.0/analyze?visualFeatures=Categories,Tags,Description,Faces,ImageType,Color,Adult&subscription-key=" + api_key

    image_data = open(image_filename, 'rb').read()
    result = requests.post(post_url, data=image_data, headers={'Content-Type': 'application/octet-stream'})
    result.raise_for_status()
    
    j = json.loads(result.text)
    return j

# Return a dictionary of features to their scored values (represented as lists of tuples).mu
# Scored values must be sorted in descending order.
#
# { 
#    'feature_1' : [(element, score), ...],
#    'feature_2' : ...
# }
#
# E.g.,
#
# { 
#    'tags' : [('throne', 0.95), ('swords', 0.84)],
#    'description' : [('A throne made of pointy objects', 0.73)]
# }
#
def get_standardized_result(api_result): #######################################################????????????????
    output = {
        'tags' : [],
#        'captions' : [],
#        'categories' : [],
#        'adult' : [],
#        'image_types' : []
#        'tags_without_score' : {}
    }

    for tag_data in api_result['tags']:
        output['tags'].append((tag_data['name'], tag_data['confidence']))

    return output


"""if __name__ == '__main__': 
    microsoft_fetch()  """

#########################################################################################   IBM    ##################
from watson_developer_cloud import VisualRecognitionV3
# pip install --upgrade watson-developer-cloud

def ibm_fetch():
    global done
    #while(True):
    """try:
        # Retrieve a 'job' from the queue
        image = msft_q.get(True,1)
    except: # Occurs if q is empty
        if FLAG and msft_q.empty() or BREAK:
            # If FLAG is high (no more items being fed to queue) 
            # and q is empty or BREAK is high due to error, quit
            return
        else:
            # Go back to the top and try to fetch object
            continue"""

    
    # At this point, var image now contains the filepath for our subimage
    # Initialize result object which will hold result from api call
    result = None

    # Call the api with image and store response object to retrieve response
    result = ibm_call_vision_api(image)
    # At this point we have our result
    ibm_process_result(image,result)
    
    #cs_q.task_done()
    #continue

# Process and store result retrieved from IBM API
def ibm_process_result(image, result):
    if result is None:
        return
    print image

    a= result['images']
    b= a[0]                 #takes first set
    c= b['classifiers']     #takes classifier set
    d= c[0]                 #classes
    #print d

    #Process completed
    
    #we are going to create a default dictionary 
    
    resultdict[image] 

    if "error" in result:
        # Check for errorid
        resultdict[image]['ibm'] = "error-file-bigger-than-2mb"
        #output['tags'].append(("error-file-bigger-than-2mb", None))
        return

    resultdict[image]['ibm'] = d

    print '2222222222222222222222222222222222222222222'
    print resultdict[image]['ibm']


def ibm_call_vision_api(image_filename):
    api_key = '5fdfb59997bcc7fba0ce643412fb7dbddf35cb13'

    # Via example found here: 
    # https://github.com/watson-developer-cloud/python-sdk/blob/master/examples/visual_recognition_v3.py
    visual_recognition = VisualRecognitionV3('2016-05-20', api_key=api_key)

    with open(image_filename, 'rb') as image_file:
        result = visual_recognition.classify(images_file=image_file)

    #print result

    return result


def ibm_get_standardized_result(api_result):
    output = {
        'tags' : [],
    }

    #api_result = api_result["images"][0]

    if "error" in api_result:
        # Check for errorid
        output['tags'].append(("error-file-bigger-than-2mb", None))
    """else:
        api_result = api_result["classifiers"][0]
        for tag_data in api_result['classes']:
            output['tags'].append((tag_data['class'], tag_data['score']))"""

    print '11111111111111111111111111111111111111111111111111111111111111111111'
    print output

    return output


"""if __name__ == '__main__': 
    ibm_fetch()  """

#########################################################################################   GOOGLE  @@@@@@@@@@@@@@@@@@

def google_fetch():
    global done
    #while(True):
    """try:
        # Retrieve a 'job' from the queue
        image = msft_q.get(True,1)
    except: # Occurs if q is empty
        if FLAG and msft_q.empty() or BREAK:
            # If FLAG is high (no more items being fed to queue) 
            # and q is empty or BREAK is high due to error, quit
            return
        else:
            # Go back to the top and try to fetch object
            continue"""

    
    # At this point, var image now contains the filepath for our subimage
    # Initialize result object which will hold result from api call
    result = None

    i=0         #count how many files

    for filename in glob('/home/eclippse/Desktop/tmp/*.jpg'): 
        result = google_call_vision_api(filename)
        i = i +1
        google_process_result(filename,result)

    print i 




    """path1 = "/home/eclippse/Desktop/tmp/"
    for filename in path1:
        call something..........
        # Call the api with image and store response object to retrieve response
        result = google_call_vision_api(im)
        # At this point we have our result
        google_process_result(im,result)"""
    
    #cs_q.task_done()
    #continue

# Process and store result retrieved from Microsoft API
def google_process_result(image, result):
    if result is None:
        return
    print image

    a= result['responses']
    b= a[0]                      #takes first set
    c= b['labelAnnotations']     #takes labelAnnotations

    #print c

    #Process completed
    
    #we are going to create a default dictionary 
    
    resultdict[image] 

    if "error" in result:
        # Check for errorid
        resultdict[image]['ibm'] = "error-file-bigger-than-2mb"
        #output['tags'].append(("error-file-bigger-than-2mb", None))
        return

    resultdict[image]['google'] = c

    print resultdict[image]['google']
    print '2222222222222222222222222222222222222222222222222222 FINISHED'
    

def _convert_image_to_base64(image_filename):
    with open(image_filename, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()

    return encoded_string

def google_call_vision_api(image_filename):
    api_key = 'AIzaSyBl670JW4dni18NSYDE9uilOMCAn-IYzCE'
    post_url = "https://vision.googleapis.com/v1/images:annotate?key=" + api_key

    base64_image = _convert_image_to_base64(image_filename)

    post_payload = {
      "requests": [
        {
          "image": {
            "content" : base64_image
          },
          "features": [
            {
              "type": "LABEL_DETECTION",
              "maxResults": 10
            },
            {
              "type": "FACE_DETECTION",
              "maxResults": 10
            },
            {
              "type": "LANDMARK_DETECTION",
              "maxResults": 10
            },      
            {
              "type": "LOGO_DETECTION",
              "maxResults": 10
            },
            {
              "type": "SAFE_SEARCH_DETECTION",
              "maxResults": 10
            },          
          ]
        }
      ]
    }

    result = requests.post(post_url, json=post_payload)
    result.raise_for_status()

    k = json.loads(result.text)

    #print result.text to see a better format of this json

    
    #print '1111111111111111111111111111111111111111111111111111111111'

    return k



# See this function in microsoft.py for docs.
def google_get_standardized_result(api_result):
    output = {
        'tags' : [],
    }

    api_result = api_result['responses'][0]

    if 'labelAnnotations' in api_result:
        for tag in api_result['labelAnnotations']:
            output['tags'].append((tag['description'], tag['score']))
    else:
        output['tags'].append(('none found', None))

    if 'logoAnnotations' in api_result:
        output['logo_tags'] = []
        for annotation in api_result['logoAnnotations']:
            output['logo_tags'].append((annotation['description'], annotation['score']))

    return output


if __name__ == '__main__': 
    #cloudsight_fetch()

    #microsoft_fetch()
    #print '3333333333333333333333333333333333333333'
    #ibm_fetch()
    print '44444444444444444444444444444444444444444444444444'
    google_fetch()



