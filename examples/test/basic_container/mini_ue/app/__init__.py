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
    from .models.ue import ue
    ue.name = config.UE_SERVER_NAME
    ue.type = config.UE_SERVER_TYPE

    # 导入路由
    # 从routes.main模块导入路由器对象main_router
    from .routes.main import router as main_router
    # 将main_router包含到应用中，设置前缀和标签
    app.include_router(main_router, prefix="", tags=["main"])

    # 返回配置好的FastAPI应用实例
    return app
