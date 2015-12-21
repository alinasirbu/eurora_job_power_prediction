
##########################
######First save data from EuroraMeasurements database into csv files
######This requres access to CINECA systems (information on [host] and [port]) and the database itself [username] and [password]

#save power data
mysql -u [username] -h [host] -P [port] -D EuroraMeasurements -p[password] -B -e "select timestamp, DCoutVolt*DCoutCurr from powerSupply_measurements" | sed 's/\t/,/g'>power.csv
gzip power.csv


#save CPU data (one file per node)
cpus=('01' '02' '03' '04' '05' '06' '07' '08' '09' '10' '11' '12' '13' '14' '15' '16' '17' '18' '19' '20' '21' '22' '23' '24' '25' '26' '27' '28' '29' '30' '31' '32' '33' '34' '35' '36' '37' '38' '39' '40' '41' '42' '43' '44' '45' '46' '47' '48' '49' '50' '51' '52' '53' '54' '55' '56' '57' '58' '59' '60' '61' '62' '63' '64')
for cpu in ${cpus[*]};
do
echo $cpu
mysql -u [username] -h [host] -P [port] -D EuroraMeasurements -p[password] -B -e "select $cpu, cpu_id, timestamp, pow_pkg+pow_dram from cpu_measurements_0$cpu "| sed 's/\t/,/g'>cpu$cpu.csv
gzip cpu$cpu.csv
done

#save GPU data (one file per node) - only last 32 nodes have gpus
gpus=('33' '34' '35' '36' '37' '38' '39' '40' '41' '42' '43' '44' '45' '46' '47' '48' '49' '50' '51' '52' '53' '54' '55' '56' '57' '58' '59' '60' '61' '62' '63' '64')
for gpu in ${gpus[*]};
do
echo $gpu
 mysql -u [username] -h [host] -P [port] -D EuroraMeasurements -p[password] -B -e "select $gpu,gpu_id, timestamp, pow from gpu_measurements_0$gpu "| sed 's/\t/,/g'>gpu$gpu.csv
gzip gpu$gpu.csv
done


#save MIC data (one file per node) - only first 32 nodes have mics
mics=('01' '02' '03' '04' '05' '06' '07' '08' '09' '10' '11' '12' '13' '14' '15' '16' '17' '18' '19' '20' '21' '22' '23' '24' '25' '26' '27' '28' '29' '30' '31' '32')
for mic in ${mics[*]};
do
echo $mic
mysql -u [username] -h [host] -P [port] -D EuroraMeasurements -p[password] -B -e "select $mic,mic_id, timestamp, total_power from mic_measurements_0$mic "| sed 's/\t/,/g'>mic$mic.csv
gzip mic$mic.csv
done

#save jobs
mysql -u [username] -h [host] -P [port] -D EuroraMeasurements -p[password] -B -e "select * from jobs" | sed 's/\t/,/g'>jobs.csv
gzip jobs.csv

#save information on where jobs are running
mysql -u [username] -h [host] -P [port] -D EuroraMeasurements -p[password] -B -e "select * from jobs_to_nodes" | sed 's/\t/,/g'>job_nodes.csv
gzip job_nodes.csv


##################upload manually to google cloud to bucket [bucket]

##################import to big query  into your own project [project_name]

#create new dataset eurora2
bq mk [project_name]:eurora2

#import jobs
bq --project_id diecicolli-hrd load --max_bad_records=2 --source_format=CSV eurora2.intermediate gs://eurora_low_level/jobs.csv.gz id:integer,job_id:string,job_name:string,queue:string,submit:timestamp,start:timestamp,end:string,user:string,nodes:integer,cpus:integer,mem:integer,wtime:string,deleted:string,dependency:string,exit_status:string,pbs_exit_code:string

#transform the string end date to timestamp end date
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.jobs "select id,job_id,job_name,queue,submit,start,if(end='0000-00-00 00:00:00',null,timestamp(end)) as finish,user,nodes,cpus,mem,wtime,deleted,dependency,exit_status,pbs_exit_code from eurora2.intermediate"

########job_nodes
bq --project_id diecicolli-hrd load --max_bad_records=2 --source_format=CSV eurora2.job_nodes gs://eurora_low_level/job_nodes.csv.gz id:integer,node_id:integer,job_id:string,ncpus:integer,ngpus:integer,nmics:integer,mem:integer


########power
bq --project_id diecicolli-hrd load --max_bad_records=2 --source_format=CSV eurora2.power gs://eurora_low_level/power.csv.gz time:timestamp,power:float


#######cpu measurements
bq --project_id diecicolli-hrd load --max_bad_records=64 --source_format=CSV eurora2.cpu gs://eurora_low_level/cpu*.csv.gz node:integer,cpu_id:integer,time:timestamp,power:float


#######gpu measurements
bq --project_id diecicolli-hrd load --max_bad_records=64 --source_format=CSV eurora2.gpu gs://eurora_low_level/gpu*.csv.gz node:integer,gpu_id:integer,time:timestamp,power:float


#######mic measurements
bq --project_id diecicolli-hrd load --max_bad_records=64 --source_format=CSV eurora2.mic gs://eurora_low_level/mic*.csv.gz node:integer,mic_id:integer,time:timestamp,power:float


