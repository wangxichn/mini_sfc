
import numpy as np
import networkx as nx
import random
import code

class NumberGen:
    def __init__(self) -> None:
        pass

    @staticmethod
    def getVector(size: int, **kwargs) -> np.ndarray:
        """Generate data with the given distribution and data type.
        
        Args:
            size (int): The size of the data.
            **kwargs: Keyword arguments to pass to the distribution generator.

        Returns:
            ndarray: The generated data.
        """
        distribution = kwargs.get('distribution')
        dtype = kwargs.get('dtype')

        assert distribution in ['uniform', 'normal', 'exponential', 'possion']
        assert dtype in ['int', 'float']

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
        return data.astype(dtype)
    
    @staticmethod
    def getMatrix(size: int, **kwargs):
        type = kwargs.get('type')
        dtype = kwargs.get('dtype')
        assert type in ['symmetric'], ValueError('Unsupported topo type!')
        assert dtype in ['int', 'float']
        if type == 'symmetric':
            low, high = kwargs.get('low',0), kwargs.get('high',1)
            if dtype == 'int':
                data = np.random.randint(low, high+1, size**2)
            elif dtype == 'float':
                data = np.random.uniform(low, high, size**2)
            
            X = data.reshape(size, size)
            X = np.triu(X)
            X += X.T - 2*np.diag(X.diagonal())
        
        return X


class TopoGen:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get(size: int, **kwargs):
        """Generates topological adjacency matrix of specified size and shape

        Args:
            size (int): the size of topo
            **kwargs (dict): {'type':'path/star/waxman'}
                if {'type':'waxman'} can further {'wm_alpha':value, 'wm_beta':value}
            
        Returns:
            adjacency matrix of the topo (NDArray)
            
        """
        assert size >= 1
        type = kwargs.get('type')
        assert type in ['path', 'star', 'waxman'], ValueError('Unsupported topo type!')

        if type == 'path':
            G = nx.path_graph(size)
        elif type == 'star':
            G = nx.star_graph(size)
        elif type == 'waxman':
            wm_alpha = kwargs.get('wm_alpha', 0.5)
            wm_beta = kwargs.get('wm_beta', 0.2)
            not_connected = True
            while not_connected:
                G = nx.waxman_graph(size, wm_alpha, wm_beta)
                not_connected = not nx.is_connected(G)
        elif type == 'tree':
            G = nx.Graph()
            G.add_node(1)
            current_node = 1
            for new_node in range(2, size + 1):
                father_node = random.randint(1, current_node)
                G.add_node(new_node)
                G.add_edge(new_node, father_node)
                current_node = new_node
        else:
            raise NotImplementedError
        
        for i in range(size):
            G.add_edge(i,i)
        
        return np.array(nx.adjacency_matrix(G,weight=None).todense())
    
    @staticmethod
    def cut_to_stp(adj_matrix: np.ndarray, source_node: int = 1):
        G = nx.from_numpy_array(adj_matrix)
        spanning_tree = nx.dfs_tree(G, source_node)
        st_adj_matrix = np.array(nx.adjacency_matrix(spanning_tree, weight=None).todense())
        
        for i in range(st_adj_matrix.shape[0]):
            st_adj_matrix[i, i] = 1  
        
        return st_adj_matrix
        