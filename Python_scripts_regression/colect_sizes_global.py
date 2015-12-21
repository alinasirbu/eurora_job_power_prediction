import gzip
import csv
import sys
import numpy as np
import pickle as pkl


month=10

file=open('global_size'+str(month)+'.csv','w')
out=csv.writer(file)
out.writerow(('user','test #', 'train #','test jobs', 'train jobs','test avg','test std','train avg','train std'))


train=0
test=0
trainj=0
testj=0
users=list(csv.reader(open('users'+str(month)+'_global.txt','r')))
for u in users:
        print(u)
        data=list(csv.reader(gzip.open('data/'+u[0]+'_jobs.csv.gz','r')))
	train_data=[r for r in data[1:] if r[0][:4]=='2014' and int(r[0][5:7])<month]
	apply_data=[r for r in data[1:] if r[0][:4]=='2014' and int(r[0][5:7])==month]
	train_power=[float(r[3])+float(r[4])+float(r[5])+float(r[6])+float(r[7]) for r in train_data]
	test_power=[float(r[3])+float(r[4])+float(r[5])+float(r[6])+float(r[7]) for r in apply_data]
	train_jobs=list(set([r[1] for r in train_data]))
	test_jobs=list(set([r[1] for r in apply_data]))
	out.writerow((u[0],len(apply_data),len(train_data),len(test_jobs),len(train_jobs),np.mean(test_power),np.std(test_power),np.mean(train_power),np.std(train_power)))
	train+=len(train_data)
	test+=len(apply_data)
	trainj+=len(train_jobs)
	testj+=len(apply_jobs)
        file.flush()

out.writerow(('total',train,test,trainj,testj))
file.close()                