###########features for high level model

#######extract valid power (unique)
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.power_unique "SELECT time, power*-1 as power FROM eurora2.power group by time,power"

###create time points (1st april to 31st july)
 bq --project_id diecicolli-hrd  query --allow_large_results --destination_table=eurora2.aux "select time, ROW_NUMBER() OVER() from  eurora2.cpu limit 140256"

 bq --project_id diecicolli-hrd  query --allow_large_results --destination_table=eurora2.times "select date_add(timestamp('2014-04-01 00:00:00 UTC'),5*(f0_),'MINUTE') as time from  eurora2.aux"


####for each time moment, find, for each node, how many cores, gpus, mics are used

#first inner join of jobs and job_nodes to make cross join faster - correct finish time ,  CORRECT duplicate job_nodes (select min(finish) will remove those with null if duplicates)
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.job_nodes_complete "SELECT t1.node_id as node_id, t1.job_id as job_id, t1.ncpus as ncpus, t1.ngpus as ngpus, t1.nmics as nmics, t1.mem as mem, t2.job_name as job_name, t2.start as start,min(t2.finish) as finish, t2.user as user, min(t2.wtime) as wtime, min(t2.exit_status) as exit_status FROM eurora2.job_nodes t1 inner join each eurora2.jobs t2 on t1.job_id=t2.job_id group by node_id,job_id,ncpus,ngpus,nmics,mem,job_name,start,user"


#some null still remaining
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.job_nodes_complete_corrected "SELECT t1.node_id as node_id, t1.job_id as job_id, t1.ncpus as ncpus, t1.ngpus as ngpus, t1.nmics as nmics, t1.mem as mem, t1.job_name as job_name, t1.start as start, if(t1.finish is null,if(t1.exit_status='RUN',date_add(t1.start,if(t1.wtime='NA',0,60*INTEGER(LEFT(t1.wtime,2))+INTEGER(RIGHT(t1.wtime,2))),'MINUTE'),t1.start),t1.finish) as finish, t1.user as user FROM eurora2.job_nodes_complete t1"


###this one times out, try month by month
bq --project_id diecicolli-hrd  query --dry_run --replace --allow_large_results --destination_table=eurora2.nodes_components_used "SELECT t1.time as time, t2.node_id as node_id, sum(t2.ncpus) as ncpus, sum(t2.ngpus) as ngpus, sum(nmics) as nmics FROM  eurora2.job_nodes_complete_corrected t2 cross join (select time from eurora2.power_unique where minute(t1.time)%5=0) t1 where t1.time between t2.start and date_add(t2.finish,-1,'second') or (t1.time>=t2.start and t2.finish is null) group by time, node_id "

starts=("2014-04-01 00:00:00 UTC" "2014-05-01 00:00:00 UTC" "2014-06-01 00:00:00 UTC" "2014-07-01 00:00:00 UTC" "2014-08-01 00:00:00 UTC" "2014-09-01 00:00:00 UTC" "2014-10-01 00:00:00 UTC" "2014-11-01 00:00:00 UTC" "2014-12-01 00:00:00 UTC" "2015-01-01 00:00:00 UTC" "2015-02-01 00:00:00 UTC" "2015-03-01 00:00:00 UTC" "2015-04-01 00:00:00 UTC" "2015-05-01 00:00:00 UTC" "2015-06-01 00:00:00 UTC" "2015-07-01 00:00:00 UTC")
ends=("2014-04-30 23:59:59 UTC" "2014-05-31 23:59:59 UTC" "2014-06-30 23:59:59 UTC" "2014-07-31 23:59:59 UTC" "2014-08-31 23:59:59 UTC" "2014-09-30 23:59:59 UTC" "2014-10-31 23:59:59 UTC" "2014-11-30 23:59:59 UTC" "2014-12-31 23:59:59 UTC" "2015-01-31 23:59:59 UTC" "2015-02-28 23:59:59 UTC" "2015-03-31 23:59:59 UTC" "2015-04-30 23:59:59 UTC" "2015-05-31 23:59:59 UTC" "2015-06-30 23:59:59 UTC" "2015-07-31 23:59:59 UTC")
for i in `seq 0 15`
do
start="${starts[$i]}"
end="${ends[$i]}"
echo $start
echo $end
bq --project_id diecicolli-hrd  query  --replace --allow_large_results --destination_table=eurora2.nodes_components_used_$i "SELECT t1.time as time, t2.node_id as node_id, sum(t2.ncpus) as ncpus, sum(t2.ngpus) as ngpus, sum(nmics) as nmics FROM  (select * from eurora2.job_nodes_complete_corrected where start<=TIMESTAMP('$end') and (finish >=TIMESTAMP('$start') or finish is null)) t2 cross join (select time from eurora2.times where time between TIMESTAMP('$start') and TIMESTAMP('$end')) t1 where t1.time between t2.start and date_add(t2.finish,-1,'second') or (t1.time>=t2.start and t2.finish is null) group by time, node_id " &
sleep 5
done 

