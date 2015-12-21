##this script applies component models to the data of the selected month
#component predictions are summed to obtain global prediction
##where the component model does not exist (because data is too little), averages are used in the spitrit of the EAM

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
        

def user_run(user,comp):
    global max_power
    global time_scale
    global pred
    t=time.time()
    data=list(csv.reader(gzip.open('data/'+user+'_jobs.csv.gz','r')))
    apply_data=[r for r in data[1:] if r[0][:4]=='2014' and int(r[0][5:7])==month and int(r[comp+8])>0 and float(r[comp+2])>0]
    apply_data=sorted(apply_data,key=lambda r:(float(r[1][:-8]),r[0]))
    if len(apply_data)==0:
	print('no data for component' + str(comp))
	return {},0
    job_time=[(r[0],r[1]) for r in apply_data]
    try:
	#load model
    	cv, model,C,epsilon,gamma,time_scale,max_power=pkl.load(file=gzip.open('results'+str(month)+'global/'+user+'_model_global'+str(comp)+'.pkl.gz','r'))
    	pred=test(cv,model,apply_data,user,'apply'+str(comp),comp)
	result=1
    	pkl.dump(time.time()-t, file=open('results'+str(month)+'global'+str(min_train)+'/'+user+'time_apply_'+str(comp)+'.pkl','w'))
    except IOError:
	#use avgs
	print ('no model for comp '+str(comp))
	pred= (np.array([r[9:14] for r in apply_data],dtype=np.float)*user_avg.get(user,global_avg))[:,comp-1]
	result=0
    return {job_time[i]:pred[i] for i in range(len(pred))},result

def test(cv,model,data,user,code,comp):
    test_power=np.array([float(r[2+comp])/max_power for r in data ])
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
    pl.ylabel('Power')
    pl.xlabel('Data point')
    #pl.legend(('Real power','Predicted power'))
    pl.subplots_adjust(hspace=0.35)
    pl.savefig('results'+str(month)+'global'+str(min_train)+'/'+user+code+'.pdf')
    pl.close()
    pkl.dump((nrmse,rmse,corr,r2,prediction*max_power,test_power*max_power,times,job_ids),file=gzip.open('results'+str(month)+'global'+str(min_train)+'/'+user+'test'+code+'.pkl.gz','w'))
    return prediction*max_power
        

max_power=1000
time_scale=1
user=sys.argv[1]
month=int(sys.argv[2])
min_train=int(sys.argv[3])


data=list(csv.reader(gzip.open('data/'+user+'_jobs.csv.gz','r')))
train_data=[r for r in data[1:] if r[0][:4]=='2014' and int(r[0][5:7])<month]
if len(train_data)<min_train:
	print('Too little training data for this user')
	exit()

apply_data=[r for r in data[1:] if r[0][:4]=='2014' and int(r[0][5:7])==month]
apply_data=sorted(apply_data,key=lambda r:(float(r[1][:-8]),r[0]))

if len(apply_data)<10:
	print('not enough test data for month ' + str(month))
else:
	#read averages, complete grid with global
	global_avg=np.array(list(csv.reader(open('data/'+'avg_global_'+str(month)+'.csv','r'))),dtype=np.float)[0]
	user_avg_data=list(csv.reader(open('data/'+'avg_user_'+str(month)+'.csv','r')))
	user_avg={}
	for u in user_avg_data:
		for i in range(1,len(u)):
			if u[i]=='':
				u[i]=global_avg[i-1]
		user_avg[u[0]]=np.array(u[1:],dtype=np.float)
	
	#repeat user run for each component
	component_power=[]
	model_count=0
	for comp in range(1,6):
		pred,result=user_run(user,comp)
		component_power.append(pred)
		model_count+=result
		
	if model_count==0:
		print('no model for this user')
		exit()
	
	#combine components to obtain total power
	total_power=np.apply_along_axis(sum,1,np.array([r[3:8] for r in apply_data],dtype=np.float))
	predicted_power=[]
	for d in apply_data:
		pp=0
		for i in range(5):
			if d[i+9]!='0' and d[i+3]!='0': #second check is just to filter invalid data
				pp+=component_power[i][(d[0],d[1])]
		predicted_power.append(pp)
	
	predicted_power=np.array(predicted_power)
	
	#plot total with r2 and rmse
	rmse=math.sqrt(np.average((predicted_power-total_power)**2))
	nrmse=math.sqrt(np.average(((predicted_power-total_power)/total_power)**2))
	corr=np.corrcoef(predicted_power,total_power)[0,1]
	r2=1-(sum((predicted_power-total_power)**2)/sum((total_power-np.average(total_power))**2))
	pl.figure(figsize=(6,7))
	pl.subplot(211)
	pl.plot(predicted_power,total_power,'+')
	if math.isnan(corr) or  math.isnan(r2) or math.isnan(rmse): 
        	pl.title("RMSPE="+str(nrmse)+"RMSE="+str(rmse)+" Corr="+str(corr)+" R2="+str(r2))
	else:
        	pl.title("RMSPE="+str(int(nrmse*1000)/1000.0)+" RMSE="+str(int(rmse*1000)/1000.0)+" Corr="+str(int(corr*1000)/1000.0)+" R2="+str(int(r2*1000)/1000.0))
	
	pl.xlabel('Predicted power')
	pl.ylabel('Real power')
	pl.plot([max(pl.xlim()[0],pl.ylim()[0]),min(pl.xlim()[1],pl.ylim()[1])],[max(pl.xlim()[0],pl.ylim()[0]),min(pl.xlim()[1],pl.ylim()[1])])
	pl.subplot(212)
	pl.plot(total_power)
	pl.plot(predicted_power)
	pl.ylabel('Power (W)')
	pl.xlabel('Data point')
	#pl.legend(('Real power','Predicted power'))
	pl.subplots_adjust(hspace=0.35)
	pl.savefig('results'+str(month)+'global'+str(min_train)+'/'+user+'_total.pdf')
	pl.close()
	pkl.dump((nrmse,rmse,corr,r2,total_power,predicted_power),file=gzip.open('results'+str(month)+'global'+str(min_train)+'/'+user+'_total.pkl.gz','w'))
