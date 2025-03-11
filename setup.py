from setuptools import setup, find_packages

setup(
    name='minisfc',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # requirements.txt
    ],
    author='Wang Xi',
    author_email='wangxi_chn@foxmail.com',
    description='A simulation framework for SFC orchestration algorithm with reference to MANO.',
    url='https://gitee.com/WangXi_Chn/mini_sfc.git',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD 3-Clause License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)

# pip install -e .