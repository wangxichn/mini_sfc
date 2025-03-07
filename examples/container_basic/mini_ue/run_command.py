import os
import subprocess
from multiprocessing import Process, Event
import signal
import atexit
import sys
import time
import argparse


def run_server(stop_event, ue_name, ue_type, ue_ip, ue_port):
    def signal_handler(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, signal_handler)

    env = os.environ.copy()
    env['UE_SERVER_NAME'] = ue_name
    env['ue_SERVER_TYPE'] = ue_type

    command = ['uvicorn','run:app',
        '--host', '0.0.0.0',
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


def parse_args():
    parser = argparse.ArgumentParser(description="UE (User Equipment) configuration")

    parser.add_argument('--ue_name', required=True, help='The name of the UE (e.g. ue_1)')
    parser.add_argument('--ue_type', required=True, help='The type of the UE (e.g. ue_post)')
    parser.add_argument('--ue_ip', required=True, help='The IP address of the UE (e.g. 192.168.31.80)')
    parser.add_argument('--ue_port', required=True, help='The port number of the UE (e.g. 8000)')
    parser.add_argument('--ue_aim', default=None, help='The aim UE or target of the UE (e.g. ue_info:dict)')

    args = parser.parse_args()
    
    return vars(args)


if __name__ == '__main__':
    
    ue_info = parse_args()
    
    stop_event = Event()

    ue_Process = create_ue_process(stop_event, **ue_info)
    ue_processes = [ue_Process]
    atexit.register(create_clean_process, ue_processes=ue_processes)

    try:
        while True:
            timestamp = time.time()
            local_time = time.localtime(timestamp)
            formatted_time = time.strftime("%H:%M:%S", local_time)
            print(f"{formatted_time} {ue_info['ue_name']} {ue_info['ue_type']} {ue_info['ue_ip']}:{ue_info['ue_port']}")
            time.sleep(5)
    except KeyboardInterrupt:
        print('Main process received interrupt, initiating clean up...')
        stop_event.set()
        create_clean_process(ue_processes)
        print('Cleanup completed, exiting...')
        sys.exit(0)

