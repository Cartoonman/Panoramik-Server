from __future__ import (absolute_import, division, print_function)
import os
from PIL import Image
import six
from collections import defaultdict
import imagehash
import subprocess
from numpy import array
from utils import allowed_file, update_progress
from glob import glob


error_bounds = 17

def filter_duplicates():
    update_progress('Pruning Duplicates')
    hashfunc = imagehash.phash
    
    image_filenames = [filename for filename in glob('/tmp/*.jpg')]
    images = {}
    images2 = defaultdict(set)
    for img in sorted(image_filenames):
        h = hashfunc(Image.open(img))
        for x in images.keys():
            if hamming(str2hex(x),str2hex(str(h))) < error_bounds:
                images2[str(h)].add(img)
                images2[str(h)].add(images[x][0])
        
            #print(hamming(str2hex(x),str2hex(str(h))))
        images[str(h)] = images.get(str(h), []) + [img]
        
    setlist = []
    for k, img_list in six.iteritems(images2):
        setlist = inset(setlist, img_list)
    print('_________________________________')
    #indy = 0 DEBUG
    # subprocess.call(['./test.sh', str(len(setlist))]) #DEBUG _ set up temporary folders for processing
    for x in setlist:
        image_array = sorted([(reduce(lambda x,y: x*y, Image.open(f, 'r').size), f) for f in x], key=lambda x: x[0], reverse=True)
        maximg = image_array[0]
        print (image_array)
        for x in image_array:
            if x != maximg:
                try:
                    print('REMOVING', x[1])
                    os.remove(x[1]) 
                except OSError as e:
                    print (e)
                    pass
        #indy = indy+1 DEBUG
        """for y in x:
            try:
                os.rename(y, "tmp/sort/" + str(indy) + "/" + y.split('/')[1])
            except OSError:
                pass"""


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

def inset(x,y):
    for a in x:
        for z in y:
            if z in a:
                for d in y:
                    a.add(d)
                return x
    x.append(y)
    return x

def str2hex(x):

    scale = 16 ## equals to hexadecimal

    num_of_bits = 64

    return bin(int(x, scale))[2:].zfill(num_of_bits)



def hamming(x,y):
    """Calculate the Hamming distance between two bit strings"""
    assert len(x) == len(y)
    count,z = 0,int(x,2)^int(y,2)
    while z:
        count += 1
        z &= z-1 # magic!
    return count

    
    
