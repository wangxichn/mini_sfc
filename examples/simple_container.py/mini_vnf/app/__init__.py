from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import config

def create_app():
    # 创建FastAPI应用实例
    app = FastAPI()

    # 挂载静态文件目录
    # 将/static路径下的请求映射到app/static目录，名称为"static"
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # 导入模型
    # 初始化 vnf 模型
    from .models.vnf import vnf
    vnf.name = config.VNF_SERVER_NAME
    vnf.type = config.VNF_SERVER_TYPE
    vnf.cpu = float(config.VNF_SERVER_CPU)
    vnf.ram = float(config.VNF_SERVER_RAM)
    vnf.rom = float(config.VNF_SERVER_ROM)

    # 导入路由
    # 从routes.main模块导入路由器对象main_router
    from .routes.main import router as main_router
    # 将main_router包含到应用中，设置前缀和标签
    app.include_router(main_router, prefix="", tags=["main"])

    # 返回配置好的FastAPI应用实例
    return app