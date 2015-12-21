##this script combines all global predicted time series for all users to obtain final plot and fit
import gzip
import csv
import sys
import numpy as np
import pickle as pkl
import math
import pylab as pl


month=10


pow=[]
pred=[]
pred_avg=[]
users=list(csv.reader(open('users'+str(month)+'_global.txt','r')))
for u in users:
        print(u)
	#if u[0]=='a07smr01':
	# 	continue
        nrmse,rmse,corr,r2,test_power,prediction=pkl.load(file=gzip.open('results'+str(month)+'global/'+u[0]+'_total.pkl.gz','r'))
	pow.extend(test_power)
	pred.extend(prediction)
	nrmse,rmse,corr,r2,test_power,prediction_avg=pkl.load(file=gzip.open('results'+str(month)+'_avg/'+u[0]+'_total_avg.pkl.gz','r'))
	pred_avg.extend(prediction_avg)
	print(sum(prediction-prediction_avg))

pow=np.array(pow)
pred=np.array(pred)
pred[pred<0]=0
pred_avg=np.array(pred_avg)
pred_avg[pred_avg<0]=0
nrmse=math.sqrt(np.average(((pred-pow))**2))/np.average(pow)
r2=1-(sum((pred-pow)**2)/sum((pow-np.average(pow))**2))
nrmse_avg=math.sqrt(np.average(((pred_avg-pow))**2))/np.average(pow)
r2_avg=1-(sum((pred_avg-pow)**2)/sum((pow-np.average(pow))**2))
print(nrmse,r2,nrmse_avg,r2_avg)
pl.figure(figsize=(5,2.3))
pl.plot(pow)
pl.plot(pred)
#pl.plot(pred_avg)
#pl.title('NRMSE='+str(int(nrmse*100)/100.0)+'/'+str(int(nrmse_avg*100)/100.0)+', R-squared='+str(int(r2*100)/100.0)+'/'+str(int(r2_avg*100)/100.0))
pl.title('NRMSE='+str(int(nrmse*100)/100.0)+', R-squared='+str(int(r2*100)/100.0))
pl.legend(('Real power','Predicted power'))
pl.ylabel('Power (W)')
pl.xlabel('Data point')
pl.xticks(rotation=30)
pl.subplots_adjust(bottom=0.3,left=0.2)
pl.savefig('concat_'+str(month)+'.pdf')
pl.close()

                
