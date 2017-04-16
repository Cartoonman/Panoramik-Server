import base64
import json
import requests
from watson_developer_cloud import VisualRecognitionV3
# pip install --upgrade watson-developer-cloud

image = 'multiplechairs.jpg'

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
    result = call_vision_api(image)
    # At this point we have our result
    
    
    #cs_q.task_done()
    #continue

def call_vision_api(image_filename):
    api_key = '5fdfb59997bcc7fba0ce643412fb7dbddf35cb13'

    # Via example found here: 
    # https://github.com/watson-developer-cloud/python-sdk/blob/master/examples/visual_recognition_v3.py
    visual_recognition = VisualRecognitionV3('2016-05-20', api_key=api_key)e wha

    with open(image_filename, 'rb') as image_file:
        result = visual_recognition.classify(images_file=image_file)

    text_result = json.dumps(result)
    print text_resultthe c
    hello = None

    hello = get_standardized_result(text_result)

    return hello


def get_standardized_result(api_result):
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


if __name__ == '__main__': 
    ibm_fetch()  
