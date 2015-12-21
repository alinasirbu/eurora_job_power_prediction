#!/bin/bash

users=$(<users10.csv)



export MONTH=10
export MINT=1000 #minimum number of training points

for u in ${users[@]}
do
echo $u
        export RUNUSER=$u
        qsub -V -p -1 script_apply.sh 
	sleep 1
done


 
