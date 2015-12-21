#this script collects and plots grid search results for one user
import gzip
import csv
import sys
import numpy as np
import pickle as pkl

user=sys.argv[1]
Cs=[10.0,1.0,100.0] #replace 0.1 with 100 for visualisation reasons
gammas=[100.0, 10.0,1.0,0.1,0.01,0.001,0.0001,0.00001]
epsilons=[0.1,0.01,0.001,0.0001,0.00001]
tss=[1.0,10.0,100.0,1000.0,10000.0]
comps=[1,2,3,4,5]
month=10

file=open(user+'_grid_search.csv','w')
out=csv.writer(file)
out.writerow(('component','C','gamma','epsilon','time_scale','sd','avg','test RMSPE','test RMSE','test corr','test r2','train RMSPE','train RMSE','train corr','train r2'))

for comp in comps:
    for c in Cs:
    	for g in gammas:
            for e in epsilons:
            	for ts in tss:
                    code='_g'+str(g)+'_e'+str(e)+'_c'+str(c)+'_ts'+str(ts)+'_comp'+str(comp)
                    try:
                    	nrmse,rmse,corr,r2,prediction,test_power,times,jobs=pkl.load(file=gzip.open('results'+str(month)+'/'+user+'test'+code+'.pkl.gz','r'))
                    	tnrmse,trmse,tcorr,tr2,tprediction,train_power,ttimes,jobs=pkl.load(file=gzip.open('results'+str(month)+'/'+user+'train'+code+'.pkl.gz','r'))
                    	power=list(test_power)+list(train_power)
                    	avg=np.average(power)
                    	std=np.std(power)
                    except IOError:
                    	std,avg,nrmse,rmse,corr,r2,tbne,tnrmse,trmse,tcorr,tr2=(-1,)*11
                    	print(code+' not found')
                    out.writerow((comp,c,g,e,ts,std,avg,nrmse,rmse,corr,r2,tnrmse,trmse,tcorr,tr2))
                    file.flush()

file.close()                