##group all into 1 table
tables='eurora2.nodes_components_used_0'
for i in `seq 1 15`
do
tables=$tables', eurora2.nodes_components_used_'$i' '
done
bq --project_id diecicolli-hrd  query  --replace --allow_large_results --destination_table=eurora2.nodes_components_used "SELECT * FROM  $tables" &

###in this table some nodes have over 16 cores /2 gpus/2 mics used (only 732 instances so I cap the values to 16,2,2)
bq --project_id diecicolli-hrd  query  --replace --allow_large_results --destination_table=eurora2.nodes_components_used_capped "SELECT time, node_id, if(ncpus>16,16,ncpus) as ncpus, if(ngpus>2,2,ngpus) as ngpus, if(nmics>2,2,nmics) as nmics FROM  eurora2.nodes_components_used" &


####for each time moment, find, for each node, total power for cores, gpus, mics 

bq --project_id diecicolli-hrd  query --replace  --allow_large_results --destination_table=eurora2.nodes_total_power_cpu "SELECT t1.time as time, t2.node as node_id, avg(t2.power)*2 as cpu_power FROM  (select * from eurora2.cpu where (second(time) between 56 and 59 or second(time)=0) and minute(time)%5 in (0,4) and power<1000) t2 cross join eurora2.times t1 where (TIMESTAMP_TO_SEC(t1.time)-TIMESTAMP_TO_SEC(t2.time)) between 0 and 4 group by time, node_id "

bq --project_id diecicolli-hrd  query --replace  --allow_large_results --destination_table=eurora2.nodes_total_power_cpu_after "SELECT t1.time as time, t2.node as node_id, avg(t2.power)*2 as cpu_power FROM  (select * from eurora2.cpu where (second(time) between 1 and 5) and minute(time)%5=0 and power<1000) t2 cross join eurora2.times t1 where (TIMESTAMP_TO_SEC(t2.time)-TIMESTAMP_TO_SEC(t1.time)) between 0 and 4 group by time, node_id "

bq --project_id diecicolli-hrd  query --replace  --allow_large_results --destination_table=eurora2.nodes_total_power_gpu "SELECT t1.time as time, t2.node as node_id, avg(t2.power)*2 as gpu_power FROM  (select * from eurora2.gpu where (second(time) between 55 and 59 or second(time)=0) and minute(time)%5 in (0,4)) t2 cross join eurora2.times t1 where(TIMESTAMP_TO_SEC(t1.time)-TIMESTAMP_TO_SEC(t2.time)) between 0 and 4 group by time, node_id "

bq --project_id diecicolli-hrd  query --replace  --allow_large_results --destination_table=eurora2.nodes_total_power_gpu_after "SELECT t1.time as time, t2.node as node_id, avg(t2.power)*2 as gpu_power FROM  (select * from eurora2.gpu where (second(time) between 1 and 5) and minute(time)%5=0) t2 cross join eurora2.times t1 where(TIMESTAMP_TO_SEC(t2.time)-TIMESTAMP_TO_SEC(t1.time)) between 0 and 4 group by time, node_id "

bq --project_id diecicolli-hrd  query --replace  --allow_large_results --destination_table=eurora2.nodes_total_power_mic "SELECT t1.time as time, t2.node as node_id, avg(t2.power)*2 as mic_power FROM  (select * from eurora2.mic where (second(time) between 55 and 59 or second(time)=0) and minute(time)%5 in (0,4)) t2 cross join eurora2.times t1 where (TIMESTAMP_TO_SEC(t1.time)-TIMESTAMP_TO_SEC(t2.time)) between 0 and 4 group by time, node_id "

bq --project_id diecicolli-hrd  query --replace  --allow_large_results --destination_table=eurora2.nodes_total_power_mic_after "SELECT t1.time as time, t2.node as node_id, avg(t2.power)*2 as mic_power FROM  (select * from eurora2.mic where (second(time) between 1 and 5) and minute(time)%5=0) t2 cross join eurora2.times t1 where (TIMESTAMP_TO_SEC(t2.time)-TIMESTAMP_TO_SEC(t1.time)) between 0 and 4 group by time, node_id "


######combine the two - have a table with time, node_id, cores_used, gpus used, mics used, total_cpu_power, total_gpu_power, total_mic_power 
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.nodes "SELECT time, row_number() over() from eurora2.mic limit 64 "
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.nodes "SELECT f0_ as node_id from eurora2.nodes "

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.time_nodes "SELECT t1.time as time, t2.node_id as node_id FROM  eurora2.nodes t2 cross join eurora2.times t1  "

