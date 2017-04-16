import base64
import json
import requests

image= 'multiplechairs.jpg'

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


    # Call the api with image and store response object to retrieve response
    result = google_call_vision_api(image)
    # At this point we have our result
    
    #ibm_process_result(image,result)
    
    #cs_q.task_done()
    #continue

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

    print k

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
    google_fetch()  
