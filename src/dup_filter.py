from __future__ import (division, print_function)
import os
from PIL import Image
import six
from collections import defaultdict
import imagehash
import vptree
import subprocess
from numpy import array
from utils import allowed_file, update_progress, hamming
from glob import glob


error_bounds = 17

def filter_duplicates():
    update_progress('Pruning Duplicates')
    hashfunc = imagehash.phash
    
    image_filenames = [filename for filename in glob('/tmp/*.jpg')]
    
    images = dict(map(lambda x: (str(hashfunc(Image.open(x))), x), image_filenames))
    
    points = map(lambda x: vptree.NDPoint(x, images[x]), images)
    
    tree = vptree.VPTree(points, hamming)
    
    neighbors = map(lambda a: map(lambda y: str(y[1].x), vptree.get_all_in_range(tree,a,17)), points)
    
    print (neighbors)
    
    setlist = merge(map(lambda x: map(lambda y: images[y], x), neighbors))
    
    print (setlist)

    for x in setlist:
        if len(x) == 1:
            continue
        image_array = sorted([(reduce(lambda x,y: x*y, Image.open(f, 'r').size), f) for f in x], key=lambda x: x[0], reverse=True)
        maximg = image_array[0]
        print (image_array)
        for x in image_array:
            if x != maximg:
                print('REMOVING', x[1])
                os.remove(x[1]) 


def merge(lsts):
    sets = [set(lst) for lst in lsts if lst]
    merged = 1
    while merged:
        merged = 0
        results = []
        while sets:
            common, rest = sets[0], sets[1:]
            sets = []
            for x in rest:
                if x.isdisjoint(common):
                    sets.append(x)
                else:
                    merged = 1
                    common |= x
            results.append(common)
        sets = results
    return sets
    
