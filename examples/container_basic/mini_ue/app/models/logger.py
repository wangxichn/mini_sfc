import logging
from .ue import ue

logger = logging.getLogger(f'{ue.name}_logger')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(f'instance/{ue.name}.log', mode='w')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
