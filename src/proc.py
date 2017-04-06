#!/usr/bin/env python
from __future__ import division
import cv2
import math
import os
from glob import glob
import boto3
import utils
from cloudsight_handler import get_results

# Utility Functions
"""
Returns list of hull data as well as edge coordinates for bounding rectangle calculation
"""
def edge_coordinates(hulls):
    return map(lambda c: (c, sorted(map(utils.mapx,c))[0], sorted(map(utils.mapy,c))[0], sorted(map(utils.mapx,c),reverse=True)[0], sorted(map(utils.mapy,c),reverse=True)[0]), hulls)
    
    
"""
Returns list of hull data as well as edge coordinates for bounding rectangle calculation
"""  
def generate_subimages(hulls, img, h, v, folder = '/tmp/'):
    utils.update_progress('Extracting Regions')
    fid = 0 
    pathlist = []
    
    coords = edge_coordinates(hulls)
    if len(coords) == 0:
        cv2.imwrite('/tmp/image.jpg', img)  
        pathlist.append(('/tmp/image.jpg', (0,h,0,v)))
        return pathlist
    for rect, c in process_coords(coords,h,v, img):       
        x1,y1,x2,y2 = rect
        #cv2.rectangle(img,(int(x),int(y)),(int(wi),int(hi)),(255,0,0),2)
        roi=img[y1:y2,x1:x2]
        fid = fid + 1
        path = folder + str(fid) + '.jpg'
        pathlist.append((path,(c[0],c[1],c[2],c[3]))) # (min_x, max_x, min_y, max_y) no padding
        cv2.imwrite(path, roi)  
        
    return pathlist 
    
"""
Processing coordinates to filter out regions which should not be included, as well as
clustering regions using groupRectangles
"""    
def process_coords(coords, h, v, img):

    padding = 1.65
    validlist = []
    for c in coords:
        if  (c[3]-c[1] > int(h *.45)) or (c[4]-c[2] > int(v *.45)) or (min(c[4]-c[2],c[3]-c[1])/max(c[4]-c[2],c[3]-c[1]) < 0.25):
            continue  
        validlist.append([int(c[1]),int(c[2]),int(c[3]-c[1]),int(c[4]-c[2])])

    validlist = validlist + validlist
    grplst, _ = cv2.groupRectangles(validlist, 1)
    validlist = []
    for c in grplst:
        x1 = int(c[0])
        y1 = int(c[1])
        x2 = int(c[2]+c[0])
        y2 = int(c[3]+c[1])
             
        width = x2-x1
        height = y2-y1
        
        new_width = width*padding
        new_height = height*padding
        
        w_delta = new_width - width
        h_delta = new_height - height
        delta = max(w_delta//2, h_delta//2)
        minx = int(max(x1 - delta, 0))
        maxx = int(min(x2 + delta, h))
        miny = int(max(y1 - delta, 0))
        maxy = int(min(y2 + delta, v))
    

        validlist.append([[minx, miny, maxx, maxy],
            [x1, y1, x2, y2]]) #[(x1,y1, w, h)],[(P1),(P2)]
    
    return validlist
    
    
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
    s3.upload_file('uploads/result.jpg', os.environ.get("S3_BUCKET"), 'results/' + filename)    

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
    
    #c_mser = cv2.MSER(5, 60, 14400, 0.25, 0.2, 200, 1.01, 0.003, 5)  #<- Default Values
    c_mser = cv2.MSER(5, min_t, max_t, 0.166, 0.153, 90, 1.001, 0.003, 5)
    c_regions = c_mser.detect(img, None)
    return [cv2.convexHull(p.reshape(-1, 1, 2)) for p in c_regions]
    
    
# Main Function    
"""
This is the MAIN PROCESS function which runs during worker operation. This is
considered the PARENT thread. Takes in input filename to fetch from S3 server, and
does all image processing and handling in this function.
"""
def run_process(filename):
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
    
    # Cloudsight Results
    results = get_results()  
 
    # Printing results for show
    cv2.polylines(img, hulls, 1, (0, 255, 0))
    
    # Places rectangles and text on regions onto the image.
    for x in pathlist:
        if x[0] in results:
            if results[x[0]][0] == 'completed':
                rc = x[1]
                cv2.rectangle(img,(rc[0],rc[1]),(rc[2],rc[3]),(255,0,0),2)
                cv2.putText(img, results[x[0]][1], (rc[0],rc[1]+15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.CV_AA)
            else:
                rc = x[1]
                cv2.rectangle(img,(rc[0],rc[1]),(rc[2],rc[3]),(0,0,255),2)
                cv2.putText(img, results[x[0]][1], (rc[0],rc[1]+15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.CV_AA)

    #cv2.rectangle(c_vis,(x,y),(x+w,y+h),(255,0,0),2)
    cv2.imwrite('uploads/result.jpg', img)
    
    # Upload result processed image to S3
    upload_result(filename)
    
    # Set flag to Finished for job
    utils.set_finished()
    
    # Return the results.
    return results






