import os
import subprocess
from multiprocessing import Process, Event
import signal
import atexit
import sys
import time
import argparse



def run_server(stop_event, vnf_name, vnf_type, vnf_ip, vnf_port, vnf_cpu, vnf_ram, vnf_rom):
    def signal_handler(signum, frame):
        stop_event.set()

    # 注册信号处理函数
    signal.signal(signal.SIGTERM, signal_handler)

    # 设置环境变量
    env = os.environ.copy()
    env['VNF_SERVER_NAME'] = vnf_name
    env['VNF_SERVER_TYPE'] = vnf_type
    env['VNF_SERVER_CPU'] = vnf_cpu
    env['VNF_SERVER_RAM'] = vnf_ram
    env['VNF_SERVER_ROM'] = vnf_rom

    # 构建uvicorn命令
    command = ['uvicorn','run:app',
        '--host', '0.0.0.0',
        '--port', vnf_port,
        '--log-level', 'error',
    ]

    with subprocess.Popen(command, env=env) as proc:
        try:
            while not stop_event.is_set():
                time.sleep(0.5)
        except Exception as e:
            print(f"Exception in server process: {e}")
        finally:
            proc.terminate()
            proc.wait()  # 等待子进程结束


def run_clean():
    command = ['python','clean.py','-db']
    with subprocess.Popen(command) as proc:
        proc.wait()


def create_vnf_process(stop_event, **kwargs):
    vnf_name = kwargs.get('vnf_name','vnf_default')
    vnf_type = kwargs.get('vnf_type','vnf_default')
    vnf_ip = kwargs.get('vnf_ip','127.0.0.1')
    vnf_port = kwargs.get('vnf_port','5001')
    vnf_cpu = kwargs.get('vnf_cpu','1')
    vnf_ram = kwargs.get('vnf_ram','0.1')
    vnf_rom = kwargs.get('vnf_rom','1')

    vnfProcess = Process(target=run_server, args=(stop_event, vnf_name, vnf_type, vnf_ip, vnf_port,
                                                  vnf_cpu, vnf_ram, vnf_rom))
    vnfProcess.daemon = True
    vnfProcess.start()

    return vnfProcess


def create_clean_process(vnf_processes):
    for p in vnf_processes:
        p.terminate()
        p.join()
    run_clean()


def parse_args():
    parser = argparse.ArgumentParser(description="VNFM (VNF Manager) configuration")
    parser.add_argument('--vnf_name', required=True, help='The name of the VNF (e.g. vnf_1)')
    parser.add_argument('--vnf_type', required=True, help='The type of the VNF (e.g. vnf_matinv)')
    parser.add_argument('--vnf_ip', required=True, help='The IP address of the VNF (e.g. 192.168.31.80)')
    parser.add_argument('--vnf_port', required=True, help='The port number of the VNF (e.g. 5001)')
    parser.add_argument('--vnf_cpu', required=True, help='The CPU requirement of the VNF (e.g. 0.5)')
    parser.add_argument('--vnf_ram', required=True, help='The RAM requirement of the VNF (e.g. 0.2)')
    parser.add_argument('--vnf_rom', required=True, help='The ROM requirement of the VNF (e.g. 10)')

    args = parser.parse_args()

    return vars(args)


if __name__ == '__main__':
    
    vnf_info = parse_args()

    stop_event = Event()
    vnf_Process = create_vnf_process(stop_event, **vnf_info)
    vnf_processes = [vnf_Process]
    atexit.register(create_clean_process, vnf_processes=vnf_processes)

    try:
        while True:
            timestamp = time.time()
            local_time = time.localtime(timestamp)
            formatted_time = time.strftime("%H:%M:%S", local_time)
            print(f"{formatted_time} {vnf_info['vnf_name']} {vnf_info['vnf_type']} {vnf_info['vnf_ip']}:{vnf_info['vnf_port']}")
            time.sleep(5)
    except KeyboardInterrupt:
        print('Main process received interrupt, initiating clean up...')
        stop_event.set()
        create_clean_process(vnf_processes)
        print('Cleanup completed, exiting...')
        sys.exit(0)

