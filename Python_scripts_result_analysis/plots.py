##this file contains several pieces of code used to create the plots from the paper.
##input files should be generated either by collecting results from teh individual runs, or from the BigQuery analysis
import csv
import gzip
import datetime
import numpy as np
import matplotlib
import pylab as pl
import math
import theanets as tn
import logging
import pickle as pkl
import sys
import theano as t
import math
from sklearn.svm import SVR
from sklearn import gaussian_process
from sklearn import linear_model
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn import metrics
from sklearn.feature_extraction.text import CountVectorizer



#####PLOT heatmap after grid search for one user 
user='[username]'

d=list(csv.reader(open(user+'_grid_search.csv','r')))
grid=np.array(d[1:],dtype=np.float)

comps=list(set(grid[:,0]))
Cs=list(set(grid[:,1]))
gammas=list(set(grid[:,2]))
epsilons=list(set(grid[:,3]))
tss=list(set(grid[:,4]))
Cs.sort()
gammas.sort()
epsilons.sort()
tss.sort()

#first NRMSE
for comp in comps:
    pl.figure(figsize=(len(Cs)*5+1,len(epsilons)*2+1))
    index=1
    for e in epsilons:
        for c in Cs:
            ax=pl.subplot(len(epsilons),len(Cs),index)
            data=grid[grid[:,0]==comp,:]
            data=data[data[:,3]==e,:]
            data=data[data[:,1]==c,:]
            imdata=np.zeros((len(tss),len(gammas)))
            for d in data:
                imdata[tss.index(d[4]),gammas.index(d[2])]=d[8]/d[6]
            
            l=ax.pcolor(imdata,vmin=0,vmax=1,shading='faceted',cmap='coolwarm_r')
            ax.set_xticks(np.arange(imdata.shape[1])+0.5, minor=False)
            ax.set_yticks(np.arange(imdata.shape[0])+0.5, minor=False)
            if e==max(epsilons):
                ax.set_xticklabels(gammas,rotation=30, ha='right')
                ax.set_xlabel('Gamma')
            else:
                ax.set_xticklabels(())
                if e==min(epsilons):
                    pl.text('NRMSE')
            if c==min(Cs):
                ax.set_yticklabels(tss)
                if e==0.001:
                    ax.set_ylabel('Time scaling factor')
            else:
                ax.set_yticklabels(())
            ax.tick_params(length=0)
            for x in range(len(tss)):
                for y in range(len(gammas)):
                    col='black'
                    if imdata[x][y]>0.8 or imdata[x][y]<0.2:
                        col='white'
                    pl.text(y + 0.5 , x + 0.5, '%.2f' % imdata[x][y],
                             horizontalalignment='center',
                             verticalalignment='center',color=col)
            
            pl.title('C='+str(c)+' Epsilon='+str(e))
            cbar = pl.colorbar(l)
            index+=1
    
    pl.subplots_adjust(wspace=0.01,right=0.99,bottom=0.2)
    pl.savefig(user+str(comp)+'gridnRMSE.pdf', format='pdf')
    pl.close()



#then R^2
for comp in comps:
    pl.figure(figsize=(len(Cs)*5+1,len(epsilons)*2+1))
    index=1
    for e in epsilons:
        for c in Cs:
            ax=pl.subplot(len(epsilons),len(Cs),index)
            data=grid[grid[:,0]==comp,:]
            data=data[data[:,3]==e,:]
            data=data[data[:,1]==c,:]
            imdata=np.zeros((len(tss),len(gammas)))
            for d in data:
                imdata[tss.index(d[4]),gammas.index(d[2])]=d[10]
            
            l=ax.pcolor(imdata,vmin=0,vmax=1,shading='faceted',cmap='coolwarm')
            ax.set_xticks(np.arange(imdata.shape[1])+0.5, minor=False)
            ax.set_yticks(np.arange(imdata.shape[0])+0.5, minor=False)
            if e==max(epsilons):
                ax.set_xticklabels(gammas,rotation=30, ha='right')
                ax.set_xlabel('Gamma')
            else:
                ax.set_xticklabels(())
                if e==min(epsilons):
                    pl.title('R-squared')
            if c==min(Cs):
                ax.set_yticklabels(tss)
                if e==0.001:
                    ax.set_ylabel('Time scaling factor')
            else:
                ax.set_yticklabels(())
            ax.tick_params(length=0)
            for x in range(len(tss)):
                for y in range(len(gammas)):
                    col='black'
                    if imdata[x][y]>0.8 or imdata[x][y]<0.2:
                        col='white'
                    pl.text(y + 0.5 , x + 0.5, '%.2f' % imdata[x][y],
                             horizontalalignment='center',
                             verticalalignment='center',color=col)
            
            pl.title('C='+str(c)+' Epsilon='+str(e))
            cbar = pl.colorbar(l)
            index+=1
    
    pl.subplots_adjust(wspace=0.01,right=0.99,bottom=0.2)
    pl.savefig(user+str(comp)+'gridR2.pdf', format='pdf')
    pl.close()


