#!/bin/bash
#PBS -A IscrC_PM-HPC             
#PBS -l walltime=05:00:00
#PBS -l select=1:ncpus=1 
#PBS -q route
#PBS -N global_user_job

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
echo python one_user_global_run.py $RUNUSER $COMP $MONTH
python one_user_global_run.py $RUNUSER $COMP $MONTH




