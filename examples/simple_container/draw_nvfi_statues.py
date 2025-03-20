import pandas as pd
import matplotlib.pyplot as plt
import glob

# 获取当前目录下所有.csv文件
csv_files = glob.glob('*.csv')

if csv_files:  # 如果找到了.csv文件
    # 默认选择第一个找到的CSV文件
    first_csv = csv_files[0]
    
    # 读取该CSV文件
    df = pd.read_csv(first_csv)
    
    print(f"已加载文件: {first_csv}")
    print(df.head())  # 打印前五行数据作为检查
else:
    raise FileNotFoundError("当前目录下没有找到CSV文件。")

# 提取时间和资源占用数据
times = df['Time'].values

# 定义颜色列表和点型列表以便于同一NVFI的CPU和RAM使用相同颜色且不同NVFI使用不同的点型
colors = [(122/255, 27/255, 109/255), (189/255, 55/255, 82/255), (251/255, 180/255, 26/255)]
markers = ['o', 's', '^'] # 点型列表：圆圈、正方形、上三角

# NVFI的CPU和RAM曲线
for i, color, marker in zip(range(3), colors, markers): # 假设有3个NVFI
    cpu_key = f'NVFI_{i}_cpu'
    ram_key = f'NVFI_{i}_ram'
    
    # 假设初始值代表总量，并计算占用率
    total_cpu = df[cpu_key].iloc[0]
    total_ram = df[ram_key].iloc[0]
    
    cpu_usage_rate = (total_cpu - df[cpu_key]) / total_cpu
    ram_usage_rate = (total_ram - df[ram_key]) / total_ram
    
    # 绘制阶梯图，其中CPU使用实线，RAM使用虚线；并且使用相同的颜色但是不同的点型
    plt.step(times, cpu_usage_rate, label=f'NVFI_{i} CPU', linestyle='-', 
             color=color, marker=marker, markerfacecolor="none", markeredgecolor=color,where='post')
    plt.step(times, ram_usage_rate, label=f'NVFI_{i} RAM', linestyle='--', 
             color=color, marker=marker, markerfacecolor="none", markeredgecolor=color,where='post')

plt.xlabel('Time(s)')
plt.ylabel('Resource Usage Rate')

plt.legend(loc='upper right')

# 保存图表为SVG格式
plt.savefig('draw_simple_dynamictopo_nvfi_statues.svg', format='svg')

# plt.show()
