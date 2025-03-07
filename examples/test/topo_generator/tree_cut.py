import networkx as nx
import matplotlib.pyplot as plt

def prune_to_spanning_tree(G):
    """
    从给定的图G中剪枝得到一个生成树。
    
    参数:
        G (nx.Graph): 输入的原始图。
        
    返回:
        nx.Graph: 剪枝后的生成树。
    """
    # 使用深度优先搜索(DFS)获取生成树
    spanning_tree = nx.dfs_tree(G, source=1)  # 可以选择任意起点作为source
    
    return spanning_tree

# 创建一个随机图
random_graph = nx.erdos_renyi_graph(10, 0.3)

# 将其转换为生成树
tree = prune_to_spanning_tree(random_graph)

# 定义绘图布局
pos = nx.spring_layout(random_graph)  # 我们将使用相同的布局使两张图易于比较

# 创建图形并调整大小
plt.figure(figsize=(16, 8))

# 绘制原始图
plt.subplot(1, 2, 1)  # 分割窗口为1行2列，并激活第一个用于画图
nx.draw(random_graph, pos, with_labels=True, node_color='lightblue', font_size=10, font_weight="bold", node_size=500)
plt.title("Original Graph")

# 绘制生成树
plt.subplot(1, 2, 2)  # 激活第二个用于画图
nx.draw(tree, pos, with_labels=True, node_color='lightgreen', font_size=10, font_weight="bold", node_size=500)
plt.title("Pruned Spanning Tree")

# 显示图形
plt.show()