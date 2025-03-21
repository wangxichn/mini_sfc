import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import re
import ast
import numpy as np

color_Bar = np.array([[122,27,109],[189,55,82],[251,180,26],[58,9,100],[237,104,37],[179,106,111],[161,208,199],[80,138,178]])
marker_Bar = ['o','s','^',',','*','+','v','<','>','d']
linestyle_Bar = ['-','--','-.',':']

# ------------------------------------------------------------------------------------------

# 读取CSV文件
csv_file_path = 'TraceNFVI_RadomSolver_20250320173054765.csv'
df = pd.read_csv(csv_file_path)

# 读取日志文件
log_file_path = 'logsave/vnf_stats.log'
with open(log_file_path, 'r') as file:
    logs = file.readlines()

# 解析日志文件
first_timestamp = None
vnf_pattern = re.compile(r'^mn.f\d+v\d+$')
vnf_resources = {}
for line in logs:
    parts = line.strip().split('\t')

    timestamp = datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')
    if not first_timestamp:
        first_timestamp = timestamp

    if not vnf_pattern.match(parts[1]):
        continue
    time_passed = (timestamp - first_timestamp).total_seconds()

    vnf_name = parts[1].split('.')[-1]
    cpu_usage = float(parts[2].replace('%', '').strip())/100.0
    mem_usage = float(parts[3].split('/')[0].strip().rstrip('MiB'))

    vnf_resources.setdefault(time_passed, {}).update({vnf_name:[cpu_usage, mem_usage]})

def find_nearest_time(times, target, max_range=1.0):
    nearest_time = min(times, key=lambda x: abs(x - target))
    difference = abs(nearest_time - target)
    if difference <= max_range:
        return nearest_time
    else:
        return None

# ------------------------------------------------------------------------------------------

title ='Draw simple dynamictopo nvfi statues with numerical data'
xlabel='Time(s)'
ylabel='Resource Usage Rate'

# 提取时间和资源占用数据
times = df['Time'].values
times_chosens = vnf_resources.keys()

fig = plt.figure(figsize=(10, 4))
ax = plt.axes()
ax.set(xlabel=xlabel,ylabel=ylabel)

# NVFI的CPU和RAM曲线
for i in range(3): # 假设有3个NVFI
    cpu_key = f'NVFI_{i}_cpu'
    ram_key = f'NVFI_{i}_ram'
    total_cpu = df[cpu_key].iloc[0]
    total_ram = df[ram_key].iloc[0]
    
    cpu_usage_list = []
    ram_usage_list = []
    for time in times:
        nearest_time = find_nearest_time(times_chosens, time)
        if nearest_time:
            cpu_usage = 0
            ram_usage = 0
            vnfs_key = f'NVFI_{i}_vnfs'
            vnfs_list = [ast.literal_eval(item) for item in df.loc[df['Time'] == time, vnfs_key].tolist()][0]
            for vnf in vnfs_list:
                cpu_usage += vnf_resources[nearest_time][vnf][0]
                ram_usage += vnf_resources[nearest_time][vnf][1]
            cpu_usage_list.append(cpu_usage)
            ram_usage_list.append(ram_usage)
        else:
            cpu_usage_list.append(0)
            ram_usage_list.append(0)

    cpu_usage_rate = [item/total_cpu for item in cpu_usage_list]
    ram_usage_rate = [item/total_ram for item in ram_usage_list]
    
    # 绘制阶梯图，其中CPU使用实线，RAM使用虚线；并且使用相同的颜色但是不同的点型
    ax.step(times, cpu_usage_rate, label=f'NVFI_{i} CPU', 
            linestyle='-', color=color_Bar[i]/255, 
            marker=marker_Bar[i], markerfacecolor="none", markeredgecolor=color_Bar[i]/255,
            where='post')
    ax.step(times, ram_usage_rate, label=f'NVFI_{i} RAM', 
            linestyle='--', color=color_Bar[i]/255, 
            marker=marker_Bar[i], markerfacecolor="none", markeredgecolor=color_Bar[i]/255,
            where='post')

ax.legend(loc='upper right')

fig.savefig('fig/'+title.replace(' ','_')+'.svg',format='svg',dpi=150)
fig.savefig('fig/'+title.replace(' ','_')+'.pdf', bbox_inches='tight', pad_inches=0.5)
