import os
import argparse

def __remove_directory(path):
    if os.name == 'posix':  # Linux, macOS
        print(f"Removing directory (Linux/macOS): {path}")
        os.system(f"rm -rf {path}")
    elif os.name == 'nt':  # Windows
        print(f"Removing directory (Windows): {path}")
        os.system(f"rmdir /S /Q {path}")
    else:
        raise OSError("Unsupported operating system")

def clear_cache(filepath):
    try:
        files = os.listdir(filepath)
        for fd in files:
            cur_path = os.path.join(filepath, fd)
            if os.path.isdir(cur_path):
                if fd == "__pycache__":
                    __remove_directory(cur_path)
                else:
                    clear_cache(cur_path)
    except Exception as e:
        print(f"Error occurred: {e}")

def clear_database():
    instance_dir = 'instance'
    if os.path.exists(instance_dir):
        for filename in os.listdir(instance_dir):
            if filename.endswith('.db'):
                file_path = os.path.join(instance_dir, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted {file_path}")
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")
            elif filename.endswith('.log'):
                file_path = os.path.join(instance_dir, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted {file_path}")
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.description='服务器清理程序 ...'
    parser.add_argument("-ca", action='store_true', help='清理python缓存文件')
    parser.add_argument("-db", action='store_true', help='清理instance下的数据库文件')

    args = parser.parse_args()
    if args.ca:
        clear_cache('.')
    elif args.db:
        clear_database()
    else:
        print("No valid option provided. Use -h for more help")

if __name__ == "__main__":
    main()