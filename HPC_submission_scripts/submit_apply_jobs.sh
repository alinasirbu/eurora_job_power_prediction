#!/bin/bash

users=$(<users12.csv)



export MONTH=12
export MINT=1000

for u in ${users[@]}
do
echo $u
        export RUNUSER=$u
        qsub -V -p -1 script_apply.sh 
	sleep 1
done


 
