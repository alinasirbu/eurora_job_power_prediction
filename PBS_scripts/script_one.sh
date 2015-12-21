#!/bin/bash
#script to submit one job only , used for collecting results            
#PBS -l walltime=3:00:00
#PBS -l select=1:ncpus=1 
#PBS -N user_job

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
python collect_results_grid.py [username] 