##include null where there is missing data - use left join
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.time_nodes_used_components_total_power "SELECT t1.time as time, t1.node_id as node_id, t2.ncpus as cores_used, t2.ngpus as gpus_used, t2.nmics as mics_used, t3.cpu_power as cpu_total_power, t4.gpu_power as gpu_total_power, t5.mic_power as mic_total_power, t6.cpu_power as cpu_total_power_after, t7.gpu_power as gpu_total_power_after, t8.mic_power as mic_total_power_after FROM  eurora2.time_nodes t1 left join each eurora2.nodes_components_used_capped t2 on t1.time=t2.time and t1.node_id=t2.node_id left join each eurora2.nodes_total_power_cpu t3 on t1.time=t3.time and t1.node_id=t3.node_id left join each eurora2.nodes_total_power_gpu t4 on t1.time=t4.time and t1.node_id=t4.node_id left join each eurora2.nodes_total_power_mic t5 on t1.time=t5.time and t1.node_id=t5.node_id left join each eurora2.nodes_total_power_cpu_after t6 on t1.time=t6.time and t1.node_id=t6.node_id left join each eurora2.nodes_total_power_gpu_after t7 on t1.time=t7.time and t1.node_id=t7.node_id left join each eurora2.nodes_total_power_mic_after t8 on t1.time=t8.time and t1.node_id=t8.node_id"

##choose non null between before and after
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.time_nodes_used_components_total_power "SELECT time, node_id,cores_used,gpus_used, mics_used, if(cpu_total_power is null,cpu_total_power_after,cpu_total_power) as cpu_total_power, if(gpu_total_power is null, gpu_total_power_after,gpu_total_power) as gpu_total_power, if( mic_total_power is null,mic_total_power_after,mic_total_power) as mic_total_power FROM  eurora2.time_nodes_used_components_total_power"


###estimate idle power for each component:
SELECT floor(power) as power, count(*) as count FROM [eurora2.cpu] group by power order by power desc
SELECT floor(power) as power, count(*) as count FROM [eurora2.gpu] group by power order by power desc
SELECT floor(power) as power, count(*) as count FROM [eurora2.mic] group by power order by power desc
###select value with largest frequency, or an average between the top 2 
core_power =19.5/8=2.4 (44/16 = 2.75 including dram)
gpu_power=12.5
mic_power=100

8used
56 idle
5


###correct data:

###NODES DOWN !!!!!!!!!
##node is down when cores_used is null and gpus_used is null and mics_used is null and cpu_total_power is null and gpu_total_power is null and mic_total_power is null 
###set everything to 0

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.time_nodes_used_components_total_power_nodes_down "SELECT time, node_id, if(cores_used is null and gpus_used is null and mics_used is null and cpu_total_power is null and gpu_total_power is null and mic_total_power is null,0, cores_used) as cores_used, if(cores_used is null and gpus_used is null and mics_used is null and cpu_total_power is null and gpu_total_power is null and mic_total_power is null,0,gpus_used) as gpus_used,if(cores_used is null and gpus_used is null and mics_used is null and cpu_total_power is null and gpu_total_power is null and mic_total_power is null,0,mics_used) as mics_used, if(cores_used is null and gpus_used is null and mics_used is null and cpu_total_power is null and gpu_total_power is null and mic_total_power is null,0,cpu_total_power) as cpu_total_power, if(cores_used is null and gpus_used is null and mics_used is null and cpu_total_power is null and gpu_total_power is null and mic_total_power is null,0,gpu_total_power) as gpu_total_power, if(cores_used is null and gpus_used is null and mics_used is null and cpu_total_power is null and gpu_total_power is null and mic_total_power is null,0,mic_total_power) as mic_total_power  FROM  eurora2.time_nodes_used_components_total_power"



###null power can be 0 if component missing (mic or gpu) or  idle or 0 (mic) if component unused  - if component is used invalidate by setting to -1
###null components are always 0
##separate low, med and high cpus
##invalidate aparently idle components that consume too much power NO DONT'T DO THIS - removes all data


bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.time_nodes_used_components_total_power_nodes_down_corrected_mic_idle "SELECT time, node_id, if(node_id<17 or node_id between 25 and 32, if(cores_used is null,0,cores_used),0) as cores_low_used,if(node_id between 17 and 24, if(cores_used is null,0,cores_used),0) as cores_med_used, if(node_id>32, if(cores_used is null,0,cores_used),0) as cores_high_used, if(gpus_used is null,0,gpus_used) as gpus_used, if(mics_used is null,0,mics_used) as mics_used,if(node_id<17 or node_id between 25 and 32, if(cpu_total_power is null,if(cores_used is null or cores_used=0,44,-1),cpu_total_power),0) as cpu_low_total_power,if(node_id between 17 and 24,if(cpu_total_power is null,if(cores_used is null or cores_used=0,44,-1),cpu_total_power),0) as cpu_med_total_power, if(node_id>32, if(cpu_total_power is null,if(cores_used is null or cores_used=0,44,-1),cpu_total_power), 0) as cpu_high_total_power, if(node_id<33,0,if(gpu_total_power is null, if(gpus_used is null or gpus_used=0,25,-1),gpu_total_power)) as gpu_total_power,if(node_id>32,0,if(mic_total_power is null,if(mics_used is null or mics_used=0,200,-1),mic_total_power)) as mic_total_power FROM  eurora2.time_nodes_used_components_total_power_nodes_down "


