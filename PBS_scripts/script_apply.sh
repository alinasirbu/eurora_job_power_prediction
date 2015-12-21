#!/bin/bash
#this script applies teh global model for one user and one month            
#PBS -l walltime=00:30:00
#PBS -l select=1:ncpus=1 
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
export PYTHONPATH=$PYTHONPATH:[user path to python]
echo python one_user_apply.py $RUNUSER $MONTH $MINT
python one_user_apply.py $RUNUSER $MONTH $MINT




