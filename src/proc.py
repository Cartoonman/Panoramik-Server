#!/usr/bin/env python
from __future__ import division
import cv2
import math
import os
from glob import glob
import boto3
import json
import utils
import vision_api_handler

# Utility Functions
"""
Returns list of the corners of our bounding box rectangles as follows:

Panorama Image
.---------------------------------h
|(0, 0)                        (h, 0)
|       (x1, y1)
|           *--------
|           |       |
|           |       |
|           --------*
|               (x2, y2)
v              
(0, v)

"""
def edge_coordinates(hulls):
    return map(
        lambda c: (
            int(sorted(map(utils.mapx,c))[0]), #x1
            int(sorted(map(utils.mapy,c))[0]), #y1
            int(sorted(map(utils.mapx,c),reverse=True)[0]), #x2
            int(sorted(map(utils.mapy,c),reverse=True)[0])  #y2
        ), hulls)
    
    
"""
Generates subimages from source images and bounding boxes of our 
detected regions.
"""  
def generate_subimages(hulls, img, h, v, folder = '/tmp/'):
    utils.update_progress('Extracting Regions')
    fid = 0 
    pathlist = []
    
    coords = edge_coordinates(hulls)
    if len(coords) == 0:
        cv2.imwrite('/tmp/image.jpg', img)  
        pathlist.append(('/tmp/image.jpg', (0, h, 0, v)))
        return pathlist
    else:
        # p_c = padded coordinates. c = coordinates.
        for p_c, c in process_coords(coords, h, v):    
            p_x1, p_y1, p_x2, p_y2 = p_c
            x1, y1, x2, y2 = c
            roi=img[p_y1:p_y2, p_x1:p_x2]
            fid = fid + 1
            path = folder + str(fid) + '.jpg'
            pathlist.append((path, p_c, c, (x1+((x2-x1)//2), y1 + ((y2-y1)//2))))
            # Write subimage to file
            cv2.imwrite(path, roi)  
        
    return pathlist 
    
"""
Processing coordinates to filter out regions which should not be included, as well as
clustering regions using groupRectangles
h = horizontal length of the panorama image
v = vertical length of the panorama image
"""    
def process_coords(coords, h, v):
    # Padding coefficient (x * p = padded_x). 1 <= p < = 2.
    # e.g. p = 1.65 = 65% increase
    p = 1.65
    
    grouplist = filter(lambda x: utils.region_filter(x, h, v), coords)
    # We duplicate each entry in grouplist so groupRectangles will work properly
    grouplist = grouplist + grouplist    
    grouplist = map(lambda x: [ int(y) for y in x ], cv2.groupRectangles(grouplist, 1, 0.05)[0])   
    rectlist = map(lambda x: (utils.pad_box(x, h, v, p), tuple(x)), grouplist)      
    return rectlist
    
    
"""
Fetches panorama image from S3 online storage
"""
def get_image(filename):
    s3 = boto3.client('s3')
    utils.update_progress('Downloading Image')
    s3.download_file(os.environ.get("S3_BUCKET"), filename, 'uploads/' + filename)
    return cv2.imread('uploads/' + filename)
    
"""
Uploads the resulting processed image to S3 for debugging/presenting to users to show the
work the server did in identifying regions
"""    
def upload_result(filename):
    s3 = boto3.client('s3')
    s3.upload_file('uploads/result.jpg', os.environ.get("S3_BUCKET"), 'results/' + filename, {'ACL': 'public-read'}) 
    url = '{}/{}/{}'.format(s3.meta.endpoint_url, os.environ.get("S3_BUCKET"), 'results/' + filename)   
    utils.set_url(url) 

"""
Clearing the temporary cache used to hold our subimages (in this implementation, uses
the system's /tmp/ folder).
"""
def clear_cache():
    utils.update_progress('Clearing Cache')
    files = glob('/tmp/*.jpg')
    for f in files:
        os.remove(f)

"""
MSER Detection is done here. Parameters are listed:
MSER(delta, min_area, max_area, max_variation, 
    min_diversity, max_evolution, area_threshold, min_margin, edge_blur_size)  

_delta 
    Compares (sizei - sizei-delta)/sizei-delta. The parameter delta indicates 
    through how many different gray levels does a region need to be stable to 
    be considered maximally stable. For a larger delta, you will get less regions.
_min_area 
    Prune the area which smaller than minArea
_max_area  
    Prune the area which bigger than maxArea
_max_variation 
    Prune the area have simliar size to its children. For smaller maxVariation, 
    you will get less regions
_min_diversity 
    For color image, trace back to cut off mser with diversity less than min_diversity.
    For larger diversity, you will get less regions.
_max_evolution 
    For color image, the evolution steps. For larger max_evolution, you will get more 
    regions
_area_threshold 
    For color image, the area threshold to cause re-initialize
_min_margin 
    For color image, ignore too small margin
_edge_blur_size 
    For color image, the aperture size for edge blur

"""
def mser_detect(img, x_len, y_len):
    utils.update_progress('Detecting Regions')
    
    min_t = int(math.floor((y_len*x_len)*0.0009))
    max_t = int(math.floor((y_len*x_len)*0.05))
    
    #MSER(5, 60, 14400, 0.25, 0.2, 200, 1.01, 0.003, 5)  <- Default Values
    c_mser = cv2.MSER(5, min_t, max_t, 0.166, 0.153, 90, 1.001, 0.003, 5)
    c_regions = c_mser.detect(img, None)
    return [cv2.convexHull(p.reshape(-1, 1, 2)) for p in c_regions]
    
    
# Main Function    
"""
This is the MAIN PROCESS function which runs during worker operation. This is
considered the PARENT thread. Takes in input filename to fetch from S3 server, and
does all image processing and handling in this function.
"""
def k(x):
    print x


def run_process(filename, DEBUG=False):
    # Fetch Image from S3
    img = get_image(filename)
    
    #Clear the subimages cache
    clear_cache()

    # Get dimensions of image
    x_len = img.shape[1]
    y_len = img.shape[0]  

    # MSER Region Detection    
    hulls = mser_detect(img, x_len, y_len)
    
    #Generate the subimages from the regions and image
    pathlist = generate_subimages(hulls, img, x_len, y_len)      
    
    # API Object Recognition Results
    results = {} if DEBUG == True else vision_api_handler.get_results()  
    
    print pathlist
    
    """return_result = map(lambda y: {'status':results[y[0]][0], 
                                    'data':{
                                        'cloudsight':results[y[0]][1],
                                        'msft' : results[y[0]][2],
                                        'ibm' : "",
                                        'google': "",
                                        'padded_coords':y[1],
                                        'coords':y[2], 
                                        'center':y[3]
                                        }
                                     }, 
                    filter(lambda x: k(x), pathlist))"""
    

    # Printing results for show
    cv2.polylines(img, hulls, 1, (0, 255, 0))
    
    # Places rectangles and text on regions onto the image.
    
    
    for x in pathlist:
        x1, y1, x2, y2 = x[2]
        center = x[3]
        cv2.circle(img, center, 3, (255, 255, 255), 2)
        if x[0] in results:
            data = results[x[0]]['cloudsight']
            if data[0] == 'completed':
                cv2.rectangle(img,(x1, y1),(x2, y2),(255,0,0),2)
                
            else:
                cv2.rectangle(img,(x1, y1),(x2, y2),(0,0,255),2)
                
                
            t_x, t_y = cv2.getTextSize(data[1], cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            overlay = img.copy()
            x_adj = max(0, (x1 + t_x) - x_len)
            cv2.rectangle(overlay, (x1 - x_adj, y1),((x1 + t_x)-x_adj, y1 + t_y + 8),(0,0,0),-1)
            cv2.addWeighted(overlay, 0.5, img, 1.0 - 0.5, 0, img)   
             
            cv2.putText(img, data[1], (x1-x_adj, y1+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                (255,255,255), 1, cv2.CV_AA)
                    
        else:
            cv2.rectangle(img,(x1, y1),(x2, y2),(255,0,0),2)
    
    cv2.imwrite('uploads/result.jpg', img)
    
    # Upload result processed image to S3
    upload_result(filename.split('.')[0]+'.jpg')
       
    # Set flag to Finished for job
    utils.set_finished()
    
    # Return the results.
    return results

