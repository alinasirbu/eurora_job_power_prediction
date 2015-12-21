#!/bin/bash
#perform grid search for all users (restricted parameter set)
#assumes the existence of the file valid_users_10_$comp.txt for each component, containing a list of user names to analyse


Cs=(1.0)
gammas=(0.1 0.01 0.001 0.0001 0.00001)
epsilons=(0.1 0.01 0.001)
tss=(1.0 10.0 100.0 1000.0 10000.0)
comps=(1 2 3 4 5)

export MONTH=10


for comp in ${comps[@]}
do
echo $comp
users=$(<valid_users_${MONTH}_$comp.txt)
for u in ${users[@]}
do
echo $u
for c in ${Cs[@]}
do
for g in ${gammas[@]}
do
for e in ${epsilons[@]}
do
for t in ${tss[@]}
do
        export RUNUSER=$u
	export C=$c
        export GAMMA=$g
        export EPSILON=$e
	export TS=$t
	export COMP=$comp
        qsub -V -p -1 script.sh 
	sleep 1
done
done
done
done
done
done

 
