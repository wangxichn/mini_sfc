import requests
import numpy as np

def get_aim_vnf_url(vnf_info:dict):
    aim_vnf_url = f"http://{vnf_info['vnf_ip']}:{vnf_info['vnf_port']}/{vnf_info['vnf_type']}"
    return aim_vnf_url


def request_ue(ue_info:dict, vnf_info:dict, matrix_data:np.ndarray):
    aim_vnf_type = vnf_info['vnf_type']
    aim_vnf_data_key = aim_vnf_type + '_data'

    data = {'traffic_from_ue': ue_info['ue_name'],
            aim_vnf_data_key: matrix_data.tolist()}
    
    response = requests.post(get_aim_vnf_url(vnf_info), json=data)

    if response.status_code == 200:
        print('request matrix inv successfully')
    else:
        error_message = response.json().get('message', 'Unknown error')
        print(f'Failed matrix inv: {response.status_code} | {error_message}')


def request_set_route(vnf_info:dict, traffic_from_ue:str, traffic_to_url:str):
    vnf_opt_url = f"http://{vnf_info['vnf_ip']}:{vnf_info['vnf_port']}/set_route"

    data = {'traffic_from_ue': traffic_from_ue,
            'traffic_to_url': traffic_to_url}
    
    response = requests.post(vnf_opt_url, json=data)

    if response.status_code == 200:
        print('request set route successfully')
    else:
        error_message = response.json().get('message', 'Unknown error')
        print(f'Failed to set route: {response.status_code} | {error_message}')


if __name__ == '__main__':

    matrix_data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    vnf_1_info = {'vnf_name':'vnf_1','vnf_type':'vnf_matinv','vnf_ip':'192.168.31.80','vnf_port':'5001',
                  'vnf_cpu':'0.5', 'vnf_ram':'0.2', 'vnf_rom':'10'}
    vnf_2_info = {'vnf_name':'vnf_2','vnf_type':'vnf_matprint','vnf_ip':'192.168.31.80','vnf_port':'5002',
                  'vnf_cpu':'0.2', 'vnf_ram':'0.1', 'vnf_rom':'20'}
    vnf_3_info = {'vnf_name':'vnf_3','vnf_type':'vnf_gnb','vnf_ip':'192.168.31.80','vnf_port':'5003',
                  'vnf_cpu':'0.3', 'vnf_ram':'0.2', 'vnf_rom':'30'}
    ue_1_info = {'ue_name':'ue_1','vnf_ip':'192.168.31.80'}
    
    request_set_route(vnf_info=vnf_3_info,
                      traffic_from_ue=ue_1_info['ue_name'],
                      traffic_to_url=get_aim_vnf_url(vnf_info=vnf_1_info))
    
    request_set_route(vnf_info=vnf_1_info,
                      traffic_from_ue=ue_1_info['ue_name'],
                      traffic_to_url=get_aim_vnf_url(vnf_info=vnf_2_info))
    
    request_set_route(vnf_info=vnf_2_info,
                      traffic_from_ue=ue_1_info['ue_name'],
                      traffic_to_url=None)

    request_ue(ue_info=ue_1_info, vnf_info=vnf_3_info, matrix_data=matrix_data)
    


# # 设置vnf_gnb路由：
# curl -X POST http://10.0.0.4:5001/set_route \
#      -H "Content-Type: application/json" \
#      -d '{"traffic_from_ue": "ue_1", "traffic_to_url": "http://10.0.0.2:5001/vnf_matinv"}'

# # 设置vnf_matinv路由
# curl -X POST http://10.0.0.2:5001/set_route \
#      -H "Content-Type: application/json" \
#      -d '{"traffic_from_ue": "ue_1", "traffic_to_url": "http://10.0.0.3:5001/vnf_matprint"}'

# # 设置vnf_matprint路由
# curl -X POST http://10.0.0.3:5001/set_route \
#      -H "Content-Type: application/json" \
#      -d '{"traffic_from_ue": "ue_1", "traffic_to_url": null}'

# # 发送矩阵数据到vnf_gnb
# curl -X POST http://10.0.0.4:5001/vnf_gnb \
#      -H "Content-Type: application/json" \
#      -d '{"traffic_from_ue": "ue_1", "vnf_gnb_data": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}'
