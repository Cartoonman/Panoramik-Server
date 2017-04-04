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
        x,y,wi,hi = rect
        #cv2.rectangle(img,(int(x),int(y)),(int(wi),int(hi)),(255,0,0),2)
        roi=img[y:hi,x:wi]
        fid = fid + 1
        path = folder + str(fid) + '.jpg'
        pathlist.append((path,(x,y,wi,hi))) # (min_x, max_x, min_y, max_y) no padding
        cv2.imwrite(path, roi)  
        
    return pathlist 
    
def process_coords(coords,h,v, img):

    padding = 1.65
    validlist = []
    for c in coords:
        #minx = c[1] - (int(c[1]*padding) - c[1])
        #maxx = minx + int((c[3]-c[1])*padding)
        #miny = c[2] - (int(c[2]*padding) - c[2])
        #maxy = miny + int((c[4]-c[2])*padding)
        
        if  (c[3]-c[1] > int(h *.45)) or (c[4]-c[2] > int(v *.45)) or (min(c[4]-c[2],c[3]-c[1])/max(c[4]-c[2],c[3]-c[1]) < 0.25):
            continue  
        validlist.append([int(c[1]),int(c[2]),int(c[3]-c[1]),int(c[4]-c[2])])

    validlist = validlist + validlist
    grplst, _ = cv2.groupRectangles(validlist, 1)
    #grplst = validlist
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
    
    
        """minx = c[0] - (int(c[0]*padding) - c[0])
        maxx = minx + int((c[2])*padding)
        miny = c[1] - (int(c[1]*padding) - c[1])
        maxy = miny + int((c[3])*padding)
            
        width = min(maxx,h)
        height = min(maxy,v)
        x_c = max(minx,0)
        y_c = max(miny,0)"""

        validlist.append([[minx, miny, maxx, maxy],[c[0],c[1],c[2]+c[0],c[3]+c[1]]]) #[(x1,x1, w,h)],[(P1),(P2)]
    
    return validlist
    
    

def get_image(filename):
    s3 = boto3.client('s3')
    utils.update_progress('Downloading Image')
    s3.download_file(os.environ.get("S3_BUCKET"), filename, 'uploads/' + filename)
    return cv2.imread('uploads/' + filename)
    
def upload_result(filename):
    s3 = boto3.client('s3')
    s3.upload_file('uploads/result.jpg', os.environ.get("S3_BUCKET"), 'results/' + filename)    

def clear_cache():
    utils.update_progress('Clearing Cache')
    files = glob('/tmp/*.jpg')
    for f in files:
        os.remove(f)

def mser_detect(img, x_len, y_len):
    utils.update_progress('Detecting Regions')
    
    min_t = int(math.floor((y_len*x_len)*0.0009))
    max_t = int(math.floor((y_len*x_len)*0.05))
    
    #c_mser = cv2.MSER(5, 60, 14400, 0.25, 0.2, 200, 1.01, 0.003, 5)  #<- Default
    c_mser = cv2.MSER(5, min_t, max_t, 0.166, 0.153, 90, 1.001, 0.003, 5)
    c_regions = c_mser.detect(img, None)
    return [cv2.convexHull(p.reshape(-1, 1, 2)) for p in c_regions]
    
    

def run_process(filename):
    img = get_image(filename)
    
    clear_cache()

    # Get dimensions of image
    x_len = img.shape[1]
    y_len = img.shape[0]  

    # MSER Region Detection
    
    hulls = mser_detect(img, x_len, y_len)
 
    pathlist = generate_subimages(hulls, img, x_len, y_len) 
      
    
    # Cloudsight Results
    results = get_results()
    
 
    # Printing results for show
    cv2.polylines(img, hulls, 1, (0, 255, 0))
    #cv2.polylines(c_vis, map(lambda x: x[1], top_regions), 1, (0, 0, 255))
    font = cv2.FONT_HERSHEY_SIMPLEX #UNCOMMENT THIS WHEN READY TO PUT TO SERVER
    for x in pathlist:
        if x[0] in results:
            rc = x[1]
            cv2.rectangle(img,(int(rc[0]),int(rc[1])),(int(rc[2]),int(rc[3])),(255,0,0),2)
            cv2.putText(img,results[x[0]][0] + ' : ' + results[x[0]][1],(int(rc[0]),int(rc[1])+15), font, 0.7,(255,255,255),1,cv2.CV_AA)

    
    #cv2.imshow('img',c_vis)
    #cv2.waitKey(0)  

    #cv2.rectangle(c_vis,(x,y),(x+w,y+h),(255,0,0),2)
    cv2.imwrite('uploads/result.jpg', img)
    upload_result(filename)
    utils.set_finished()
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



top_regions = sorted(map(lambda x: (PolyArea(np.array(map(utils.mapx,x)), np.array(map(utils.mapy,x))), x, sorted(map(utils.mapx,x))[0], sorted(map(utils.mapx,x),reverse=True)[0]), g_hulls), key=lambda y: y[0], reverse=True)[:5]

#top_regions sample output: (area, numpy_array(region), min x coord, max x coord)



cv2.polylines(g_vis, g_hulls, 1, (0, 255, 0))

cv2.polylines(g_vis, map(lambda x: x[1], top_regions), 1, (0, 0, 255))





cv2.imwrite('/media/sf_Ubuntu_Shared/g_result.jpg', g_vis)







#cv2.imshow('img', vis)

#cv2.waitKey()



cv2.destroyAllWindows()

"""




