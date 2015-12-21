##this file contains code to train a model with parameters given as arguments (user name, epsilon, gamma, C, month, component)
#it is used for meta-parameter search in the paper
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
    if len(data)<100:
        print('not enough job data for this user and this component in the valid time points')
        return 
    
    job_ids=list(set([float(r[1][:-8]) for r in data]))
    job_ids.sort()

    if len(job_ids)<5:
        print('not enough jobs for this user and this component in the valid time points')
        return 
    
    train_jobs=job_ids[:int(len(job_ids)*train_f)]
    test_jobs=job_ids[int(len(job_ids)*train_f):]
    
    train_data=[r for r in data[1:] if float(r[1][:-8]) in train_jobs]
    test_data=[r for r in data[1:] if float(r[1][:-8]) in test_jobs]

    
    cv, model,tnrmse,trmse,tcorr,tr2=train(train_data,user,code)
    nrmse,rmse,corr,r2=test(cv,model,test_data,user,code)
    pkl.dump(time.time()-t, file=open('results'+str(month)+'/'+user+'time'+code+'.pkl','w'))



def train(data,user,code):
    global max_power
    data=sorted(data,key=lambda r:(float(r[1][:-8]),r[0]))
    jobs=list(set([(r[1],r[2]) for r in data]))
    job_names=[r[1] for r in jobs] 
    cv=CountVectorizer(analyzer='char', ngram_range=(2, 4))
    cv.fit(job_names)
    target_power=[float(r[comp+2]) for r in data]
    #max_power=max(1000,max(target_power)*1.3)
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
    pl.figure(figsize=(6,7))
    pl.subplot(211)
    if math.isnan(corr) or  math.isnan(r2) or math.isnan(rmse) or math.isinf(rmse) or math.isinf(corr) or math.isinf(r2): 
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
    pl.ylabel('Power')
    pl.xlabel('Data point')
    #pl.legend(('Real power','Predicted power'))
    pl.subplots_adjust( hspace=0.35)
    pl.savefig('results'+str(month)+'/'+user+'train'+code+'.pdf')
    pl.close()
    pkl.dump((nrmse,rmse,corr,r2,pred*max_power,target_power*max_power,times,job_ids),file=gzip.open('results'+str(month)+'/'+user+'train'+code+'.pkl.gz','w'))
    return cv,model,nrmse,rmse,corr,r2


def test(cv,model,data,user,code):
    data[1:]=sorted(data[1:],key=lambda r:(float(r[1][:-8]),r[0]))
    test_power=np.array([float(r[comp+2])/max_power for r in data ])
    times=[datetime.datetime.strptime(r[0],'%Y-%m-%d %H:%M:%S UTC') for r in data]
    features=np.array([d[8:] for d in data],dtype=np.float)
    features[:,0]=features[:,0]/time_scale
    jobs=list(set([(r[1],r[2]) for r in data]))
    name_features=cv.transform([d[2] for d in data]).toarray()
    features=np.hstack((features,name_features))
    job_ids=[r[1] for r in data]
    prediction=model.predict(features)
    rmse=math.sqrt(np.average(((prediction-test_power)*max_power)**2))
    nrmse=math.sqrt(np.average(((prediction-test_power)/test_power)**2))
    corr=np.corrcoef(prediction,test_power)[0,1]
    r2=1-(sum((prediction-test_power)**2)/sum((test_power-np.average(test_power))**2))
    pl.figure(figsize=(6,7))
    pl.subplot(211)
    pl.plot(prediction*max_power,test_power*max_power,'+')
    if math.isnan(corr) or  math.isnan(r2) or math.isnan(rmse): 
        pl.title("RMSPE="+str(nrmse)+"RMSE="+str(rmse)+" Corr="+str(corr)+" R2="+str(r2))
    else:
        pl.title("RMSPE="+str(int(nrmse*1000)/1000.0)+" RMSE="+str(int(rmse*1000)/1000.0)+" Corr="+str(int(corr*1000)/1000.0)+" R2="+str(int(r2*1000)/1000.0))
    pl.xlabel('Predicted power')
    pl.ylabel('Real power')
    pl.plot([max(pl.xlim()[0],pl.ylim()[0]),min(pl.xlim()[1],pl.ylim()[1])],[max(pl.xlim()[0],pl.ylim()[0]),min(pl.xlim()[1],pl.ylim()[1])])
    pl.subplot(212)
    pl.plot(test_power*max_power)
    pl.plot(prediction*max_power)
    pl.ylabel('Power (W)')
    pl.xlabel('Data point')
    #pl.legend(('Real power','Predicted power'))
    pl.subplots_adjust(hspace=0.35)
    pl.savefig('results'+str(month)+'/'+user+'test'+code+'.pdf')
    pl.close()
    pkl.dump((nrmse,rmse,corr,r2,prediction*max_power,test_power*max_power,times,job_ids),file=gzip.open('results'+str(month)+'/'+user+'test'+code+'.pkl.gz','w'))
    return nrmse,rmse,corr,r2
        

max_power=1000
train_f=0.8
user=sys.argv[1]
gamma=float(sys.argv[3])
epsilon=float(sys.argv[4])
C=float(sys.argv[2])
time_scale=float(sys.argv[5])
comp=int(sys.argv[6])
month=int(sys.argv[7])
code='_g'+str(gamma)+'_e'+str(epsilon)+'_c'+str(C)+'_ts'+str(time_scale)+'_comp'+str(comp)

user_run(user,code)

