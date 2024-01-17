import networkx as nx
import matplotlib.pyplot as plt

list_a = [1, 2, 3, 4]

for item in list_a[:]:
    if item > 2:
        list_a.remove(item)

print(list_a)
