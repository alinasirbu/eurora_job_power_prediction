#!/bin/bash
##submits global jobs for users in file users10.csv 
users=$(<users10.csv)

comps=(1 2 3 4 5)


export MONTH=10

for u in ${users[@]}
do
echo $u
for comp in ${comps[@]}
do
        export RUNUSER=$u
	export COMP=$comp
        qsub -V -p -1 script_global.sh 
	sleep 1
done
done


 
