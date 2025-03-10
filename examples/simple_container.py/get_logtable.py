import re
from datetime import datetime
from collections import defaultdict
import csv

logspath = "logsave"

# 定义 SFC
sfc = ["ue_1", "vnf_3", "vnf_1", "vnf_4", "ue_2"]

# 定义日志条目的正则表达式模式
log_pattern = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - '
    r'(?P<object>\w+)_logger - '
    r'(?P<action>\w+) - '
    r'(?P<packet_id>\d+)'
)

# 用于存储每个数据包的时间信息
packet_times = defaultdict(dict)

# 解析并存储日志文件的信息
def parse_log(filename, packet_times):
    try:
        with open(filename, 'r') as file:
            for line in file:
                match = log_pattern.match(line.strip())
                if match:
                    data = match.groupdict()
                    timestamp_str = data['timestamp']
                    obj = data['object']
                    action = data['action']
                    packet_id = int(data['packet_id'])

                    # 将时间字符串转换为datetime对象
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')

                    # 存储对应的时间戳
                    key = f"{obj}_{action}"
                    packet_times[packet_id][key] = timestamp
    except FileNotFoundError:
        print(f"Warning: File not found: {filename}")

# 处理服务功能链 (SFC)
def process_sfc(sfc, packet_times):
    for obj in sfc:
        filename = f"{logspath}/{obj}.log"
        parse_log(filename, packet_times)

# 输出结果
def print_results(packet_times, sfc):
    headers = ["Packet ID"]
    for i, obj in enumerate(sfc):
        if i == 0:
            headers.append(f"{obj}_send")
        elif i == len(sfc) - 1:
            headers.append(f"{obj}_recv")
        else:
            headers.extend([f"{obj}_recv", f"{obj}_send"])

    print(" | ".join(headers))
    print("-" * 80)

    for packet_id in sorted(packet_times.keys()):
        row = [str(packet_id)]
        for i, obj in enumerate(sfc):
            if i == 0:
                send_time = packet_times[packet_id].get(f"{obj}_send", None)
                row.append(format_time(send_time))
            elif i == len(sfc) - 1:
                recv_time = packet_times[packet_id].get(f"{obj}_recv", None)
                row.append(format_time(recv_time))
            else:
                recv_time = packet_times[packet_id].get(f"{obj}_recv", None)
                send_time = packet_times[packet_id].get(f"{obj}_send", None)
                row.extend([format_time(recv_time), format_time(send_time)])

        print(" | ".join(row))

# 格式化输出时间
def format_time(t):
    return t.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3] if t else 'N/A'

# 处理 SFC 并解析日志文件
process_sfc(sfc, packet_times)

# 输出结果
print_results(packet_times, sfc)

# ------------------------ 以下为可选功能 ------------------------

# 计算延迟
def calculate_delays(packet_times, sfc):
    for packet_id, times in packet_times.items():
        for i in range(len(sfc) - 1):
            current_obj = sfc[i]
            next_obj = sfc[i + 1]

            send_time = times.get(f"{current_obj}_send")
            recv_time = times.get(f"{next_obj}_recv")

            if send_time and recv_time:
                transmission_delay = (recv_time - send_time).total_seconds() * 1000  # 毫秒
                times[f"{current_obj}_{next_obj}_delay"] = transmission_delay

            if i > 0:
                recv_time = times.get(f"{current_obj}_recv")
                send_time = times.get(f"{current_obj}_send")

                if recv_time and send_time:
                    processing_delay = (send_time - recv_time).total_seconds() * 1000  # 毫秒
                    times[f"{current_obj}_delay"] = processing_delay

# 格式化输出延迟
def format_delay(d):
    return f"{d:.2f}" if d is not None else 'N/A'

# 动态生成表头
def generate_headers(sfc):
    headers = ["pkt_id"]

    for i, obj in enumerate(sfc):
        if i == 0:
            headers.append(f"{obj}_send")
        else:
            prev_obj = sfc[i - 1]
            # 添加上一个节点到当前节点的延迟和当前节点的接收字段
            headers.extend([f"{prev_obj}_{obj}_delay", f"{obj}_recv"])
            if i < len(sfc) - 1:
                # 如果不是最后一个节点，则添加当前节点的处理延迟和发送字段
                headers.extend([f"{obj}_delay", f"{obj}_send"])

    headers.append("total_delay")
    return headers

# 生成 CSV 文件
def generate_csv(packet_times, sfc, output_file):
    
    headers = generate_headers(sfc)

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for packet_id in sorted(packet_times.keys()):
            row = [packet_id]
            times = packet_times[packet_id]

            # 动态查找并填充每一列
            for header in headers[1:-1]:
                if header.endswith('_delay'):
                    delay_key = header
                    row.append(format_delay(times.get(delay_key)))
                else:
                    time_key = header
                    row.append(format_time(times.get(time_key)))

            # 计算 total_delay
            ue_1_send = times.get("ue_1_send")
            ue_2_recv = times.get("ue_2_recv")
            if ue_1_send and ue_2_recv:
                total_delay = (ue_2_recv - ue_1_send).total_seconds() * 1000  # 毫秒
                row.append(format_delay(total_delay))
            else:
                row.append('N/A')

            writer.writerow(row)

# 计算延迟
calculate_delays(packet_times, sfc)

# 生成 CSV 文件
output_file = "trace_delay.csv"
generate_csv(packet_times, sfc, output_file)

print(f"Analysis results have been saved to {output_file}")