########extract idle power for system

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.system_idle_power_nodes_down_mics_idle "SELECT time, sum(if(cores_low_used=0,cpu_low_total_power,2.75*(16-cores_low_used))) as cores_low_power, sum(if(cores_med_used=0,cpu_med_total_power,2.75*(16-cores_med_used))) as cores_med_power, sum(if(cores_high_used=0,cpu_high_total_power,2.75*(16-cores_high_used))) as cores_high_power, sum(if(gpus_used=0,gpu_total_power,12.5*(2-gpus_used))) as gpus_power, sum(if(mics_used=0,mic_total_power,100.0*(2-mics_used))) as mics_power FROM  eurora2.time_nodes_used_components_total_power_nodes_down_corrected_mic_idle group by time"


#######extract used components for system
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.system_used_components "SELECT time, sum(cores_low_used) as cores_low_used, sum(cores_med_used) as cores_med_used, sum(cores_high_used) as cores_high_used, sum(gpus_used) as gpus_used, sum(mics_used) as mics_used FROM eurora2.time_nodes_used_components_total_power_nodes_down_corrected_mic_idle group by time"


########extract used power for system
#first total power

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.system_total_power_nodes_down_mics_idle "SELECT time, sum(cpu_low_total_power) as cores_low_power, sum(cpu_med_total_power) as cores_med_power, sum(cpu_high_total_power) as cores_high_power, sum(gpu_total_power) as gpus_power, sum(mic_total_power) as mics_power FROM  eurora2.time_nodes_used_components_total_power_nodes_down_corrected_mic_idle group by time"


#then compute used as total-idle

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.system_used_power_nodes_down_mics_idle "SELECT t1.time as time, t1.cores_low_power-t2.cores_low_power as cores_low_power, t1.cores_med_power-t2.cores_med_power as cores_med_power, t1.cores_high_power-t2.cores_high_power as cores_high_power, t1.gpus_power-t2.gpus_power as gpus_power, t1.mics_power-t2.mics_power as mics_power FROM  eurora2.system_total_power_nodes_down_mics_idle t1 inner join each eurora2.system_idle_power_nodes_down_mics_idle t2 on t1.time=t2.time"


###extract valid times - when all measures are available after correction

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.valid_times "SELECT time, min(cpu_low_total_power) as cl, min(cpu_med_total_power) as cm, min(cpu_high_total_power) as ch, min(gpu_total_power) as g, min(mic_total_power) as m FROM  eurora2.time_nodes_used_components_total_power_nodes_down_corrected_mic_idle  group by time having cl!=-1 and cm !=-1 and ch !=-1 and g!=-1 and m !=-1"


##one table with all valid data

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.system_power_data_nodes_down_mics_idle "SELECT t1.time as time, t2.power as system_power, t3.cores_low_used as cores_low_used, t3.cores_med_used as cores_med_used, t3.cores_high_used as cores_high_used, t3.gpus_used as gpus_used, t3.mics_used as mics_used, t4.cores_low_power as cores_low_power_used, t4.cores_med_power as cores_med_power_used, t4.cores_high_power as cores_high_power_used, t4.gpus_power as gpus_power_used, t4.mics_power as mics_power_used , t5.cores_low_power as cores_low_power_idle, t5.cores_med_power as cores_med_power_idle, t5.cores_high_power as cores_high_power_idle, t5.gpus_power as gpus_power_idle, t5.mics_power as mics_power_idle from eurora2.valid_times t1 left join each eurora2.power_unique t2 on t1.time=t2.time left join each eurora2.system_used_components t3 on t1.time=t3.time left join each eurora2.system_used_power_nodes_down_mics_idle t4 on t4.time=t1.time left join each eurora2.system_idle_power_nodes_down_mics_idle t5 on t5.time=t1.time "


###check correlations
SELECT corr(system_power,cores_low_used),
corr(system_power,cores_med_used),
corr(system_power,cores_high_used),
corr(system_power,gpus_used),
corr(system_power,mics_used),
corr(system_power,cores_low_power_used),
corr(system_power,cores_med_power_used),
corr(system_power,cores_high_power_used),
corr(system_power,gpus_power_used),
corr(system_power,mics_power_used),
corr(system_power,cores_low_power_idle),
corr(system_power,cores_med_power_idle),
corr(system_power,cores_high_power_idle),
corr(system_power,gpus_power_idle),
corr(system_power,mics_power_idle),
corr(system_power,cores_low_power_used+cores_med_power_used+cores_high_power_used+gpus_power_used+mics_power_used+cores_low_power_idle+cores_med_power_idle+cores_high_power_idle+gpus_power_idle+mics_power_idle)
FROM [eurora2.system_power_data_nodes_down_mics_idle] 
where system_power>0 and cores_med_used+cores_low_used+cores_high_used+gpus_used+mics_used>0


####download the data
bq --project_id diecicolli-hrd extract eurora2.system_power_data_nodes_down_mics_idle gs://eurora_low_level/system_data_nodes_down_mics_idle.csv
gsutil cp gs://eurora_low_level/system_data_nodes_down_mics_idle.csv ./system_data_nodes_down_mics_idle.csv
gzip system_data_nodes_down_mics_idle.csv




#####user data usage by job
users=$(<users1.csv)
for user in $users 
do 

echo $user

