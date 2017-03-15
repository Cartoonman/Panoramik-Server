#!/usr/bin/env python

import cv2
import math
import sys
import cloudsight
import pickle
import subprocess
import os, glob


# Utility Functions

def mapx(x):
    return x[0][0]

def mapy(x):
    return x[0][1]

"""
Returns list of hull data as well as edge coordinates for bounding rectangle calculation
"""
def edge_coordinates(hulls):
    return map(lambda x: (x, sorted(map(mapx,x))[0], sorted(map(mapy,x))[0], sorted(map(mapx,x),reverse=True)[0], sorted(map(mapy,x),reverse=True)[0]), hulls)
    
    
"""
Returns list of hull data as well as edge coordinates for bounding rectangle calculation
"""  
padding = 1.15
horizlen = 0
vertilen = 0

def generate_subimages(hulls, img, c_vis=None):
    coords = edge_coordinates(hulls)
    fid = 0 
    pathlist = []
    
    for x in coords:
        fid += 1
        minx = x[1] - (int(x[1]*padding) - x[1])
        maxx = int(x[3]*padding)
        miny = x[2] - (int(x[2]*padding) - x[2])
        maxy = int(x[4]*padding)

        roi=img[max(miny, 0):max(miny, 0)+(maxy-miny),max(minx,0):max(minx,0)+(maxx-minx)]

        if (x[4]-x[2] > int(vertilen *.45)) or (x[3]-x[1] > int(horizlen *.45)):
            continue
        #cv2.rectangle(c_vis,(max(x[1],0),max(x[2],0)),(max(x[1],0)+(x[3]-x[1]), max(x[2],0)+(x[4]-x[2])),(255,0,0),2)
        path = '/tmp/' + str(fid) + '.jpg'
        pathlist.append((path,(x[1],x[3],x[2],x[4])))
        cv2.imwrite(path, roi)  
        
    return pathlist  
    
    #print map(lambda x: x[1], top_regions) #min X
    #print map(lambda x: x[2], top_regions) #min Y
    #print map(lambda x: x[3], top_regions) #max X
    #print map(lambda x: x[4], top_regions) #max Y
    
    
def run(filepath, BASE_DIR):
    #File Input
    img = cv2.imread(filepath)
    
    files = glob.glob('/tmp/*.jpg')
    for f in files:
        os.remove(f)

    # Initializing MSER

    

    # Get maximum and minimum
    maxthres=int(math.floor((img.shape[0]*img.shape[1])*0.05))
    minthres=int(math.floor((img.shape[0]*img.shape[1])*0.0009))
    global horizlen
    global vertilen
    horizlen = img.shape[1]
    vertilen = img.shape[0]
    print img.shape[0]*img.shape[1]
    print maxthres
    print minthres


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~COLOR MSER
    #c_mser = cv2.MSER_create(5, 60, 14400, 0.25, 0.2, 200, 1.01, 0.003, 5)  #<- Default
    c_mser = cv2.MSER(5, minthres, maxthres, 0.166, 0.153, 90, 1.001, 0.003, 5)

    c_vis = img.copy()
  

    #COLOR MSER
    c_regions = c_mser.detect(img, None)
    c_hulls = [cv2.convexHull(p.reshape(-1, 1, 2)) for p in c_regions]
    
    #pathlist = generate_subimages(c_hulls,img,c_vis) #DEBUG
    pathlist = generate_subimages(c_hulls,img) #NONDEBUG
   
    #print pathlist

    """ THIS IS EXPERIMENTAL FROM THIS POINT ON """
    # Finding duplicates and pruning them
    subprocess.call(["python", os.path.join(BASE_DIR,"src/similarity.py"),'phash', '/tmp/'], )
    print 'CSDELE'
    # cloudsight result getter
    subprocess.call(["python", os.path.join(BASE_DIR,"src/csdele.py")], )

    results = pickle.load( open( "output.txt", "rb" ) )

    print results
    
    
    
    # Printing results for show
    
    cv2.polylines(c_vis, c_hulls, 1, (0, 255, 0))
    #cv2.polylines(c_vis, map(lambda x: x[1], top_regions), 1, (0, 0, 255))
    font = cv2.FONT_HERSHEY_SIMPLEX
    for x in pathlist:
        if x[0] in results:
            rc = x[1]
            cv2.rectangle(c_vis,(max(rc[0],0),max(rc[2],0)),(max(rc[0],0)+(rc[1]-rc[0]), max(rc[2],0)+(rc[3]-rc[2])),(255,0,0),2)
            cv2.putText(c_vis,results[x[0]][0] + ' : ' + results[x[0]][1],(rc[0],rc[2]+10), font,0.7,(255,255,255),1,cv2.CV_AA)


    #cv2.imshow('img',c_vis)
    #cv2.waitKey(0)  

    #cv2.rectangle(c_vis,(x,y),(x+w,y+h),(255,0,0),2)
    print BASE_DIR
    cv2.imwrite(BASE_DIR + '/uploads/result.jpg', c_vis)
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




