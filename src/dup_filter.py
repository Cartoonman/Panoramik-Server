from __future__ import division
import os
from PIL import Image
import imagehash
import vptree
from utils import allowed_file, update_progress, hamming, merge, image_size
from glob import glob


error_bounds = 17

def filter_duplicates():
    update_progress('Pruning Duplicates')

    image_filenames = [filename for filename in glob('/tmp/*.jpg')]
    
    images = dict(map(lambda x: (str(imagehash.phash(Image.open(x))), x), image_filenames))
    
    points = map(lambda x: vptree.NDPoint(x, images[x]), images)
    
    tree = vptree.VPTree(points, hamming)
    
    neighbors = map(lambda a: map(lambda y: str(y[1].x), vptree.get_all_in_range(tree,a,error_bounds)), points)
       
    setlist = merge(map(lambda x: map(lambda y: images[y], x), neighbors))
    
    for x in setlist:
        if len(x) == 1:
            continue
        image_array = sorted([(image_size(Image.open(f, 'r')), f) for f in x], key=lambda x: x[0], reverse=True)[1:]
        for x in image_array:
            os.remove(x[1]) 



    
