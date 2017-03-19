from PIL import Image
from shutil import copyfile
import imagehash
import subprocess
import os
import sys
import cv2
import shutil
import src.proc as proc
import src.utils as utils
import src.vptree as vptree
from glob import glob

"""
Demo of hashing
"""
error_bounds = 16

if __name__ == '__main__':
    if not os.path.exists('tmp/'):
        os.makedirs('tmp/')
    else:
        shutil.rmtree('tmp/')
        os.makedirs('tmp/')
    img = cv2.imread(sys.argv[1])    
    

    # Get dimensions of image
    x_len = img.shape[1]
    y_len = img.shape[0]  

    # MSER Region Detection
    
    hulls = proc.mser_detect(img, x_len, y_len)

    pathlist = proc.generate_subimages(hulls, img, x_len, y_len, 'tmp/') 

    image_filenames = [filename for filename in glob('tmp/*.jpg')]
    
    images = dict(map(lambda x: (str(imagehash.phash(Image.open(x),8,4)), x), image_filenames))
    
    points = map(lambda x: vptree.NDPoint(x, images[x]), images)
    
    tree = vptree.VPTree(points, utils.hamming)
    
    for x in sorted(images, key=lambda x: images[x]):
        print x + " : " + images[x] + " - " + str(sorted(map(lambda x: (x[0], x[1].idx), vptree.get_all_in_range(tree,vptree.NDPoint(x, images[x]),100)), key=lambda x: x[0]))
    
    neighbors = map(lambda a: map(lambda y: str(y[1].x), vptree.get_all_in_range(tree,a,error_bounds)), points)
       
    setlist = utils.merge(map(lambda x: map(lambda y: images[y], x), neighbors))
    
    setlist = filter(lambda x: len(x) != 1, setlist)
    subprocess.call(['./phash_test_setup.sh', str(len(setlist))]) #DEBUG _ set up temporary folders for processing
    
    indy = 0 
    for x in setlist:
        indy = indy+1
        for y in x:
            shutil.copyfile(y, "tmp/sort/" + str(indy) + "/" + y.split('/')[1])
