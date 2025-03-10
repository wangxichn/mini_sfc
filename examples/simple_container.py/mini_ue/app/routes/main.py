from fastapi import APIRouter, Request, status, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator 
from typing import Optional, Any
from ..models.ue import ue
from ..models.logger import logger
import httpx
import time


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# public route-------------------------------------------------------------------------------------

@router.get('/', response_class=HTMLResponse, name="main.index")
def index(request: Request):
    """
    获取该 ue 信息
    """
    return templates.TemplateResponse('index.html', {'request': request, 'ue': ue})

# public tool---------------------------------------------------------------------------------------

async def post_to(data: dict, aim_url: str):
    try:
        logger.info(f"send - {data['request_id']}")
        async with httpx.AsyncClient() as client:
            response = await client.post(aim_url, json=data)
            response.raise_for_status()
        print(f"{ue.name} {ue.type} post to: {aim_url} | pkg {data['request_id']}")
    except httpx.RequestError as exc:
        print(f"{ue.name} {ue.type} request failed: {exc}")
    except httpx.HTTPStatusError as exc:
        print(f"{ue.name} {ue.type} http error: {exc.response.status_code}, {exc.response.text}")

# ue post function---------------------------------------------------------------------------------------

class uePostRequest(BaseModel):
    ue_post_url: str
    ue_post_data: Any
    request_id: int

@router.post('/ue_post', response_class=JSONResponse, name="main.ue_post")
async def ue_post(request: Request, 
                 ue_post_request: uePostRequest,
                 background_tasks: BackgroundTasks):
    try:
        aim_vnf_type = ue_post_request.ue_post_url.split('/')[-1]
        aim_ue_data_key = aim_vnf_type + '_data'
        data = {'traffic_from_ue': ue.name,
                aim_ue_data_key: ue_post_request.ue_post_data,
                'request_id': ue_post_request.request_id,
                'request_time': time.time()}
        background_tasks.add_task(post_to, data, ue_post_request.ue_post_url)

        print(f"{ue.name} {ue.type} processing successful")
        return JSONResponse(
            content={"message": f"{ue.name} {ue.type} processing successful"},
            status_code=status.HTTP_200_OK
        )

    except:
        print(f"{ue.name} {ue.type} processing failed")
        return JSONResponse(
            content={"message": f"{ue.name} {ue.type} processing failed"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

# ue print function---------------------------------------------------------------------------------------

class uePrintRequest(BaseModel):
    traffic_from_ue: str
    ue_print_data: Any
    request_id: int
    request_time: float

@router.post('/ue_print', response_class=JSONResponse, name='main.ue_print')
async def ue_print(request: Request,
                   ue_print_request: uePrintRequest):
    logger.info(f"recv - {ue_print_request.request_id}")
    used_time = time.time() - ue_print_request.request_time
    print(f"{ue.name} {ue.type} \n | pkg {ue_print_request.request_id} used time {used_time}")
    return JSONResponse(
            content={"message": f"ue {ue.name} processing successful"},
            status_code=status.HTTP_200_OK
        )