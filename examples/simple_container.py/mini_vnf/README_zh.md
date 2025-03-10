# Mini_VNF：一个参考MANO架构的VNF微服务模型

## 引用本框架

如果您发现 Mini-VNF 对您的研究有帮助，请随时引用我们的相关论文

**[Drones, 2024] PSO**

```bibtex
@Article{drones8040117,
AUTHOR = {Wang, Xi and Shi, Shuo and Wu, Chenyu},
TITLE = {Research on Service Function Chain Embedding and Migration Algorithm for UAV IoT},
JOURNAL = {Drones},
VOLUME = {8},
YEAR = {2024},
NUMBER = {4},
ARTICLE-NUMBER = {117},
URL = {https://www.mdpi.com/2504-446X/8/4/117},
ISSN = {2504-446X},
DOI = {10.3390/drones8040117}
}
```

## 环境依赖
Python3
FastAPI
uvicorn

## 部署步骤

1. 如果单独启动一个服务器代表一个抽象的 VNF 微服务模型
    终端执行 `uvicorn run:app` 在默认本地地址开启微服务
    - 可通过浏览器访问服务器地址，显示部署的微服务的简要信息
2. 如果想批量启动多个服务器代表一组抽象的 VNF 微服务模型
    - 终端执行 `python run_batch.py` 可启动默认两个微服务
      - vnf1 矩阵求逆计算微服务
      - vnf2 打印矩阵微服务
    - 通过终端执行 `python run_request.py` 实现服务功能链的请求
      - 指定了服务功能链的入口地址和出口地址
      - 提交需求矩阵，自动完成矩阵求逆且在出口处打印的服务
3. 可通过浏览器访问url:`https:微服务地址/docs`使用FastAPI提供的接口手册

## 目录结构描述

```shell
📦mini_vnf
 ┣ 📂app
 ┃ ┣ 📂models
 ┃ ┃ ┣ 📜vnf.py
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂routes
 ┃ ┃ ┣ 📜main.py
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂static
 ┃ ┃ ┣ 📂css
 ┃ ┃ ┃ ┗ 📜style.css
 ┃ ┃ ┗ 📂js
 ┃ ┣ 📂templates
 ┃ ┃ ┗ 📜index.html
 ┃ ┗ 📜__init__.py
 ┣ 📂instance
 ┣ 📜clean.py
 ┣ 📜config.py
 ┣ 📜README_zh.md
 ┣ 📜requirements.txt
 ┣ 📜run.py
 ┣ 📜run_batch.py
 ┗ 📜run_request.py
```
