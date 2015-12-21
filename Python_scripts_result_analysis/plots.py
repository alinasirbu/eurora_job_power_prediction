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


user='fesposit'

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






d=list(csv.reader(open('all_users_both.csv','r')))
rmses=[float(r[5])/float(r[2])for r in d[1:] if float(r[5])!=-1]
r2s=[float(r[7]) for r in d[1:] if float(r[5])!=-1]
trmses=[float(r[10])/float(r[2]) for r in d[1:] if float(r[5])!=-1]
tr2s=[float(r[12]) for r in d[1:] if float(r[5])!=-1]
pl.figure(figsize=(6,7))
pl.subplot(221)
pl.hist(rmses,bins=50)
pl.title('Test MAE')
pl.subplot(222)
pl.hist(r2s,bins=50)
pl.title('Test R-squared')
pl.subplot(223)
pl.hist(trmses,bins=50)
pl.title('Train MAE')
pl.subplot(224)
pl.hist(tr2s,bins=50)
pl.title('Train R-squared')
pl.savefig('all_hist.pdf')
pl.close()
pl.figure(figsize=(6,7))
pl.subplot(211)
pl.plot(trmses,tr2s,'*')
pl.ylabel('Train R-squared')
pl.xlabel('Train normalised MAE')
pl.axhline(y=1,ls=':',color='grey')
pl.axhline(y=0.5,ls=':',color='grey')
pl.axhline(y=0,ls=':',color='grey')
pl.axvline(x=0.1,ls=':',color='grey')
pl.ylim((-1,1.1))
pl.subplot(212)
pl.plot(rmses,r2s,'*')
pl.ylabel('Test R-squared')
pl.xlabel('Test normalised MAE')
pl.axhline(y=1,ls=':',color='grey')
pl.axhline(y=0.5,ls=':',color='grey')
pl.axhline(y=0,ls=':',color='grey')
pl.ylim((-1,1.1))
pl.axvline(x=0.1,ls=':',color='grey')
pl.savefig('all_scatter.pdf')
pl.close()


d=list(csv.reader(open('all_users_both.csv','r')))
rmses=[float(r[5])/float(r[2])for r in d[1:] if float(r[5])!=-1]
r2s=[float(r[7]) for r in d[1:] if float(r[5])!=-1]
trmses=[float(r[10])/float(r[2]) for r in d[1:] if float(r[5])!=-1]
tr2s=[float(r[12]) for r in d[1:] if float(r[5])!=-1]
users=[r[0] for r in d[1:] if float(r[5])!=-1]
d=[(users[i],rmses[i],r2s[i],trmses[i],tr2s[i]) for i in range(len(r2s))]
good=[r for r in d if r[1]<=0.1 or r[2]>=0.5]
groups=[good]
user_g=[['abianchi','tbusatta','dmelazzi','emarcucc','kkwapien','gbertain','sschifan','planucar'],['aspitale','gprandin'],['gcocco00','mdistefa','nspalla1','pcacciot'],['szia0000'],['bziosi00']]
for g in user_g:
    groups.append([r for r in d if r[0] in g ])

shapes=['*',u'o',u's',u'^',u'H',u'D']
colors=['green','blue','grey','brown','orange','red']
pl.figure(figsize=(6,7))
pl.subplot(211)
for i in range(len(groups)):
    pl.plot([g[3] for g in groups[i]],[g[4] for g in groups[i]],shapes[i],color=colors[i])

pl.ylabel('Train R-squared')
pl.xlabel('Train normalised MAE')
pl.axhline(y=1,ls=':',color='grey')
pl.axhline(y=0.5,ls=':',color='grey')
pl.axhline(y=0,ls=':',color='grey')
pl.axvline(x=0.1,ls=':',color='grey')
pl.ylim((-1,1.1))
pl.subplot(212)
for i in range(len(groups)):
    pl.plot([g[1] for g in groups[i]],[g[2] for g in groups[i]],shapes[i],color=colors[i])

pl.ylabel('Test R-squared')
pl.xlabel('Test normalised MAE')
pl.axhline(y=1,ls=':',color='grey')
pl.axhline(y=0.5,ls=':',color='grey')
pl.axhline(y=0,ls=':',color='grey')
pl.ylim((-1,1.1))
pl.axvline(x=0.1,ls=':',color='grey')
pl.savefig('all_scatter.pdf')
pl.close()




largeRcount=len([r for r in r2s if r>=0.5])
smallMAEcount=len([rmses[i] for i in range(len(rmses)) if rmses[i]<=0.1 and r2s[i]<0.5])
bad=[r for r in d[1:] if float(r[7])<0.5 and float(r[5])/float(r[2])>0.1]
bad_rmses=[float(r[5])for r in bad if float(r[5])!=-1]

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


