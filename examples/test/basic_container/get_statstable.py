import csv
from collections import defaultdict

# 定义输入和输出文件名
log_file = 'logsave/vnf_stats.log'
csv_file = 'trace_stats.csv'

# 声明哪些设备被记录
sfc = ["mn.vnf_1", "mn.vnf_2", "mn.vnf_3", "mn.vnf_4"]

# 初始化一个字典来保存每秒的时间戳以及对应的vnf信息
data_dict = defaultdict(lambda: {'timestamp': ''})

# 根据sfc列表动态生成表头
fieldnames = ['timestamp']
for vnf in sfc:
    fieldnames.extend([vnf, f'{vnf}_cpu_use', f'{vnf}_ram_use'])
    data_dict.default_factory().update({
        vnf: '',
        f'{vnf}_cpu_use': 0,
        f'{vnf}_ram_use': 0
    })

# 读取.log文件并填充字典
with open(log_file, 'r') as file:
    for line in file:
        parts = line.strip().split()
        timestamp = ' '.join(parts[0:2])
        vnf = parts[2]
        cpu_use = float(parts[3].strip('%'))
        ram_parts = parts[4].split('/')
        ram_use = float(ram_parts[0].strip('MiB'))

        # 将信息添加到字典中
        if vnf in sfc:
            data_dict[timestamp]['timestamp'] = timestamp
            data_dict[timestamp][vnf] = vnf
            data_dict[timestamp][f'{vnf}_cpu_use'] = cpu_use
            data_dict[timestamp][f'{vnf}_ram_use'] = ram_use

# 将字典中的数据写入CSV文件
with open(csv_file, 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()  # 写入表头
    for key in sorted(data_dict.keys()):  # 按时间戳排序
        if any(data_dict[key][f'{vnf}_cpu_use'] or data_dict[key][f'{vnf}_ram_use'] for vnf in sfc):
            writer.writerow(data_dict[key])

print(f"Data has been successfully written to {csv_file}")