####feature explanations
#number of nodes
pl.figure(figsize=(6,2))
d=list(csv.reader(open('nnodes.csv','r')))
jobs_nnodes=list(set([(r[1],r[-1]) for r in d[1:]]))
jobs_nnodes.sort(key=lambda x:x[1],reverse=True)
h=[]
for j in jobs_nnodes:
    jobts=[float(r[3]) for r in d[1:] if r[1]==j[0]]
    jobtimes=[float(r[4]) for r in d[1:] if r[1]==j[0]]
    hh,=pl.plot(jobtimes,jobts)
    h.append(hh)


pl.xlabel('Seconds since job start')
pl.ylabel('Power (W)')
pl.ylim((95,195))
pl.legend([h[0]],('16 cores on '+jobs_nnodes[0][1]+' nodes',), loc=2)
pl.twinx()
pl.yticks(color='white')
pl.legend([h[1]],('16 cores on '+jobs_nnodes[1][1]+' node',), loc=3)
pl.subplots_adjust(bottom=0.25)
pl.savefig('nnodes.pdf',format='pdf')
pl.close()


#number of same -node components used by other users
pl.figure(figsize=(6,2))
d=list(csv.reader(open('cores_shared.csv','r')))
jobts=[float(r[3]) for r in d[1:]]
jobtimes=[float(r[4]) for r in d[1:]]
cores_shared=[int(r[-4]) for r in d[1:]]
h1=pl.plot(jobtimes,jobts)
pl.ylabel('Power (W)',color='blue')
pl.legend(('Power',), loc=2)
pl.ylim((150,550))
pl.yticks(color='blue')
pl.twinx()
h2=pl.plot(jobtimes,cores_shared,color='green')
pl.xlabel('Seconds since job start')
pl.ylabel('Cores used by other jobs',color='green',fontsize=10)
pl.legend(('Cores',), loc=3)
pl.yticks(color='green')
pl.subplots_adjust(bottom=0.2)
pl.savefig('shared.pdf',format='pdf')
pl.close()


#type of core
pl.figure(figsize=(6,2))
d=list(csv.reader(open('3jobs-low-med-high2.csv','r')))
all_jobs=[r[1] for r in d[1:]]
jobs=[]
for j in all_jobs:
    if j not in jobs:
        jobs.append(j)

labels=[]
for j in jobs: 
    jobts=[float(r[3]) for r in d[1:] if r[1]==j]
    jobtimes=[float(r[4]) for r in d[1:] if r[1]==j]
    pl.plot(jobtimes,jobts)
    r=[r[5:8] for r in d[1:] if r[1]==j][0]
    labels.append(r[0]+' S, '+r[1]+' M, '+r[2]+' F cores')

pl.xlabel('Seconds since job start')
pl.ylabel('Power (W)')
pl.ylim((20,300))
pl.legend(labels, loc=1,fontsize=11)
pl.subplots_adjust(bottom=0.25)
pl.savefig('lowmedhigh.pdf',format='pdf')
pl.close()


#application runtime (time since start)
pl.figure(figsize=(6,2))
d=list(csv.reader(open('runtime.csv','r')))
jobts=[float(r[3]) for r in d[1:]]
jobtimes=[float(r[4]) for r in d[1:]]
pl.plot(jobtimes,jobts)
pl.xlabel('Seconds since job start')
pl.ylabel('Power (W) ')
pl.subplots_adjust(bottom=0.25)
pl.ylim((0,pl.ylim()[1]))
pl.savefig('runtime.pdf',format='pdf')
pl.close()



