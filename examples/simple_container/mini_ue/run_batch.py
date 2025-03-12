import os
import subprocess
from multiprocessing import Process, Event
import signal
import atexit
import sys
import time

def run_server(stop_event, ue_name, ue_type, ue_ip, ue_port):
    def signal_handler(signum, frame):
        stop_event.set()

    # 注册信号处理函数
    signal.signal(signal.SIGTERM, signal_handler)

    # 设置环境变量
    env = os.environ.copy()
    env['UE_SERVER_NAME'] = ue_name
    env['ue_SERVER_TYPE'] = ue_type

    # 构建uvicorn命令
    command = ['uvicorn','run:app',
        '--host', ue_ip,
        '--port', ue_port,
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

def create_ue_process(stop_event, **kwargs):
    ue_name = kwargs.get('ue_name','ue_default')
    ue_type = kwargs.get('ue_type','ue_default')
    ue_ip = kwargs.get('ue_ip','127.0.0.1')
    ue_port = kwargs.get('ue_port','5001')

    ueProcess = Process(target=run_server, args=(stop_event, ue_name, ue_type, ue_ip, ue_port))
    ueProcess.daemon = True
    ueProcess.start()

    return ueProcess

def create_clean_process(ue_processes):
    for p in ue_processes:
        p.terminate()
        p.join()
    run_clean()

if __name__ == '__main__':
    
    ue_1_info = {'ue_name':'ue_1','ue_type':'ue_post','ue_ip':'169.254.124.164','ue_port':'8001'}
    ue_2_info = {'ue_name':'ue_2','ue_type':'ue_print','ue_ip':'169.254.124.164','ue_port':'8002'}
    
    stop_event1 = Event()
    stop_event2 = Event()

    ue_1_Process = create_ue_process(stop_event1, **ue_1_info)
    ue_2_Process = create_ue_process(stop_event2, **ue_2_info)

    ue_processes = [ue_1_Process, ue_2_Process]

    # 注册退出处理器
    atexit.register(create_clean_process, ue_processes=ue_processes)

    try:
        while True:
            print('Main process is running...')
            time.sleep(2)
    except KeyboardInterrupt:
        print('Main process received interrupt, initiating clean up...')
        stop_event1.set()
        stop_event2.set()
        create_clean_process(ue_processes)
        print('Cleanup completed, exiting...')
        sys.exit(0)

