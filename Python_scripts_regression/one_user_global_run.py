#once meta-parameters are explored, this file finds the best parameter combination and trains a model from all data, for each component
#this is a first step to obtain the global model
import csv
import gzip
import datetime
import numpy as np
import matplotlib
import pylab as pl
import math
import pickle as pkl
import sys
import math
from sklearn.svm import SVR
from sklearn.feature_extraction.text import CountVectorizer
import time
        

def user_run(user,code):
    t=time.time()
    data=list(csv.reader(gzip.open('data/'+user+'_jobs.csv.gz','r')))
    data=[r for r in data[1:] if r[0][:4]=='2014' and int(r[0][5:7])<month and int(r[comp+8])>0 and float(r[comp+2])>0]
    cv, model,tnrmse,trmse,tcorr,tr2=train(data,user,code)
    pkl.dump(time.time()-t, file=open('results'+str(month)+'global/'+user+'time'+code+'.pkl','w'))
    pkl.dump((cv,model,C,epsilon,gamma,time_scale,max_power),file=gzip.open('results'+str(month)+'global/'+user+'_model_'+code+'.pkl.gz','w'))



def train(data,user,code):
    global max_power
    data=sorted(data,key=lambda r:(float(r[1][:-8]),r[0]))
    jobs=list(set([(r[1],r[2]) for r in data]))
    job_names=[r[1] for r in jobs] 
    cv=CountVectorizer(analyzer='char', ngram_range=(2, 4))
    cv.fit(job_names)
    target_power=[float(r[comp+2]) for r in data]
    max_power=max(target_power)*1.3
    times=[datetime.datetime.strptime(r[0],'%Y-%m-%d %H:%M:%S UTC') for r in data]
    target_power=np.array([float(r[comp+2])/max_power for r in data ])
    features=np.array([r[8:] for r in data ],dtype=np.float)
    features[:,0]=features[:,0]/time_scale
    cluster_jobs=cv.transform([r[2] for r in data]).toarray()
    job_ids=[r[1] for r in data]
    features=np.hstack((features,cluster_jobs))
    model=SVR(gamma=gamma,epsilon=epsilon)
    model.fit(features,target_power)
    pred=model.predict(features)
    rmse=math.sqrt(np.average(((pred-target_power)*max_power)**2))
    nrmse=math.sqrt(np.average(((pred-target_power)/target_power)**2))
    corr=np.corrcoef(pred,target_power)[0,1]
    r2=1-(sum((pred-target_power)**2)/sum((target_power-np.average(target_power))**2))
    pl.figure(figsize=(6,10))
    pl.subplot(211)
    if math.isnan(corr) or  math.isnan(r2) or math.isnan(rmse): 
        pl.title("RMSPE="+str(nrmse)+" RMSE="+str(rmse)+" Corr="+str(corr)+" R2="+str(r2))
    else:
        pl.title("RMSPE="+str(int(nrmse*1000)/1000.0)+" RMSE="+str(int(rmse*1000)/1000.0)+" Corr="+str(int(corr*1000)/1000.0)+" R2="+str(int(r2*1000)/1000.0))
    pl.plot(pred*max_power,target_power*max_power,'+')
    pl.xlabel('Predicted power')
    pl.ylabel('Real power')
    pl.plot([max(pl.xlim()[0],pl.ylim()[0]),min(pl.xlim()[1],pl.ylim()[1])],[max(pl.xlim()[0],pl.ylim()[0]),min(pl.xlim()[1],pl.ylim()[1])])
    pl.subplot(212)
    pl.plot(target_power*max_power)
    pl.plot(pred*max_power)
    pl.ylabel('Power (W)')
    pl.xlabel('Data point')
    #pl.legend(('Real power','Predicted power'))
    pl.subplots_adjust( hspace=0.35)
    pl.savefig('results'+str(month)+'global/'+user+'train'+code+'.pdf')
    pl.close()
    pkl.dump((nrmse,rmse,corr,r2,pred*max_power,target_power*max_power,times,job_ids),file=gzip.open('results'+str(month)+'global/'+user+'train'+code+'.pkl.gz','w'))
    return cv,model,nrmse,rmse,corr,r2
        

max_power=1000
user=sys.argv[1]
comp=int(sys.argv[2])
month=int(sys.argv[3])
C=1.0

epsilons=[0.1,0.01,0.001]
gammas=[0.1,0.01,0.001,0.0001,0.00001]
tss=[1.0,10.0,100.0,1000.0,10000.0]

best=(-1,-1,-1,-1,1000)#epsilon, gamma, ts, r2, mae
for g in gammas:
    for ts in tss:
	for e in epsilons:
		code='_g'+str(g)+'_e'+str(e)+'_c'+str(C)+'_ts'+str(ts)
            	try:
			file='results'+str(month)+'/'+user+'test'+code+'_comp'+str(comp)+'.pkl.gz'
                        nrmse,rmse,corr,r2,prediction,test_power,times,jobs=pkl.load(file=gzip.open(file,'r'))
                        R=max(r2,best[3])
                        if R<0.1:
                            if rmse<best[4]:
                                    best=(e,g,ts,r2,rmse)
                        else:
                            if r2>best[3]:
                                    best=(e,g,ts,r2,rmse)
            	except IOError:
                        print(file+' not found')



gamma=best[1]
epsilon=best[0]
time_scale=best[2]

if gamma!=-1: #there is some run
	code='global'+str(comp)
	user_run(user,code)

