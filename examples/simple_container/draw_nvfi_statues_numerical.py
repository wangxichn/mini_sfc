import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

color_Bar = np.array([[122,27,109],[189,55,82],[251,180,26],[58,9,100],[237,104,37],[179,106,111],[161,208,199],[80,138,178]])
marker_Bar = ['o','s','^',',','*','+','v','<','>','d']
linestyle_Bar = ['-','--','-.',':']

# ------------------------------------------------------------------------------------------

# 获取当前目录下TraceNFVI_*.csv文件
csv_file_path = glob.glob("TraceNFVI_*.csv")
if csv_file_path:
    first_csv = csv_file_path[0]
    df = pd.read_csv(first_csv)
    print(f"已加载文件: {first_csv}")
    print(df.head())  # 打印前五行数据作为检查
else:
    raise FileNotFoundError("当前目录下没有找到CSV文件。")
    
title ='Draw simple dynamictopo nvfi statues with numerical data'
xlabel='Time(s)'
ylabel='Resource Usage Rate'

times = df['Time'].values

fig = plt.figure(figsize=(6, 4))
ax = plt.axes()
ax.set(xlabel=xlabel,ylabel=ylabel)

# NVFI的CPU和RAM曲线
for i in range(3): # 有3个NVFI
    cpu_key = f'NVFI_{i}_cpu'
    ram_key = f'NVFI_{i}_ram'
    
    total_cpu = df[cpu_key].iloc[0]
    total_ram = df[ram_key].iloc[0]
    
    cpu_usage_rate = (total_cpu - df[cpu_key]) / total_cpu
    ram_usage_rate = (total_ram - df[ram_key]) / total_ram
    
    ax.step(times, cpu_usage_rate, label=f'NVFI_{i} CPU', 
            linestyle='-', color=color_Bar[i]/255, 
            marker=marker_Bar[i], markerfacecolor="none", markeredgecolor=color_Bar[i]/255,
            where='post')
    ax.step(times, ram_usage_rate, label=f'NVFI_{i} RAM', 
            linestyle='--', color=color_Bar[i]/255, 
            marker=marker_Bar[i], markerfacecolor="none", markeredgecolor=color_Bar[i]/255,
            where='post')

ax.legend(loc='upper right')

if os.path.exists('fig') == False:
    os.mkdir('fig')

fig.savefig('fig/'+title.replace(' ','_')+'.svg',format='svg',dpi=150)
fig.savefig('fig/'+title.replace(' ','_')+'.pdf', bbox_inches='tight', pad_inches=0.5)
