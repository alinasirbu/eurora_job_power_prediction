#!/bin/bash
#PBS -A IscrC_PM-HPC             
#PBS -l walltime=00:30:00
#PBS -l select=1:ncpus=1 
#PBS -q route
#PBS -N apply_user_job

module load gnu
module load blas
module load python
module load lapack
module load numpy
module load scipy
module load matplotlib

cd $PBS_O_WORKDIR
hostname
export PYTHONPATH=$PYTHONPATH:/galileo/home/userexternal/asirbu00/sw/lib/python2.7/site-packages
echo python one_user_apply.py $RUNUSER $MONTH $MINT
python one_user_apply.py $RUNUSER $MONTH $MINT




