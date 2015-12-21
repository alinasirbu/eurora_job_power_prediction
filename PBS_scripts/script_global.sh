#!/bin/bash
#this script submits one global job to PBS             
#PBS -l walltime=05:00:00
#PBS -l select=1:ncpus=1 
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
export PYTHONPATH=$PYTHONPATH:[user path to python]
echo python one_user_global_run.py $RUNUSER $COMP $MONTH
python one_user_global_run.py $RUNUSER $COMP $MONTH