###find number of components used per node per job and time from start
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.nodes_components_used_$user "SELECT t1.time as time, t2.node_id as node_id, t2.job_id as job_id, t2.job_name as job_name, sum(t2.ncpus) as ncpus, sum(t2.ngpus) as ngpus, sum(t2.nmics) as nmics, avg(TIMESTAMP_TO_SEC(t1.time)-TIMESTAMP_TO_SEC(t2.start)) as runtime FROM  (select * from eurora2.job_nodes_complete_corrected where user like '$user%') t2 cross join eurora2.times  t1 where t1.time between t2.start and date_add(t2.finish,-1,'second') group by time, node_id, job_id,job_name "


###add power to no of comps used per node per job
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.nodes_$user "SELECT t1.time as time, t1.node_id as node_id, t1.job_id as job_id, t1.job_name as job_name, t1.runtime as runtime, if(t1.node_id<17 or t1.node_id between 25 and 32, t1.ncpus,0) as cores_low, if(t1.node_id between 17 and 24, t1.ncpus,0) as cores_med, if(t1.node_id>32, t1.ncpus,0) as cores_high, t1.ngpus as ngpus, t1.nmics as nmics,  if(t1.node_id<17 or t1.node_id between 25 and 32, if(t1.ncpus=0,0,((t2.cpu_low_total_power-((16-t2.cores_low_used)*2.7))/t2.cores_low_used*t1.ncpus)),0) as cpu_low_power, if(t1.node_id between 17 and 24, if(t1.ncpus=0,0,((t2.cpu_med_total_power-((16-t2.cores_med_used)*2.7))/t2.cores_med_used*t1.ncpus)),0) as cpu_med_power, if(t1.node_id>32, if(t1.ncpus=0,0,((t2.cpu_high_total_power-((16-t2.cores_high_used)*2.7))/t2.cores_high_used*t1.ncpus)),0) as cpu_high_power, if(t1.ngpus=0,0,((t2.gpu_total_power-((2-t2.gpus_used)*12.5))/t2.gpus_used*t1.ngpus)) as gpu_power, if(t1.nmics=0,0,((t2.mic_total_power-((2-t2.mics_used)*100))/t2.mics_used*t1.nmics)) as mic_power, if(t1.node_id<17 or t1.node_id between 25 and 32, t2.cores_low_used-t1.ncpus,0) as cores_low_shared, if( t1.node_id between 17 and 24, t2.cores_med_used-t1.ncpus,0) as cores_med_shared, if(t1.node_id>32 , t2.cores_high_used-t1.ncpus,0) as cores_high_shared,t2.gpus_used-t1.ngpus as ngpus_shared, t2.mics_used-t1.nmics as nmics_shared FROM eurora2.nodes_components_used_$user t1 left outer join each eurora2.time_nodes_used_components_total_power_nodes_down_corrected_mic_idle t2 on t1.time=t2.time and t1.node_id=t2.node_id where t2.cpu_med_total_power!=-1 and t2.cpu_low_total_power!=-1 and t2.cpu_high_total_power!=-1 and t2.gpu_total_power!=-1 and t2.mic_total_power!=-1 "


#sum to total power per job per component
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.${user}_jobs "SELECT time, job_id, job_name, sum(cpu_low_power) as cpu_low_power,sum(cpu_med_power) as cpu_med_power,sum(cpu_high_power) as cpu_high_power, sum(gpu_power) as gpu_power, sum(mic_power) as mic_power, avg(runtime) as runtime, sum(cores_low) as cores_low, sum(cores_med) as cores_med, sum(cores_high) as cores_high, sum(ngpus) as ngpus, sum(nmics) as nmics , sum(cores_low_shared) as cores_low_shared, sum(cores_med_shared) as cores_med_shared,sum(cores_high_shared) as cores_high_shared,sum(ngpus_shared) as ngpus_shared,sum(nmics_shared) as nmics_shared, count(*) as nnodes FROM eurora2.nodes_$user group by time,job_id,job_name "

###CORRECT for missing records
#first compute max components per job
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.${user}_jobs_max "SELECT job_id,job_name,max(cores_low) as cores_low, max(cores_med) as cores_med, max(cores_high) as cores_high, max(ngpus) as ngpus, max(nmics) as nmics, max(nnodes) as nnodes FROM eurora2.${user}_jobs group by job_id, job_name "

#then remove points where number of components smaller
#also remove jobs with mic>0 and date < 17 June 2014
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.${user}_jobs "SELECT t1.time as time, t1.job_id as job_id, t1.job_name as job_name, t1.cpu_low_power as cpu_low_power,t1.cpu_med_power as cpu_med_power,t1.cpu_high_power as cpu_high_power, t1.gpu_power as gpu_power, t1.mic_power as mic_power, t1.runtime as runtime, t1.cores_low as cores_low, t1.cores_med as cores_med, t1.cores_high as cores_high, t1.ngpus as ngpus, t1.nmics as nmics , t1.cores_low_shared as cores_low_shared, t1.cores_med_shared as cores_med_shared,t1.cores_high_shared as cores_high_shared,t1.ngpus_shared as ngpus_shared,t1.nmics_shared as nmics_shared, t1.nnodes as nnodes FROM eurora2.${user}_jobs t1 inner join  eurora2.${user}_jobs_max t2 on t1.job_id=t2.job_id and t1.job_name=t2.job_name where t1.cores_low=t2.cores_low and  t1.cores_med=t2.cores_med and t1.cores_high=t2.cores_high and t1.ngpus=t2.ngpus and t1.nmics=t2.nmics and t1.nnodes=t2.nnodes and (t1.nmics=0 or t1.time>'2014-06-17 23:59:59 UTC') "


