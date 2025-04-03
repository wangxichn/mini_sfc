import importlib.metadata
from pathlib import Path
from setuptools import setup, find_packages

# 动态生成 requirements.txt
def generate_requirements():
    packages = [
        "matplotlib",
        "networkx",
        "numpy",
        "pandas",
        "PyQt5",
        "Pyqt5-tools",
        "setuptools"
    ]

    # 写入 requirements.txt
    with open("requirements.txt", "w") as f:
        for package in packages:
            try:
                version = importlib.metadata.version(package)
                f.write(f"{package}>={version}\n")
            except importlib.metadata.PackageNotFoundError:
                f.write(f"{package}\n")

# 调用函数生成 requirements.txt
generate_requirements()

# 读取 requirements.txt 中的内容
with open('requirements.txt', 'r') as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# 设置 setuptools 配置
setup(
    name='Netterminal',
    version='0.0',
    packages=find_packages(),
    install_requires=install_requires,
    author='Wang Xi',
    author_email='wangxi_chn@foxmail.com',
    description='Network demonstration system terminal development framework.',
    url='https://gitee.com/WangXi_Chn/netterminal.git',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)

# 使用方式：pip install -e .