import base64
import json
import requests

image = 'multiplechairs.jpg'

def microsoft_fetch():
    global done
    while(True):
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
        microsoft_process_result(image,result)
        #cs_q.task_done()
        continue

# Process and store result retrieved from Microsoft API
def microsoft_process_result(image, result):
    if result is None:
        return
    print image

    print result['tags']
    #Process completed
    resultdict[image]['msft'] = result['tags']


def call_vision_api(image_filename):
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
def get_standardized_result(api_result):
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

#    for caption in api_result['description']['captions']:
#        output['captions'].append((caption['text'], caption['confidence']))


#    for category in api_result['categories']:
#        output['categories'].append(([category['name'], category['score']))

#    output['adult'] = api_result['adult']

#    for tag in api_result['description']['tags']:
#        output['tags_without_score'][tag] = 'n/a'

#    output['image_types'] = api_result['imageType']

    return output


if __name__ == '__main__': 
    microsoft_fetch()  


