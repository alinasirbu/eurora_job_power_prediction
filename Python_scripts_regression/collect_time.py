#this script collects running time for grid search phase
import gzip
import csv
import sys
import numpy as np
import pickle as pkl


c=1.0
epsilons=[0.1,0.01,0.001]
gammas=[0.1,0.01,0.001,0.0001,0.00001]
tss=[1.0,10.0,100.0,1000.0,10000.0]
comps=[1,2,3,4,5]
month=10

file=open('times_'+str(month)+'_1.csv','w')
out=csv.writer(file)
out.writerow(('user','C','epsilon','gamma','tss','time'))

total=0
m=0
for comp in comps:
	users=list(csv.reader(open('users'+str(month)+'_'+str(comp)+'.txt','r')))
	for u in users:
    		print(u)
		if len(u)==0:
			continue
    		for g in gammas:
        		for ts in tss:
	    			for e in epsilons:
            				code='_g'+str(g)+'_e'+str(e)+'_c'+str(c)+'_ts'+str(ts)+'_comp'+str(comp)
            				try:
                				time=pkl.load(file=open('results'+str(month)+'/'+u[0]+'time'+code+'.pkl','r'))
            				except IOError:
                				print(u[0]+code+' not found')
						time=0
    					out.writerow((u[0],c,e,g,ts,time))
					total+=time
					if time>m:
						m=time
    					file.flush()

out.writerow(('total',total,'max',m))
file.close()                
