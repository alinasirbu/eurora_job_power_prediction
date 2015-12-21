# Scripts for predicting power of jobs in the Eurora system.

Folders:
*Preprocessing* - contains mysql and big query commands to extract  features from the data. These require access to the EuroraMeasurements database, CINECA systems and Google Query.

*Python_scripts_regression* - contains 3 scripts for the three stages of the study: meta-parameter search, global model training, model application. These were run on an HPC system with PBS. Running scripts are in folder *PBS_scripts*. Files with user names are assumed to exist (not published for privacy reasons).


*Python_scripts_result_analysis* - contains Python scripts to collect results from multiple runs. These include time series, AUPR and AUROC, running times. Again most of these were run in parallel for the users, using scripts from the  *PBS_scripts* folder.
