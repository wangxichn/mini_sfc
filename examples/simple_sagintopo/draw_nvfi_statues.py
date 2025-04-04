import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

# 获取当前目录下TraceNFVI_*.csv文件
csv_files = glob.glob("TraceNFVI_*.csv")
if csv_files:
    first_csv = csv_files[0]
    df = pd.read_csv(first_csv)
    print(f"已加载文件: {first_csv}")
    print(df.head())  # 打印前五行数据作为检查
else:
    raise FileNotFoundError("当前目录下没有找到CSV文件。")


times = df['Time'].values

colors = [(122/255, 27/255, 109/255), (189/255, 55/255, 82/255), (251/255, 180/255, 26/255)]
markers = ['o', 's', '^']

# NVFI的CPU和RAM曲线
for i, color, marker in zip(range(48), colors, markers): # 48个NVFI
    cpu_key = f'NVFI_{i}_cpu'
    ram_key = f'NVFI_{i}_ram'
    
    total_cpu = df[cpu_key].iloc[0]
    total_ram = df[ram_key].iloc[0]
    
    cpu_usage_rate = (total_cpu - df[cpu_key]) / total_cpu
    ram_usage_rate = (total_ram - df[ram_key]) / total_ram
    
    plt.step(times, cpu_usage_rate, label=f'NVFI_{i} CPU', linestyle='-', 
             color=color, marker=marker, markerfacecolor="none", markeredgecolor=color,where='post')
    plt.step(times, ram_usage_rate, label=f'NVFI_{i} RAM', linestyle='--', 
             color=color, marker=marker, markerfacecolor="none", markeredgecolor=color,where='post')

if os.path.exists('fig') == False:
    os.mkdir('fig')

plt.xlabel('Time(s)')
plt.ylabel('Resource Usage Rate')
plt.legend(loc='upper left')
plt.savefig('fig/draw_simple_sagintopo_nvfi_statues.svg', format='svg')

# plt.show()