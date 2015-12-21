#this script collects global results for all users per component
import gzip
import csv
import sys
import numpy as np
import pickle as pkl

comps=[1,2,3,4,5]
month=10

file=open('all_users_components'+str(month)+'.csv','w')
out=csv.writer(file)
out.writerow(('user','component','sd','avg','test sd', 'test avg','test rmse','test r2'))


for comp in comps:
	users=list(csv.reader(open('users'+str(month)+'_'+str(comp)+'.txt','r')))
	for u in users:
    		print(u)
                nrmse,rmse,corr,r2,prediction,test_power,times,jobs=pkl.load(file=gzip.open('results'+str(month)+'global/'+u[0]+'testapply'+str(comp)+'.pkl.gz','r'))
                tnrmse,trmse,tcorr,tr2,tprediction,train_power,ttimes,jobs=pkl.load(file=gzip.open('results'+str(month)+'global/'+u[0]+'trainglobal'+str(comp)+'.pkl.gz','r'))
                power=list(test_power)+list(train_power)
                avg=np.average(power)
                std=np.std(power)
		avgt=np.average(test_power)
                stdt=np.std(test_power)
		result=(std,avg,stdt,avgt,rmse,r2)
    		out.writerow((u[0],comp)+result)
    		file.flush()

file.close()                
