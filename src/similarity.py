#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)

from PIL import Image

import six

import Levenshtein

from collections import defaultdict

import imagehash

import subprocess

from numpy import array



"""

Demo of hashing

"""

def find_similar_images(userpath, hashfunc = imagehash.average_hash):

    import os

    def is_image(filename):

        f = filename.lower()

        return f.endswith(".png") or f.endswith(".jpg") or \

            f.endswith(".jpeg") or f.endswith(".bmp") or f.endswith(".gif")

    

    image_filenames = [os.path.join(userpath, path) for path in os.listdir(userpath) if is_image(path)]

    images = {}

    images2 = defaultdict(set)

    for img in sorted(image_filenames):

        h = hashfunc(Image.open(img))

        for x in images.keys():

            if hamming(str2hex(x),str2hex(str(h))) < 17:

                images2[str(h)].add(img)

                images2[str(h)].add(images[x][0])

        

            #print(hamming(str2hex(x),str2hex(str(h))))

        images[str(h)] = images.get(str(h), []) + [img]

        

        

    for k, img_list in six.iteritems(images):

        if len(img_list) > 1:

            print(" ".join(img_list))

            #lv = Levenshtein.distance(img_list[0], img_list[1])

    print('_________________________________')

    for k, img_list in six.iteritems(images2):

        print(" ".join(img_list))

        #lv = Levenshtein.distance(img_list[0], img_list[1])

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





if __name__ == '__main__':

    import sys, os

    def usage():

        sys.stderr.write("""SYNOPSIS: %s [ahash|phash|dhash|...] [<directory>]



Identifies similar images in the directory.



Method: 

  ahash:      Average hash

  phash:      Perceptual hash

  dhash:      Difference hash

  whash-haar: Haar wavelet hash

  whash-db4:  Daubechies wavelet hash



(C) Johannes Buchner, 2013-2017

""" % sys.argv[0])

        sys.exit(1)

    

    hashmethod = sys.argv[1] if len(sys.argv) > 1 else usage()

    if hashmethod == 'ahash':

        hashfunc = imagehash.average_hash

    elif hashmethod == 'phash':

        hashfunc = imagehash.phash

    elif hashmethod == 'dhash':

        hashfunc = imagehash.dhash

    elif hashmethod == 'whash-haar':

        hashfunc = imagehash.whash

    elif hashmethod == 'whash-db4':

        hashfunc = lambda img: imagehash.whash(img, mode='db4')

    else:

        usage()

    userpath = sys.argv[2] if len(sys.argv) > 2 else "."

    find_similar_images(userpath=userpath, hashfunc=hashfunc)


