
import numpy as np


class NumberOperator:
    def __init__(self) -> None:
        pass

    @staticmethod
    def generate_data_with_distribution(size: int, **kwargs):
        """
        Generate data with the given distribution and data type.
        
        Args:
            size (int): The size of the data.
            **kwargs: Keyword arguments to pass to the distribution generator.

        Returns:
            np.ndarray: The generated data.
        """
        distribution = kwargs.get('distribution')
        dtype = kwargs.get('dtype')

        assert distribution in ['uniform', 'normal', 'exponential', 'possion']
        assert dtype in ['int', 'float', 'bool']

        if distribution == 'normal':
            loc, scale = kwargs.get('loc'), kwargs.get('scale')
            data = np.random.normal(loc, scale, size)
        elif distribution == 'uniform':
            low, high = kwargs.get('low'), kwargs.get('high')
            if dtype == 'int':
                data = np.random.randint(low, high + 1, size)
            elif dtype == 'float':
                data = np.random.uniform(low, high, size)
        elif distribution == 'exponential':
            scale = kwargs.get('scale')
            data = np.random.exponential(scale, size)
        elif distribution == 'possion':
            lam = kwargs.get('lam')
            if kwargs.get('reciprocal', False):
                lam = 1 / lam
            data = np.random.poisson(lam, size)
        else:
            raise NotImplementedError(f'Generating {dtype} data following the {distribution} distribution is unsupporrted!')
        return data.astype(dtype).tolist()
