#!/bin/bash



echo "/home/shahar/downward/benchmarks/$1/$2"
echo "start"

cd /home/shahar/downward/src/
translate/translate.py /home/shahar/downward/benchmarks/$1/$2
preprocess/preprocess < output.sas
search/downward --search "astar(lmcut())" < output

echo "/home/gal/downward/benchmarks/$1/$2"
echo "end" 

exit
