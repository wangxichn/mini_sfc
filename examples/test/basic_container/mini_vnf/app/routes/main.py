
from fastapi import APIRouter, Request, status, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator 
import numpy as np
import httpx
from ..models.vnf import vnf
from ..models.logger import logger
import time


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# public route-------------------------------------------------------------------------------------

@router.get('/', response_class=HTMLResponse, name="main.index")
def index(request: Request):
    """
    获取该 vnf 信息
    """
    return templates.TemplateResponse('index.html', {'request': request, 'vnf': vnf})


class setRouteRequest(BaseModel):
    traffic_from_ue: str = Field(..., description="Cannot be empty")
    traffic_to_url: Optional[str] = None

    @field_validator ('traffic_from_ue')
    def traffic_from_ue_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Traffic from Name must not be empty.')
        return v.strip()

@router.post('/set_route', response_class=JSONResponse, name="main.set_route")
async def set_route(set_route_request: setRouteRequest):
    add_route_from = set_route_request.traffic_from_ue
    add_route_to = set_route_request.traffic_to_url

    save_route = vnf.route.get(add_route_from, [])

    if add_route_to is not None:
        if not save_route:
            vnf.route[add_route_from] = [add_route_to]
        else:
            vnf.route[add_route_from].append(add_route_to)
    else:
        vnf.route[add_route_from] = []

    print(f"{vnf.name} {vnf.type} route set successfully")
    return JSONResponse(
        content={"message": f"{vnf.name} {vnf.type} route set successfully"},
        status_code=status.HTTP_200_OK
    )

# public tool---------------------------------------------------------------------------------------

async def post_to(data: dict, aim_url: str):
    try:
        logger.info(f"send - {data['request_id']}")
        async with httpx.AsyncClient() as client:
            response = await client.post(aim_url, json=data)
            response.raise_for_status()
        used_time = time.time() - data['request_time']
        print(f"{vnf.name} {vnf.type} post to: {aim_url} | pkg {data['request_id']} used time {used_time}")
    except httpx.RequestError as exc:
        print(f"{vnf.name} {vnf.type} request failed: {exc}")
    except httpx.HTTPStatusError as exc:
        print(f"{vnf.name} {vnf.type} http error: {exc.response.status_code}, {exc.response.text}")


# vnf_gnb ------------------------------------------------------------------------------------------
class gnbRequest(BaseModel):
    traffic_from_ue: str
    vnf_gnb_data: Any
    request_id: int
    request_time: float

