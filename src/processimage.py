#!/usr/bin/env python



import numpy as np
import cv2
import math
import sys
import cloudsight
import pickle
import subprocess
import os, glob


def mapx(x):
    return x[0][0]

def mapy(x):
    return x[0][1]

def PolyArea(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))


def run(filepath, BASE_DIR):

    #File Input
    img = cv2.imread(filepath)
    
    
    files = glob.glob('/tmp/*')

    for f in files:
        os.remove(f)

    

    

    # Initializing MSER

    

    # Get maximum and minimum
    maxthres=int(math.floor((img.shape[0]*img.shape[1])*0.004))
    minthres=int(math.floor((img.shape[0]*img.shape[1])*0.0009))
    print img.shape[0]*img.shape[1]
    print maxthres
    print minthres

    

    

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~COLOR MSER

    #c_mser = cv2.MSER_create(5, 60, 14400, 0.25, 0.2, 200, 1.01, 0.003, 5)  #<- Default
    c_mser = cv2.MSER(5, minthres, maxthres, 0.25, 0.2, 200, 1.01, 0.009, 5)

    

    c_vis = img.copy()

    

    #COLOR MSER

    c_regions = c_mser.detect(img, None)
    c_hulls = [cv2.convexHull(p.reshape(-1, 1, 2)) for p in c_regions]

    

    top_regions = sorted(map(lambda x: (PolyArea(np.array(map(mapx,x)), np.array(map(mapy,x))), x, sorted(map(mapx,x))[0], sorted(map(mapy,x))[0], sorted(map(mapx,x),reverse=True)[0], sorted(map(mapy,x),reverse=True)[0]), c_hulls), key=lambda y: y[0], reverse=True)

    

    

    n = 1.15

    

    

    idx = 0 

    pathlist = []

    for x in top_regions:

        idx += 1

        minx = x[2] - (int(x[2]*n) - x[2])

        maxx = int(x[4]*n)

        miny = x[3] - (int(x[2]*n) - x[2])

        maxy = int(x[5]*n)

        cv2.rectangle(c_vis,(max(minx,0),max(miny,0)),(max(minx,0)+(maxx-minx), max(miny,0)+(maxy-miny)),(255,0,0),2)

        

        roi=img[max(miny, 0):max(miny, 0)+(maxy-miny),max(minx,0):max(minx,0)+(maxx-minx)]

        path = '/tmp/' + str(idx) + '.jpg'

        pathlist.append((path,(max(minx,0),max(miny,0))))

        cv2.imwrite(path, roi)

    

    

    print pathlist

    #print map(lambda x: x[2], top_regions) #min X

    #print map(lambda x: x[3], top_regions) #min Y

    #print map(lambda x: x[4], top_regions) #max X

    #print map(lambda x: x[5], top_regions) #max Y

    

    

    

    """ THIS IS EXPERIMENTAL FROM THIS POINT ON """

    

    subprocess.call(["python", os.path.join(BASE_DIR,"src/similarity.py"),'phash', '/tmp/'], )
    print 'CSDELE'
    subprocess.call(["python", os.path.join(BASE_DIR,"src/csdele.py")], )

    

    results = pickle.load( open( "output.txt", "rb" ) )

    

    print results

    

    cv2.polylines(c_vis, c_hulls, 1, (0, 255, 0))

    #cv2.polylines(c_vis, map(lambda x: x[1], top_regions), 1, (0, 0, 255))

    font = cv2.FONT_HERSHEY_SIMPLEX

    for x in pathlist:

        if x[0] in results:

            cv2.putText(c_vis,results[x[0]][0] + ' ' + results[x[0]][1],x[1], font,0.7,(255,255,255),1,cv2.CV_AA)

    

    #cv2.imshow('img',c_vis)
    #cv2.waitKey(0)  

    

    #cv2.rectangle(c_vis,(x,y),(x+w,y+h),(255,0,0),2)

    

    cv2.imwrite('uploads/result.jpg', c_vis)

    return results

   
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


