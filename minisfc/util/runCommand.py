import os
import stat
import subprocess

class RunCommand:
    def __init__(self):
        # 获取util目录的绝对路径
        self.bash_file_path_prefix = os.path.dirname(os.path.abspath(__file__))

    def make_executable(self, path):
        """为指定路径的文件添加执行权限"""
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)

    def run_shell(self, bash_file_path):
        try:
            # 确保脚本具有可执行权限
            self.make_executable(bash_file_path)
            # 直接运行脚本并等待其完成
            result = subprocess.run([bash_file_path], check=True, text=True, stdout=subprocess.PIPE)
            print("INFO: ", result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: {e.stderr}")
        except Exception as e:
            print(f"ERROR: {e}")

    def run_shell_in_terminal(self, bash_file_path):
        try:
            # 确保脚本具有可执行权限
            self.make_executable(bash_file_path)
            # 使用gnome-terminal直接运行脚本
            subprocess.run(['gnome-terminal', '--', '/bin/bash', '-c', f'{bash_file_path}; exec bash'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"INFO: {e.stderr}")
        except Exception as e:
            print(f"ERROR: {e}")

    def clear_container(self):
        bash_file_path = os.path.join(self.bash_file_path_prefix, 'auto_clean.sh')
        self.run_shell(bash_file_path)

    def get_container_logs(self):
        bash_file_path = os.path.join(self.bash_file_path_prefix, 'auto_getlogs.sh')
        self.run_shell_in_terminal(bash_file_path)

    def get_container_status(self):
        bash_file_path = os.path.join(self.bash_file_path_prefix, 'auto_getstatus.sh')
        self.run_shell_in_terminal(bash_file_path)