#####variability of power
files=['cpu5.0_var.csv','cpu18.0_var.csv','cpu64.0_var.csv','gpu40_var.csv']
#files=['cpu1.0_var.csv','cpu20.0_var.csv','cpu50.0_var.csv','gpu33var.csv']
col=['green','#DC0000','blue','#FF9933']

data=[]
pl.figure(figsize=(10,7))
pl.subplot(211)
for i in range(len(files)):
    d=list(csv.reader(open(files[i],'r')))[1:]
    x=[int(r[0]) for r in d]
    y=[float(r[2]) for r in d]
    yerr=[float(r[3]) for r in d]
    pl.errorbar(x,y,yerr=yerr,color=col[i])
    data.append(d)

pl.xlabel('Load %')
pl.ylabel('Power')
pl.xlim((0,100))
pl.ylim((0,200))
pl.grid(True)
pl.legend(('S','M','F','GPU'), loc=2)          

pl.subplot(212)
for i in range(len(files)):
    d=data[i]
    x=[int(r[0]) for r in d]
    y=[float(r[4]) for r in d]
    pl.plot(x,y,color=col[i])

pl.xlabel('Load %')
pl.ylabel('Power CV')
pl.xlim((0,100))
pl.ylim((0,0.6))
pl.grid(True)
pl.legend(('S','M','F','GPU'))          
pl.savefig('var.pdf')
pl.close()




                      
####performance per user - R2 vs NRMSE

month=10
components=[1,2,3,4,5]
names=['S','M','F','GPU','MIC']

for component in components:
    svr=list(csv.reader(open('all_users_components'+str(month)+'.csv','r')))
    eavg=list(csv.reader(open('all_users_components'+str(month)+'_avg.csv','r'))) #this is the EAM performance - obtain by running one_user_apply.py with no models trained
    svr_r2=[max(-2,float(r[7])) for r in svr[1:] if int(r[1])==component]
    eavg_r2=[max(-2,float(eavg[i][3])) for i in range(1,len(eavg)) if int(eavg[i][1])==component]
    svr_mse=[float(r[6])/float(r[5])for r in svr[1:] if int(r[1])==component]
    eavg_mse=[float(eavg[i][2])/float(svr[i][5]) for i in range(1,len(eavg)) if int(eavg[i][1])==component]
    pl.figure(figsize=(5,2.5))
    for i in range(len(svr_r2)):
        pl.plot((svr_r2[i],eavg_r2[i]),(svr_mse[i],eavg_mse[i]), color='black',alpha=0.4)
    
    pl.plot(eavg_r2,eavg_mse,'o',color='blue',alpha=0.3)
    pl.plot(svr_r2,svr_mse,'*',color='red')
    pl.ylabel('NRMSE')
    pl.xlabel('R-squared')
    pl.subplots_adjust(left=0.2,bottom=0.2)
    pl.yscale('log')
    pl.xlim((-2.1,1.1))
    pl.ylim((0.001,10))
    pl.text(-1.8,2,names[component-1],fontsize=14)
    pl.axhline(y=0.2,ls=':',color='grey')
    pl.axvline(x=0.5,ls=':',color='grey')
    pl.savefig('all_scatter_both_'+str(month)+'_'+str(component)+'.pdf')
    pl.close()

    

####performance globally 

month=10

svr=list(csv.reader(open('all_users_global'+str(month)+'_noneg.csv','r')))
eavg=list(csv.reader(open('all_users_global'+str(month)+'avg.csv','r')))#this is the EAM performance - obtain by running one_user_apply.py with no models trained
svr_r2=[max(float(r[4]),-2)for r in svr[1:] ]
eavg_r2=[max(float(eavg[i][4]),-2) for i in range(1,len(eavg)) ]
svr_mse=[float(r[3])/float(r[2])for r in svr[1:]]
eavg_mse=[float(eavg[i][3])/float(svr[i][2]) for i in range(1,len(eavg))]
pl.figure(figsize=(5,2.5))
pl.axhline(y=0.2,ls=':',color='grey')
pl.axvline(x=0.5,ls=':',color='grey')
for i in range(len(svr_r2)):
    pl.plot((svr_r2[i],eavg_r2[i]),(svr_mse[i],eavg_mse[i]), color='black',alpha=0.4)