###frequency
for i in range(8):
    pl.figure(figsize=(6,3))
    d=list(csv.reader(open('freq45_0_'+str(i)+'.csv','r')))
    jobts=[float(r[0]) for r in d[1:]]
    jobtsavg=np.convolve(jobts, np.ones((60,))/60, mode='valid')
    jobtimes=[float(r[2])-float(d[1][2]) for r in d[1:]]
    pl.plot(jobtimes,jobts)
    pl.plot(jobtimes[59:],jobtsavg,color='red')
    pl.xlabel('Seconds since job start')
    pl.ylabel('Average core frequency')
    pl.subplots_adjust(bottom=0.2)
    pl.savefig('freq45_0_'+str(i)+'.pdf',format='pdf')
    pl.close()




users=list(csv.reader(open('users.csv','r')))
file=open('valid_users.csv','w')
for u in users:
    print(u)
    data=list(csv.reader(gzip.open(u[0]+'_jobss.csv.gz','r')))
    data=[data[0]]+[r for r in data[1:] if r[0][:4]=='2014']
    if len(data)<1000:
        print('not enough job data for this user in the valid time points')
    else:
        job_ids=list(set([float(r[1][:-8]) for r in data[1:]]))
        job_ids.sort()
        if len(job_ids)<100:
            print('not enough jobs for this user in the valid time points')
        else:
            file.write(u[0]+'\n')
            

users=list(csv.reader(open('users.csv','r')))
N=0
for u in users:
    print(u)
    data=list(csv.reader(gzip.open(u[0]+'_jobss.csv.gz','r')))
    data=[data[0]]+[r for r in data[1:] if r[0][:4]=='2014']
    if len(data)<1000:
        print('not enough job data for this user in the valid time points')
    else:
        job_ids=list(set([float(r[1][:-8]) for r in data[1:]]))
        job_ids.sort()
        if len(job_ids)<100:
            print('not enough jobs for this user in the valid time points')
        else:
            N+=len(data)-1


###generic heatmap
column=4
file='emarcucc_times.csv'

d=list(csv.reader(open(file,'r')))
grid=np.array(d[1:],dtype=np.float)

Cs=list(set(grid[:,0]))
gammas=list(set(grid[:,2]))
epsilons=list(set(grid[:,1]))
tss=list(set(grid[:,3]))
Cs.sort()
gammas.sort()
epsilons.sort()
tss.sort()

pl.figure(figsize=(len(Cs)*4.2+1,len(epsilons)*2+1))
index=1
for e in epsilons:
    for c in Cs:
        ax=pl.subplot(len(epsilons),len(Cs),index)
        data=grid[grid[:,0]==c,:]
        data=data[data[:,2]==e,:]
        imdata=np.zeros((len(tss),len(gammas)))
        for d in data:
            imdata[tss.index(d[3]),gammas.index(d[1])]=d[column]
        
        l=ax.pcolor(imdata,vmin=0,vmax=max(grid[:,column]),shading='faceted')
        ax.set_xticks(np.arange(imdata.shape[1])+0.5, minor=False)
        ax.set_yticks(np.arange(imdata.shape[0])+0.5, minor=False)
        if e==max(epsilons):
            ax.set_xticklabels(gammas,rotation=30, ha='right')
            ax.set_xlabel('Gamma')
        else:
            ax.set_xticklabels(())
        if c==min(Cs):
            ax.set_yticklabels(tss)
            ax.set_ylabel('Time scaling factor')
        else:
            ax.set_yticklabels(())
        ax.tick_params(length=0)
        for x in range(len(tss)):
            for y in range(len(gammas)):
                if imdata[x][y]>99:
                    pl.text(y + 0.5 , x + 0.5, '%.0f' % imdata[x][y],
                         horizontalalignment='center',
                         verticalalignment='center')
                else:
                    pl.text(y + 0.5 , x + 0.5, '%.1f' % imdata[x][y],
                         horizontalalignment='center',
                         verticalalignment='center')
        
        pl.title('C='+str(c)+' Epsilon='+str(e))
        cbar = pl.colorbar(l)
        index+=1

pl.subplots_adjust(wspace=0.01,right=0.99,bottom=0.2)
pl.savefig(file+'grid.pdf', format='pdf')
pl.close()



###replot for some users
#user name, epsilon, gamma, ts,comp#
users=[['sdecherc',0.01,0.1,1.0],
       ['mmapelli',0.001,0.001,10000.0],
       ['abianchi',0.001,0.001,10000.0],
       ['dmelazzi',0.01,0.0001,1.0],
       ['emarcucc',0.001,0.1,10000.0],
       ['gbertain',0.001,.0001,1000.0],
       ['kkwapien',0.001,0.1,10000.0],
       ['sschifan',0.01,0.0001,10000.0],
       ['tbusatta',0.01,0.001,100.0],
       ['planucar',0.001,0.01,100.0],
       ['aspitale',0.01,1.0,1.0],
       ['gprandin',0.001,0.0001,100.0],
       ['bziosi00',0.01,0.1,10000.0]]

