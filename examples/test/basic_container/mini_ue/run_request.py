import requests
import numpy as np
import time

def get_aim_url(aim_info:dict):
    if aim_info != None:
        aim_type = list(aim_info.keys())[0].split('_')[0]
        if aim_type == 'vnf':
            aim_url = f"http://{aim_info['vnf_ip']}:{aim_info['vnf_port']}/{aim_info['vnf_type']}"
        elif aim_type == 'ue':
            aim_url = f"http://{aim_info['ue_ip']}:{aim_info['ue_port']}/{aim_info['ue_type']}"
        return aim_url
    else:
        return None

def get_aim_control_url(aim_info:dict):
    if aim_info != None:
        aim_type = list(aim_info.keys())[0].split('_')[0]
        if aim_type == 'vnf':
            aim_url = f"http://{aim_info['control_ip']}:{aim_info['vnf_port']}/{aim_info['vnf_type']}"
        elif aim_type == 'ue':
            aim_url = f"http://{aim_info['control_ip']}:{aim_info['ue_port']}/{aim_info['ue_type']}"
        return aim_url
    else:
        return None


def request_set_route(vnf_info:dict, traffic_from_ue:str, traffic_to_url:str):
    vnf_opt_url = f"http://{vnf_info['control_ip']}:{vnf_info['vnf_port']}/set_route"

    data = {'traffic_from_ue': traffic_from_ue,
            'traffic_to_url': traffic_to_url}
    
    print(f"{vnf_info['vnf_name']}  {vnf_info['vnf_type']}")
    print(f'--  {vnf_opt_url}   {data}')
    
    response = requests.post(vnf_opt_url, json=data)

    if response.status_code == 200:
        print('request set route successfully')
    else:
        error_message = response.json().get('message', 'Unknown error')
        print(f'Failed to set route: {response.status_code} | {error_message}')


def request_set_param(vnf_info:dict, param:int):
    vnf_opt_url = f"http://{vnf_info['control_ip']}:{vnf_info['vnf_port']}/{vnf_info['vnf_type']}/{param}"

    response = requests.post(vnf_opt_url)

    if response.status_code == 200:
        print('request set param successfully')
    else:
        error_message = response.json().get('message', 'Unknown error')
        print(f'Failed to set param: {response.status_code} | {error_message}')


def mano_set_route(sfc_info: dict, ue_info_list: list):
    for i, vnf_info in enumerate(sfc_info['vnfs']):
        if i != len(sfc_info['vnfs'])-1:
            for ue_info in ue_info_list:
                request_set_route(vnf_info=vnf_info,
                                  traffic_from_ue=ue_info['ue_name'],
                                  traffic_to_url=get_aim_url(aim_info=sfc_info['vnfs'][i+1]))
        else:
            for ue_info in ue_info_list:
                request_set_route(vnf_info=vnf_info,
                                  traffic_from_ue=ue_info['ue_name'],
                                  traffic_to_url=get_aim_url(aim_info=ue_info['ue_aim']))

def generate_invertible_matrix(size=10):
    while True:
        # 生成一个随机矩阵
        matrix = np.random.rand(size, size)
        # 计算行列式
        det = np.linalg.det(matrix)
        # 如果行列式不接近于零，则矩阵是可逆的
        if abs(det) > 1e-10:
            return matrix


def let_ue_request(ue_info:dict, sfc_info:dict, request_id:int):
    matrix_data = generate_invertible_matrix(50)

    data = {'ue_post_url': get_aim_url(sfc_info['vnfs'][0]),
            'ue_post_data': matrix_data.tolist(),
            'request_id': request_id}
    
    response = requests.post(get_aim_control_url(ue_info), json=data)

    if response.status_code == 200:
        print('request matrix inv successfully')
    else:
        error_message = response.json().get('message', 'Unknown error')
        print(f'Failed matrix inv: {response.status_code} | {error_message}')


if __name__ == '__main__':
    vnf_1_info = {'vnf_name':'vnf_1','vnf_type':'vnf_matinv','vnf_ip':'10.0.0.11','vnf_port':'5000',
                'vnf_cpu':'0.5', 'vnf_ram':'0.2', 'vnf_rom':'10', 'control_ip':'172.17.0.11'}
    vnf_2_info = {'vnf_name':'vnf_2','vnf_type':'vnf_matprint','vnf_ip':'10.0.0.12','vnf_port':'5000',
                    'vnf_cpu':'0.2', 'vnf_ram':'0.1', 'vnf_rom':'20', 'control_ip':'172.17.0.12'}
    vnf_3_info = {'vnf_name':'vnf_3','vnf_type':'vnf_gnb','vnf_ip':'10.0.0.13','vnf_port':'5000',
                    'vnf_cpu':'0.3', 'vnf_ram':'0.2', 'vnf_rom':'30', 'control_ip':'172.17.0.13'}
    vnf_4_info = {'vnf_name':'vnf_4','vnf_type':'vnf_gnb','vnf_ip':'10.0.0.14','vnf_port':'5000',
                    'vnf_cpu':'0.3', 'vnf_ram':'0.2', 'vnf_rom':'30', 'control_ip':'172.17.0.14'}
    
    ue_2_info = {'ue_name':'ue_2','ue_type':'ue_print','ue_ip':'10.0.0.102','ue_port':'8000',
             'control_ip':'172.17.0.102', 'ue_aim':None}
    ue_1_info = {'ue_name':'ue_1','ue_type':'ue_post','ue_ip':'10.0.0.101','ue_port':'8000',
                'control_ip':'172.17.0.101', 'ue_aim':ue_2_info}
    
    ue_info_list = [ue_1_info]

    sfc_1_info = {'sfc_name':'sfc_1','sfc_type':'sfc_matcal','vnfs':[vnf_3_info,vnf_1_info,vnf_4_info]}

    mano_set_route(sfc_1_info, ue_info_list)

    input()

    request_times = 0
    for _ in range(5):
        time.sleep(0.5)
        request_times += 1
        let_ue_request(ue_info=ue_1_info, sfc_info=sfc_1_info, request_id=request_times)
    
    # input()

    # request_set_param(vnf_info=vnf_1_info,param=10000)

    # input()

    # request_times = 0
    # for _ in range(5):
    #     time.sleep(0.5)
    #     request_times += 1
    #     let_ue_request(ue_info=ue_1_info, sfc_info=sfc_1_info, request_id=request_times)
    


