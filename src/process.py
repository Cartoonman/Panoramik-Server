#!/usr/bin/env python

import cv2
import math
import sys
import subprocess
import os
from glob import glob
import boto3
from utils import initialize_progress, update_progress, mapx, mapy
from cloudsight_handler import get_results
from dup_filter import filter_duplicates

# Utility Functions
"""
Returns list of hull data as well as edge coordinates for bounding rectangle calculation
"""
def edge_coordinates(hulls):
    return map(lambda c: (c, sorted(map(mapx,c))[0], sorted(map(mapy,c))[0], sorted(map(mapx,c),reverse=True)[0], sorted(map(mapy,c),reverse=True)[0]), hulls)
    
    
"""
Returns list of hull data as well as edge coordinates for bounding rectangle calculation
"""  
def generate_subimages(hulls, img, h, v):
    update_progress('Extracting Regions')
    padding = 1.15
    fid = 0 
    pathlist = []
    
    coords = edge_coordinates(hulls)
    
    for c in coords:
        if  (c[3]-c[1] > int(h *.45)) or (c[4]-c[2] > int(v *.45)):
            continue
        #if c_vis is not None:
        #    cv2.rectangle(c_vis,(max(c[1],0),max(c[2],0)),(max(c[1],0)+(c[3]-c[1]), max(c[2],0)+(c[4]-c[2])),(255,0,0),2)
        fid += 1
        minx = c[1] - (int(c[1]*padding) - c[1])
        maxx = int(c[3]*padding)
        miny = c[2] - (int(c[2]*padding) - c[2])
        maxy = int(c[4]*padding)

        roi=img[max(miny, 0):max(miny, 0)+(maxy-miny),max(minx,0):max(minx,0)+(maxx-minx)]

        path = '/tmp/' + str(fid) + '.jpg'
        pathlist.append((path,(c[1],c[3],c[2],c[4]))) # (min_x, max_x, min_y, max_y) no padding
        cv2.imwrite(path, roi)  
        
    return pathlist 
    

def get_image(filename, UPLOAD_FOLDER):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    s3 = boto3.client('s3')
    update_progress('Downloading Image')
    s3.download_file(os.environ.get("S3_BUCKET"), filename, filepath)
    return cv2.imread(filepath)

def clear_cache():
    update_progress('Clearing Cache')
    files = glob('/tmp/*.jpg')
    for f in files:
        os.remove(f)

def mser_detect(img, x_len, y_len):
    update_progress('Detecting Regions')
    
    min_t = int(math.floor((y_len*x_len)*0.0009))
    max_t = int(math.floor((y_len*x_len)*0.05))
    
    #c_mser = cv2.MSER(5, 60, 14400, 0.25, 0.2, 200, 1.01, 0.003, 5)  #<- Default
    c_mser = cv2.MSER(5, min_t, max_t, 0.166, 0.153, 90, 1.001, 0.003, 5)
    c_regions = c_mser.detect(img, None)
    return [cv2.convexHull(p.reshape(-1, 1, 2)) for p in c_regions]
    
    

def run(filename, UPLOAD_FOLDER, BASE_DIR):

    initialize_progress()  
    img = get_image(filename, UPLOAD_FOLDER)
    
    clear_cache()

    # Get dimensions of image
    x_len = img.shape[1]
    y_len = img.shape[0]  

    # MSER Region Detection
    
    hulls = mser_detect(img, x_len, y_len)

    pathlist = generate_subimages(hulls, img, x_len, y_len) 
      
    # Duplicate Removal
    filter_duplicates()
    
    # Cloudsight Results
    results = get_results()
    
 
    # Printing results for show
    cv2.polylines(img, hulls, 1, (0, 255, 0))
    #cv2.polylines(c_vis, map(lambda x: x[1], top_regions), 1, (0, 0, 255))
    font = cv2.FONT_HERSHEY_SIMPLEX
    for x in pathlist:
        if x[0] in results:
            rc = x[1]
            cv2.rectangle(img,(max(rc[0],0),max(rc[2],0)),(max(rc[0],0)+(rc[1]-rc[0]), max(rc[2],0)+(rc[3]-rc[2])),(255,0,0),2)
            cv2.putText(img,results[x[0]][0] + ' : ' + results[x[0]][1],(rc[0],rc[2]+15), font,0.7,(255,255,255),1,cv2.CV_AA)


    #cv2.imshow('img',c_vis)
    #cv2.waitKey(0)  

    #cv2.rectangle(c_vis,(x,y),(x+w,y+h),(255,0,0),2)
    print BASE_DIR
    cv2.imwrite(BASE_DIR + '/uploads/result.jpg', img)
    return results
    #return {}

   
"""
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~GREYSCALE (SINGLE CHANNEL) MSER

#g_mser = cv2.MSER_create(5, 500, 14400, 0.25, 0.2) #<- Default

g_mser = cv2.MSER(5, minthres, maxthres, 0.25, 0.2) 





gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)



g_vis = img.copy()





#GRAYSCALE MSER

g_regions = g_mser.detect(gray, None)

g_hulls = [cv2.convexHull(p.reshape(-1, 1, 2)) for p in g_regions]



top_regions = sorted(map(lambda x: (PolyArea(np.array(map(mapx,x)), np.array(map(mapy,x))), x, sorted(map(mapx,x))[0], sorted(map(mapx,x),reverse=True)[0]), g_hulls), key=lambda y: y[0], reverse=True)[:5]

#top_regions sample output: (area, numpy_array(region), min x coord, max x coord)



cv2.polylines(g_vis, g_hulls, 1, (0, 255, 0))

cv2.polylines(g_vis, map(lambda x: x[1], top_regions), 1, (0, 0, 255))





cv2.imwrite('/media/sf_Ubuntu_Shared/g_result.jpg', g_vis)







#cv2.imshow('img', vis)

#cv2.waitKey()



cv2.destroyAllWindows()

"""




