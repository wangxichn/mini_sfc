#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   test_pso_algorithm.py
@Time    :   2024/01/22 10:26:09
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from sko.PSO import PSO
import matplotlib.pyplot as plt
import numpy as np
import code

V_NET_SIZE = 5
P_NET_SIZE = 10
VALUE_MAT = np.random.random(size=(V_NET_SIZE,P_NET_SIZE))

def demo_func(x):
    x = np.array(x)
    x = x.reshape((V_NET_SIZE,P_NET_SIZE))
    value = 0
    for i in range(V_NET_SIZE):
        value += VALUE_MAT[i,np.where(x[i,:]==np.max(x[i,:]))[0][0]]
    return -value

pso = PSO(
    	func=demo_func, 
    	dim=V_NET_SIZE*P_NET_SIZE, pop=40, 
    	max_iter=150, 
    	lb=[0]*(V_NET_SIZE*P_NET_SIZE), 
    	ub=[1]*(V_NET_SIZE*P_NET_SIZE), 
    	w=0.8,
    	c1=0.5, 
    	c2=0.5)

# code.interact(banner="",local=locals())

pso.run()
print('best_x is ', pso.gbest_x, 'best_y is', pso.gbest_y)

plt.plot(pso.gbest_y_hist)
plt.show()

