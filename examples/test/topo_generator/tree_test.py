import networkx as nx
import random

def generate_random_tree(num_nodes):
    # 创建一个空的无向图
    G = nx.Graph()

    # 添加根节点
    G.add_node(1)

    current_node = 1
    for new_node in range(2, num_nodes + 1):
        # 随机选择一个已存在的节点作为新节点的父亲
        father_node = random.randint(1, current_node)
        
        # 添加新节点以及它与父亲之间的边
        G.add_node(new_node)
        G.add_edge(new_node, father_node)
        
        # 更新当前最大节点编号
        current_node = new_node
    
    return G

# 生成一个包含100个节点的随机树
num_nodes = 100
random_tree = generate_random_tree(num_nodes)

# 打印生成的树的所有边，表示节点间的连接关系
print("Edges of the generated tree:")
for edge in random_tree.edges():
    print(edge)

# 如果想要可视化这个树状拓扑，可以使用matplotlib
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 8))
pos = nx.spring_layout(random_tree)  # 定义布局
nx.draw(random_tree, pos, with_labels=True, node_color='lightblue', font_size=10, font_weight="bold", node_size=500)
plt.show()