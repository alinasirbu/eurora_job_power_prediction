import gzip
import csv
import sys
import numpy as np
import pickle as pkl


comps=[1,2,3,4,5]
month=10

file=open('meta_'+str(month)+'.csv','w')
out=csv.writer(file)
out.writerow(('user','comp','C','Gamma','epsilon','ts'))


for comp in comps:
	users=list(csv.reader(open('users'+str(month)+'_'+str(comp)+'.txt','r')))
	for u in users:
    		print(u)
		if len(u)==0:
			continue
            	try:
                	(cv,model,C,epsilon,gamma,time_scale,max_power)=pkl.load(file=gzip.open('results'+str(month)+'global/'+u[0]+'_model_global'+str(comp)+'.pkl.gz','r'))
            	except IOError:
                	print(u[0]+' not found')
			time=0
    		out.writerow((u[0],comp,C,gamma,epsilon,time_scale))
    		file.flush()

file.close()                
