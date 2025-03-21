import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

color_Bar = np.array([[122,27,109],[189,55,82],[251,180,26],[58,9,100],[237,104,37],[179,106,111],[161,208,199],[80,138,178]])
marker_Bar = ['o','s','^',',','*','+','v','<','>','d']
linestyle_Bar = ['-','--','-.',':']

# ------------------------------------------------------------------------------------------

df = pd.read_csv("TraceNFVI_RadomSolver_20250320173054765.csv")
    
title ='Draw simple dynamictopo nvfi statues with numerical data'
xlabel='Time(s)'
ylabel='Resource Usage Rate'

times = df['Time'].values

fig = plt.figure(figsize=(10, 4))
ax = plt.axes()
ax.set(xlabel=xlabel,ylabel=ylabel)

# NVFI的CPU和RAM曲线
for i in range(3): # 假设有3个NVFI
    cpu_key = f'NVFI_{i}_cpu'
    ram_key = f'NVFI_{i}_ram'
    
    # 假设初始值代表总量，并计算占用率
    total_cpu = df[cpu_key].iloc[0]
    total_ram = df[ram_key].iloc[0]
    
    cpu_usage_rate = (total_cpu - df[cpu_key]) / total_cpu
    ram_usage_rate = (total_ram - df[ram_key]) / total_ram
    
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