bq --project_id diecicolli-hrd extract eurora2.${user}_jobs gs://eurora_low_level/${user}_jobs.csv
gsutil cp gs://eurora_low_level/${user}_jobs.csv ./${user}_jobs.csv
gzip ${user}_jobs.csv

sleep 1

done


#job list for each valid time point

#unique jobs corrected
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.jobs_corrected "SELECT job_id, job_name,start,finish,user FROM [eurora2.job_nodes_complete_corrected] group by job_id, job_name,start,finish,user"

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.system_time_jobs "SELECT t1.time as time, group_concat( concat(left(t2.user,8),t2.job_id),';') as jobs FROM    eurora2.jobs_corrected t2 cross join eurora2.valid_times t1 where t1.time between t2.start and t2.finish group by time order by time"

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.users_sept "SELECT left(user,8) as user FROM eurora2.jobs_corrected where month(start)=9 or month(finish)=9 group by user "

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.users_oct "SELECT left(user,8) as user FROM eurora2.jobs_corrected where month(start)=10 or month(finish)=10 group by user "



#find average power per used component global
SELECT avg(cores_low_power_used/cores_low_used), avg(cores_med_power_used/cores_med_used), avg(cores_high_power_used/cores_high_used) ,
avg(gpus_power_used/gpus_used), avg(mics_power_used/mics_used) 
FROM [eurora2.system_power_data_nodes_down_mics_idle] where month(time)<9 and year(time)=2014


#find average power per used component per user - create one table with all users at the end
#first put all job data into one table
users=$(<data/users.csv)

tables=""

for user in $users 
do 
echo $user
tables=${tables}"(SELECT '${user}' as user, * FROM [eurora2.${user}_jobs])," 

done

bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.all_user_jobs "SELECT * FROM $tables" 	 


bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.avg_user_sep "SELECT user,avg(cpu_low_power/cores_low), avg(cpu_med_power/cores_med), avg(cpu_high_power/cores_high),avg(gpu_power/ngpus), avg(mic_power/nmics) FROM eurora2.all_user_jobs where month(time)<9 and year(time)=2014 group by user" 	 

bq --project_id diecicolli-hrd extract eurora2.avg_user_sep gs://eurora_low_level/avg_user_9.csv
gsutil cp gs://eurora_low_level/avg_user_9.csv ./avg_user_9.csv




users=$(<users9.csv)
for user in $users 
do 
echo $user
python one_user_apply.py $user 9 
done



###power vs load for all cpus and gpus

##download core info
cpus=('02' '03' '04' '06' '07' '08' '09' '10' '11' '12' '13' '14' '15' '16' '17' '19' '21' '22' '23' '24' '25' '26' '27' '28' '29' '30' '31' '32' '33' '34' '35' '36' '37' '38' '39' '40' '41' '42' '43' '44' '45' '46' '47' '48' '49' '51' '52' '53' '54' '55' '56' '57' '58' '59' '60' '61' '62' '63')
for cpu in ${cpus[*]};
do
echo $cpu
mysql -u [username] -h [host] -P [port] -D EuroraMeasurements -p[password] -B -e "select core_id,load_core,timestamp from core_measurements_full_0$cpu "| sed 's/\t/,/g'>cores0$cpu.csv
gzip cores0$cpu.csv
done



#create bigquery tables
for cpu in ${cpus[*]};
do
echo $cpu
bq --project_id diecicolli-hrd load --max_bad_records=64 --source_format=CSV eurora2.cores0$cpu gs://eurora_low_level/cores0$cpu.csv.gz core_id:integer,load_core:float,time:timestamp	&
sleep 10
done


#create load tables

for cpu in ${cpus[*]};
do
echo $cpu
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.load_cpu0_$cpu "SELECT t1.time as time, avg(t2.load_core) as load, t1.power as power from eurora2.cpu t1 inner join each eurora2.cores0$cpu t2 on t1.time=t2.time where t1.node=$cpu and t1.cpu_id=0 and t2.core_id<8 group by time, power" &
sleep 20
done


for cpu in ${cpus[*]};
do
echo $cpu
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.load_cpu1_$cpu "SELECT t1.time as time, avg(t2.load_core) as load, t1.power as power from eurora2.cpu t1 inner join each eurora2.cores0$cpu t2 on t1.time=t2.time where t1.node=$cpu and t1.cpu_id=1 and t2.core_id>7 group by time, power" &
sleep 10
done



cpus=('01' '05' '18' '20' '50' '64')
for cpu in ${cpus[*]};
do
echo $cpu
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.load_cpu0_$cpu "SELECT t1.time as time, avg(t2.load_core) as load, t1.power as power from eurora2.cpu t1 inner join each eurora2.cores0$cpu t2 on t1.time=t2.timestamp where t1.node=$cpu and t1.cpu_id=0 and t2.core_id<8 group by time, power" &
sleep 20
done


