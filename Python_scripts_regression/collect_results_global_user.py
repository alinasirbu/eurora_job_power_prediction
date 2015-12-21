#this script collects global model results (components summed)
import gzip
import csv
import sys
import numpy as np
import math
import pickle as pkl


month=10

file=open('all_users_global'+str(month)+'_noneg.csv','w')
out=csv.writer(file)
out.writerow(('user','test sd', 'test avg','test rmse','test r2'))



users=list(csv.reader(open('users'+str(month)+'_global.txt','r')))
for u in users:
        print(u)
        nrmse,rmse,corr,r2,test_power,prediction=pkl.load(file=gzip.open('results'+str(month)+'global/'+u[0]+'_total.pkl.gz','r'))
        avgt=np.average(test_power)
        stdt=np.std(test_power)
	prediction[prediction<0]=0
	rmse=math.sqrt(np.average(((prediction-test_power))**2))
	r2=1-(sum((prediction-test_power)**2)/sum((test_power-np.average(test_power))**2))
        result=(stdt,avgt,rmse,r2)
        out.writerow((u[0],)+result)
        file.flush()

file.close()                