@router.post('/vnf_gnb',response_class=JSONResponse, name="main.vnf_gnb")
async def vnf_gnb(request: Request, 
                  gnb_request: gnbRequest,
                  background_tasks: BackgroundTasks):
    if vnf.type == 'vnf_gnb':
        try:
            # post to next url with route record
            traffic_from = gnb_request.traffic_from_ue
            save_route = vnf.route.get(traffic_from)
            if save_route == [] or save_route == None: # check
                print(f"{vnf.name} {vnf.type} was unable to forward the result from {traffic_from}")
                return JSONResponse(
                    content={"message": f"{vnf.name} {vnf.type} was unable to forward the result from {traffic_from}"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            else: # post
                logger.info(f"recv - {gnb_request.request_id}")
                for aim_url in save_route:
                    aim_vnf_type = aim_url.split('/')[-1]
                    aim_vnf_data_key = aim_vnf_type + '_data'
                    data = {'traffic_from_ue': traffic_from, 
                            aim_vnf_data_key: gnb_request.vnf_gnb_data,
                            'request_id': gnb_request.request_id,
                            'request_time': gnb_request.request_time}
                    background_tasks.add_task(post_to, data, aim_url)

            return JSONResponse(
                content={"message": f"{vnf.name} {vnf.type} processing successful"},
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            print(f"{vnf.name} {vnf.type} processing failed for {e}")
            return JSONResponse(
                content={"message": f"{vnf.name} {vnf.type} processing failed"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
    else:
        print(f"Error {vnf.name} {vnf.type} request type")
        return JSONResponse(
            content={"message": f"Error {vnf.name} {vnf.type} request type"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    

# vnf_matinv ---------------------------------------------------------------------------------------

class matinvRequest(BaseModel):
    traffic_from_ue: str
    vnf_matinv_data: list[list[float]]
    request_id: int
    request_time: float

@router.post('/vnf_matinv',response_class=JSONResponse, name="main.vnf_matinv")
async def vnf_matinv(request: Request, 
                     matinv_request: matinvRequest,
                     background_tasks: BackgroundTasks):
    if vnf.type == 'vnf_matinv':
        try:
            # post to next url with route record
            traffic_from = matinv_request.traffic_from_ue
            save_route = vnf.route.get(traffic_from)
            if save_route == [] or save_route == None: # check
                print(f"{vnf.name} {vnf.type} was unable to forward the result from {traffic_from}")
                return JSONResponse(
                    content={"message": f"{vnf.name} {vnf.type} was unable to forward the result from {traffic_from}"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            else: # post
                logger.info(f"recv - {matinv_request.request_id}")
                matrix_data_np = np.array(matinv_request.vnf_matinv_data)

                starttime = time.time()
                for _ in range(vnf.param):
                    matrix_data_np = np.linalg.inv(matrix_data_np)
                    perturbation = np.random.randn(matrix_data_np.shape[0], matrix_data_np.shape[1]) * 1e-6
                    matrix_data_np += perturbation
                print(f"************************************************ need time {time.time()-starttime}")

                for aim_url in save_route:
                    aim_vnf_type = aim_url.split('/')[-1]
                    aim_vnf_data_key = aim_vnf_type + '_data'
                    data = {'traffic_from_ue': traffic_from, 
                            aim_vnf_data_key: matrix_data_np.tolist(),
                            'request_id': matinv_request.request_id,
                            'request_time': matinv_request.request_time}
                    background_tasks.add_task(post_to, data, aim_url)

            return JSONResponse(
                content={"message": f"{vnf.name} {vnf.type} processing successful"},
                status_code=status.HTTP_200_OK
            )

        except:
            print(f"{vnf.name} {vnf.type} processing failed")
            return JSONResponse(
                content={"message": f"{vnf.name} {vnf.type} processing failed"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
    else:
        print(f"Error {vnf.name} {vnf.type} request type")
        return JSONResponse(
            content={"message": f"Error {vnf.name} {vnf.type} request type"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.post('/vnf_matinv/{inv_times}')
async def vnf_matinv_param(inv_times:int, response_class=JSONResponse):
    if vnf.type == 'vnf_matinv':
        vnf.param = inv_times
        print(f"{vnf.name} {vnf.type} set inv times {vnf.param}")
        return JSONResponse(
                content={"message": f"{vnf.name} {vnf.type} set inv times {vnf.param}"},
                status_code=status.HTTP_200_OK
            )
    else:
        print(f"Error {vnf.name} {vnf.type} request type")
        return JSONResponse(
            content={"message": f"Error {vnf.name} {vnf.type} request type"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

# vnf_matprint ---------------------------------------------------------------------------------------

class matprintRequest(BaseModel):
    traffic_from_ue: str
    vnf_matprint_data: list[list[float]]
    request_id: int
    request_time: float

@router.post('/vnf_matprint',response_class=JSONResponse, name="main.vnf_matprint")
async def vnf_matprint(request: Request, matprint_request: matprintRequest):
    if vnf.type == 'vnf_matprint':
        try:
            traffic_from = matprint_request.traffic_from_ue
            save_route = vnf.route.get(traffic_from, None)
            if save_route == [] or save_route == None: # check
                print(f"{vnf.name} {vnf.type} was unable to retrieve the source {traffic_from}")
                return JSONResponse(
                    content={"message": f"{vnf.name} {vnf.type} was unable to retrieve the source {traffic_from}"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            else: # print
                logger.info(f"recv - {matprint_request.request_id}")
                used_time = time.time() - matprint_request.request_time
                print(f"{vnf.name} {vnf.type} print:\n {matprint_request}\n | pkg {matprint_request.request_id} used time {used_time}")
                return JSONResponse(
                    content={"message": f"Vnf {vnf.name} processing successful"},
                    status_code=status.HTTP_200_OK
                )

        except:
            print(f"{vnf.name} {vnf.type} processing failed")
            return JSONResponse(
                content={"message": f"{vnf.name} {vnf.type} processing failed"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
    else:
        print(f"Error {vnf.name} {vnf.type} request type")
        return JSONResponse(
            content={"message": f"Error {vnf.name} {vnf.type} request type"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
