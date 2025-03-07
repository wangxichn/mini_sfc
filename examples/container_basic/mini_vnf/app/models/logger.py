import logging
from .vnf import vnf

logger = logging.getLogger(f'{vnf.name}_logger')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(f'instance/{vnf.name}.log', mode='w')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