pl.plot(eavg_r2,eavg_mse,'o',color='blue',alpha=0.3)
pl.plot(svr_r2,svr_mse,'*',color='red')
pl.ylabel('NRMSE')
pl.xlabel('R-squared')
pl.subplots_adjust(left=0.2,bottom=0.2)
pl.yscale('log')
pl.xlim((-2.1,1.1))
pl.ylim((0.001,10))
pl.text(-1.8,2,'Global',fontsize=14)
pl.savefig('all_scatter_both_'+str(month)+'.pdf')
pl.close()



##running time histogram for the three stages
month=10
pl.figure(figsize=(6,3))
t1=list(csv.reader(open('times_'+str(month)+'_1.csv','r')))
t2=list(csv.reader(open('times_'+str(month)+'_global.csv','r')))
t3=list(csv.reader(open('times_'+str(month)+'_apply.csv','r')))
n,bins,patches=pl.hist([float(r[5]) for r in t1[1:-1]],histtype='step',normed=True,color='blue',bins=2000,cumulative=True)
patches[0].set_xy(patches[0].get_xy()[:-1])
n,bins,patches=pl.hist([float(r[2]) for r in t2[1:-1]],histtype='step',normed=True,color='red',bins=2000,cumulative=True)
patches[0].set_xy(patches[0].get_xy()[:-1])
n,bins,patches=pl.hist([float(r[2]) for r in t3[1:-1]],histtype='step',normed=True,color='green',bins=2000,cumulative=True)
patches[0].set_xy(patches[0].get_xy()[:-1])
h1,=pl.plot([-1,-1])
h2,=pl.plot([-1,-1])
h3,=pl.plot([-1,-1])
pl.xscale('log')
pl.xlabel('Running time (s)')
pl.ylabel('Fraction of runs')
pl.ylim((0,1.1))
pl.legend((h1,h2,h3),('Meta-parameter optimization','Global otimization','Model application'),loc=4)
pl.grid()
pl.subplots_adjust(left=0.1,bottom=0.2,right=0.99)
pl.savefig('time_hist'+str(month)+'.pdf')
pl.close()


##variability over all components
gpus=range(33,65)
gpu_cvs=[]
for gpu in gpus:
    d=list(csv.reader(open('load_avg_gpu'+str(gpu)+'.csv','r')))
    gpu_cvs.append(np.mean([float(r[5]) for r in d[1:] if r[2]!='1' and float(r[1])<=100]))


cpus=range(1,65)
cvs=[]
for cpu in cpus:
    d=list(csv.reader(open('load0_avg_cpu'+('0'+str(cpu))[-2:]+'.csv','r')))
    d1=list(csv.reader(open('load1_avg_cpu'+('0'+str(cpu))[-2:]+'.csv','r')))
    d.extend(d1[1:])
    cvs.append(np.mean([float(r[4]) for r in d[1:] if r[2]!='1' and float(r[0])<=100]))

pl.figure(figsize=(10,3))
pl.bar(cpus[:16]+cpus[24:32],cvs[:16]+cvs[24:32],color='green')
pl.bar(cpus[16:24],cvs[16:24],color='#DC0000')
pl.bar(cpus[32:38]+cpus[39:52]+cpus[53:],cvs[32:38]+cvs[39:52]+cvs[53:],color='blue')
pl.bar(gpus,gpu_cvs,color='#FF9933')
pl.bar([cpus[38]]+[cpus[44]]+[cpus[48]]+[cpus[52]]+[cpus[54]],[cvs[38]]+[cvs[44]]+[cvs[48]]+[cvs[52]]+[cvs[54]],color='blue')

pl.legend(('S','M','F', 'GPU'))
pl.grid()
pl.xlabel('Node')
pl.ylabel('Average CV')
pl.xlim((1,65))
pl.subplots_adjust(left=0.2,bottom=0.2)
pl.savefig('var_all.pdf')


