#!/bin/sh
cd tmp
mkdir sort
cd sort
n=1
max=$1
set -- 

while [ "$n" -le "$max" ]; do
    set -- "$@" "$n" # this adds s$n to the end of $@
    n=$(( $n + 1 ));
done 
mkdir "$@"