for cpu in ${cpus[*]};
do
echo $cpu
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.load_cpu1_$cpu "SELECT t1.time as time, avg(t2.load_core) as load, t1.power as power from eurora2.cpu t1 inner join each eurora2.cores0$cpu t2 on t1.time=t2.timestamp where t1.node=$cpu and t1.cpu_id=1 and t2.core_id>7 group by time, power"
sleep 20
done



cpus=('01' '02' '03' '04' '05' '06' '07' '08' '09' '10' '11' '12' '13' '14' '15' '16' '17' '18' '19' '20' '21' '22' '23' '24' '25' '26' '27' '28' '29' '30' '31' '32' '33' '34' '35' '36' '37' '38' '39' '40' '41' '42' '43' '44' '45' '46' '47' '48' '49' '50' '51' '52' '53' '54' '55' '56' '57' '58' '59' '60' '61' '62' '63' '64')

#compute avg and std
for cpu in ${cpus[*]};
do
echo $cpu
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.load0_avg_cpu$cpu "SELECT integer(load) as load, count(*) as count, avg(power) as avg, stddev(power) as std,  stddev(power)/avg(power) as cv  from eurora2.load_cpu0_$cpu where power<1000 group by load"&
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.load1_avg_cpu$cpu "SELECT integer(load) as ld, count(*) as count, avg(power) as avg, stddev(power) as std,  stddev(power)/avg(power) as cv  from eurora2.load_cpu1_$cpu where power<1000 group by ld"&
sleep 2
done

##download avg and std
for cpu in ${cpus[*]};
do
echo $cpu
bq --project_id diecicolli-hrd extract eurora2.load0_avg_cpu$cpu gs://eurora_low_level/load0_avg_cpu${cpu}.csv
gsutil cp gs://eurora_low_level/load0_avg_cpu${cpu}.csv ./load0_avg_cpu${cpu}.csv
done

for cpu in ${cpus[*]};
do
echo $cpu
bq --project_id diecicolli-hrd extract eurora2.load1_avg_cpu$cpu gs://eurora_low_level/load1_avg_cpu${cpu}.csv
gsutil cp gs://eurora_low_level/load1_avg_cpu${cpu}.csv ./load1_avg_cpu${cpu}.csv
done


gpus=('34' '35' '36' '37' '38' '39' '41' '42' '43' '44' '45' '46' '47' '48' '49' '50' '51' '52' '53' '54' '55' '56' '57' '58' '59' '60' '61' '62' '63' '64')
for gpu in ${gpus[*]};
do
echo $gpu
 mysql -u [username] -h [host] -P [port] -D EuroraMeasurements -p[password] -B -e "select gpu_id, timestamp, pow, gpu_load from gpu_measurements_0$gpu "| sed 's/\t/,/g'>gpu${gpu}full.csv
gzip gpu${gpu}full.csv
done


for gpu in ${gpus[*]};
do
echo $gpu
bq --project_id diecicolli-hrd load --max_bad_records=64 --source_format=CSV eurora2.gpu${gpu}full gs://eurora_low_level/gpu${gpu}full.csv.gz gpu_id:integer,time:timestamp,pow:float,gpu_load:integer &
sleep 5
done


gpus=('33' '34' '35' '36' '37' '38' '39' '40' '41' '42' '43' '44' '45' '46' '47' '48' '49' '50' '51' '52' '53' '54' '55' '56' '57' '58' '59' '60' '61' '62' '63' '64')

for gpu in ${gpus[*]};
do
echo $gpu
bq --project_id diecicolli-hrd  query --replace --allow_large_results --destination_table=eurora2.load_avg_gpu$gpu "SELECT gpu_id, integer(gpu_load) as load, count(*) as count, avg(pow) as avg, stddev(pow) as std,  stddev(pow)/avg(pow) as cv  from eurora2.gpu${gpu}full group by load, gpu_id" &
sleep 5
done


for gpu in ${gpus[*]};
do
echo $gpu
bq --project_id diecicolli-hrd extract eurora2.load_avg_gpu$gpu gs://eurora_low_level/load_avg_gpu${gpu}.csv
gsutil cp gs://eurora_low_level/load_avg_gpu${gpu}.csv ./load_avg_gpu${gpu}.csv
done







SELECT node_id,left(user,8) as u, count(*) as c FROM [eurora2.job_nodes_complete_corrected]
where month(start)=10 and left(user,8) in ('asaetti0','bziosi00','epapaleo','mcerini','gprandin','dburatto','planucar') group by node_id, u order by u,c


SELECT  job_id FROM [eurora2.job_nodes_complete_corrected]
where (month(start)=10 or month(finish)=10) and left(user,8) in ('asaetti0','bziosi00','epapaleo','mcerini0','gprandin','dburatto','planucar') and node_id in (1 ,22, 26, 31, 33 ,34, 41) group by job_id



SELECT  job_id FROM [eurora2.job_nodes_complete_corrected]
where (month(start)=10 or month(finish)=10) and node_id in (1 ,22, 26, 31, 33 ,34, 41) group by job_id
