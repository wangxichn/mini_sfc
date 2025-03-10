import os
import subprocess
from multiprocessing import Process, Event
import signal
import atexit
import sys
import time

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
        '--host', vnf_ip,
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

if __name__ == '__main__':
    
    vnf_1_info = {'vnf_name':'vnf_1','vnf_type':'vnf_matinv','vnf_ip':'169.254.124.164','vnf_port':'5001',
                  'vnf_cpu':'0.5', 'vnf_ram':'0.2', 'vnf_rom':'10'}
    vnf_2_info = {'vnf_name':'vnf_2','vnf_type':'vnf_matprint','vnf_ip':'169.254.124.164','vnf_port':'5002',
                  'vnf_cpu':'0.2', 'vnf_ram':'0.1', 'vnf_rom':'20'}
    vnf_3_info = {'vnf_name':'vnf_3','vnf_type':'vnf_gnb','vnf_ip':'169.254.124.164','vnf_port':'5003',
                  'vnf_cpu':'0.3', 'vnf_ram':'0.2', 'vnf_rom':'30'}
    vnf_4_info = {'vnf_name':'vnf_4','vnf_type':'vnf_gnb','vnf_ip':'169.254.124.164','vnf_port':'5004',
                  'vnf_cpu':'0.3', 'vnf_ram':'0.2', 'vnf_rom':'30'}
    
    stop_event1 = Event()
    stop_event2 = Event()
    stop_event3 = Event()
    stop_event4 = Event()

    vnf_1_Process = create_vnf_process(stop_event1, **vnf_1_info)
    vnf_2_Process = create_vnf_process(stop_event2, **vnf_2_info)
    vnf_3_Process = create_vnf_process(stop_event3, **vnf_3_info)
    vnf_4_Process = create_vnf_process(stop_event4, **vnf_4_info)

    vnf_processes = [vnf_1_Process, vnf_2_Process, 
                     vnf_3_Process, vnf_4_Process]

    # 注册退出处理器
    atexit.register(create_clean_process, vnf_processes=vnf_processes)

    try:
        while True:
            print('Main process is running...')
            time.sleep(2)
    except KeyboardInterrupt:
        print('Main process received interrupt, initiating clean up...')
        stop_event1.set()
        stop_event2.set()
        stop_event3.set()
        stop_event4.set()
        create_clean_process(vnf_processes)
        print('Cleanup completed, exiting...')
        sys.exit(0)

