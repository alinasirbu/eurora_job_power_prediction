#this script collects running time for second training phase: global model
import gzip
import csv
import sys
import numpy as np
import pickle as pkl


comps=[1,2,3,4,5]
month=10
file=open('times_'+str(month)+'_global.csv','w')
out=csv.writer(file)
out.writerow(('user','comp','time'))

total=0
m=0
for comp in comps:
	users=list(csv.reader(open('users'+str(month)+'_'+str(comp)+'.txt','r')))
	for u in users:
    		print(u)
		if len(u)==0:
			continue
            	try:
                	time=pkl.load(file=open('results'+str(month)+'global/'+u[0]+'timeglobal'+str(comp)+'.pkl','r'))
            	except IOError:
                	print(u[0]+' not found')
			time=0
    		out.writerow((u[0],comp,time))
		total+=time
		if time>m:
			m=time
    		file.flush()

out.writerow(('total',total,'max',m))
file.close()                
