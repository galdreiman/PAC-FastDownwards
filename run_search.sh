#!/bin/bash



echo "/home/gal-d/downward/benchmarks/$1/$2"
echo "start"

cd /home/gal-d/downward/src/
translate/translate.py /home/shahar/downward/benchmarks/$1/$2
preprocess/preprocess < output.sas
search/downward --search "astar(lmcut())" < output

echo "/home/gal-d/downward/benchmarks/$1/$2"
echo "end" 

exit