users=[['sdecherc',0.01,0.001,1.0,4],['fesposit',0.01,0.001,10000.0,3]]
for u in users:
    code='_g'+str(u[2])+'_e'+str(u[1])+'_c1.0_ts'+str(u[3])+'_comp'+str(u[4])
    nrmse,rmse,corr,r2,prediction,test_power,times,jobs=pkl.load(file=gzip.open(u[0]+'test'+code+'.pkl.gz','r'))
    #tbne,tnrmse,trmse,tcorr,tr2,tprediction,train_power,ttimes=pkl.load(file=gzip.open(u[0]+'train'+code+'.pkl.gz','r'))
    #power=list(test_power)+list(train_power)
    #avg=np.average(power)
    pl.figure(figsize=(6,2.5))
    pl.plot(test_power)
    pl.plot(prediction)
    #pl.axhline(y=avg,ls='--',color='red')
    pl.ylabel('Power (W)')
    pl.xlabel('Data point')
    if u[0]=='fesposit':
        pl.legend(('Real power','Predicted power'),loc='best',fontsize=12)
        pl.ylim((pl.ylim()[0],pl.ylim()[1]*1.25))
    #pl.title('R-squared = '+str(int(r2*1000)/1000.0)+', normalized MAE = '+str(int((rmse/avg)*1000)/1000.0))
    pl.subplots_adjust(right=0.9,bottom=0.2)
    pl.savefig(u[0]+'.pdf')
    pl.close()

                       
####avg vs svr nrmes components

month=10
components=[1,2,3,4,5]
names=['S','M','F','GPU','MIC']
for component in components:
    svr=list(csv.reader(open('all_users_components'+str(month)+'.csv','r')))
    eavg=list(csv.reader(open('all_users_components'+str(month)+'_avg.csv','r')))
    svr_data=[float(r[6])/float(r[5])for r in svr[1:] if int(r[1])==component]
    eavg_data=[float(eavg[i][2])/float(svr[i][5]) for i in range(1,len(eavg)) if int(eavg[i][1])==component]
    pl.figure(figsize=(4,3))
    pl.plot(svr_data,eavg_data,'*')
    pl.ylabel('NRMSE for EAM')
    pl.xlabel('NRMSE for SVR')
    pl.subplots_adjust(left=0.2,bottom=0.2)
    pl.yscale('log')
    pl.xscale('log')
    #pl.axhline(y=0.1,ls=':',color='grey')
    #pl.axvline(x=0.1,ls=':',color='grey')
    pl.plot((min(pl.ylim()[0],pl.xlim()[0]),max(pl.ylim()[1],pl.xlim()[1])),(min(pl.ylim()[0],pl.xlim()[0]),max(pl.ylim()[1],pl.xlim()[1])),ls=':',color='grey')
    pl.savefig('all_scatter'+str(month)+'_'+str(component)+'.pdf')
    pl.close()

for component in components:
    svr=list(csv.reader(open('all_users_components'+str(month)+'.csv','r')))
    eavg=list(csv.reader(open('all_users_components'+str(month)+'_avg.csv','r')))
    svr_data=[float(r[7])for r in svr[1:] if int(r[1])==component]
    eavg_data=[float(eavg[i][3]) for i in range(1,len(eavg)) if int(eavg[i][1])==component]
    pl.figure(figsize=(4,3))
    pl.plot(svr_data,eavg_data,'*')
    pl.ylabel('R-squared for EAM')
    pl.xlabel('R-squared for SVR')
    pl.subplots_adjust(left=0.2,bottom=0.2)
    pl.xlim((-2,1))
    pl.ylim((-2,1))
    pl.plot((min(pl.ylim()[0],pl.xlim()[0]),max(pl.ylim()[1],pl.xlim()[1])),(min(pl.ylim()[0],pl.xlim()[0]),max(pl.ylim()[1],pl.xlim()[1])),ls=':',color='grey')
    pl.savefig('all_scatterR2_'+str(month)+'_'+str(component)+'.pdf')
    pl.close()

for component in components:
    svr=list(csv.reader(open('all_users_components'+str(month)+'.csv','r')))
    eavg=list(csv.reader(open('all_users_components'+str(month)+'_avg.csv','r')))
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
    #if component<5:
    pl.text(-1.8,2,names[component-1],fontsize=14)
    #else:
    #    pl.text(-2,0.7*pl.ylim()[1],names[component-1])
    pl.axhline(y=0.2,ls=':',color='grey')
    pl.axvline(x=0.5,ls=':',color='grey')
    pl.savefig('all_scatter_both_'+str(month)+'_'+str(component)+'.pdf')
    pl.close()

    

####avg vs svr nrmes global

month=10

svr=list(csv.reader(open('all_users_global'+str(month)+'.csv','r')))
eavg=list(csv.reader(open('all_users_global'+str(month)+'avg.csv','r')))
svr_data=[float(r[3])/float(r[2])for r in svr[1:]]
eavg_data=[float(eavg[i][3])/float(svr[i][2]) for i in range(1,len(eavg))]
pl.figure(figsize=(4,3))
pl.plot(svr_data,eavg_data,'*')
pl.ylabel('NRMSE for EAM')
pl.xlabel('NRMSE for SVR')
pl.subplots_adjust(left=0.2,bottom=0.2)
pl.yscale('log')
pl.xscale('log')
#pl.axhline(y=0.1,ls=':',color='grey')
#pl.axvline(x=0.1,ls=':',color='grey')
pl.plot((min(pl.ylim()[0],pl.xlim()[0]),max(pl.ylim()[1],pl.xlim()[1])),(min(pl.ylim()[0],pl.xlim()[0]),max(pl.ylim()[1],pl.xlim()[1])),ls=':',color='grey')
pl.savefig('all_scatter'+str(month)+'.pdf')
pl.close()


svr_data=[float(r[4])for r in svr[1:] ]
eavg_data=[float(eavg[i][4]) for i in range(1,len(eavg)) ]
pl.figure(figsize=(4,3))
pl.plot(svr_data,eavg_data,'*')
pl.ylabel('R-squared for EAM')
pl.xlabel('R-squared for SVR')
pl.subplots_adjust(left=0.2,bottom=0.2)
pl.xlim((-2,1))
pl.ylim((-2,1))
pl.plot((min(pl.ylim()[0],pl.xlim()[0]),max(pl.ylim()[1],pl.xlim()[1])),(min(pl.ylim()[0],pl.xlim()[0]),max(pl.ylim()[1],pl.xlim()[1])),ls=':',color='grey')
pl.savefig('all_scatterR2_'+str(month)+'.pdf')
pl.close()



svr=list(csv.reader(open('all_users_global'+str(month)+'_noneg.csv','r')))
eavg=list(csv.reader(open('all_users_global'+str(month)+'avg.csv','r')))
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



##time hist
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


##all gpus var
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



#[1.9371853682810434, 0.14360108243813363, 1.5688362859167588, 1.5427676996211435, 0.14385991404272405, 0.11336570798403517, 1.4557097873881035, 1.7573329703323712, 1.8360769604479545, 1.4305051257165438, 1.649636775911798, 0.10457834414316422, 1.435600049289915, 1.1183826303869846, 0.13674179949032242, 0.12571269687550671, 1.4473556513447507, 1.7531762600488534, 1.5057993850266804, 1.7616314247910101, 1.7588042742578953, 1.5371511718278164, 1.8190037747581922, 1.8037935180640712, 1.7800313311370044, 1.8585335321510086, 1.7597186203009076, 1.8031505159284666, 1.8188289746528064, 1.6454430201356418, 1.8336569631688027, 0.14126074255349197, 1.6068262166027001, 1.5964247632428137, 1.2567713265548968, 0.17950129152387465, 0.69273796483882377, 0.82730367364589885, 1.2177974554120357, 0.61641737710511102, 1.5069532251405902, 0.91087809605983316, nan, 1.0170370924829291, 0.14489709386200089, 0.55842021186832391, 0.78366300811151279, 0.6934732347092335, 0.78019814474326299, 0.72023025546511177, 0.14883140452122287, 1.4228501716554378, 0.064049908703878361, 0.22805207111139408, 1.2568220943809199, 0.57107800015179544, 0.77803028560911835, 0.79063641535170048]


####percentage var for all users

file=open('var_points10.csv','w')
out=csv.writer(file)
out.writerow(('user','variable points', 'total points','percentage'))
users=list(csv.reader(open('users10_global.txt','r')))
users=[u[0] for u in users]
#users=['asaetti0','bziosi00','epapaleo','mcerini0','gprandin','dburatto','planucar']
bad_jobs=list(csv.reader(open('jobs_variable_nodes.csv','r')))
bad_jobs=[e[0] for e in bad_jobs]
for u in users:
    print(u)
    data=list(csv.reader(gzip.open('data/'+u+'_jobs.csv.gz','r')))
    apply_jobs=[r[1] for r in data[1:] if r[0][:4]=='2014' and int(r[0][5:7])==month]
    bad_apply_jobs=[j for j in apply_jobs if j in bad_jobs]
    out.writerow((u,len(bad_apply_jobs),len(apply_jobs),float(len(bad_apply_jobs))/len(apply_jobs)))

file.close()             

