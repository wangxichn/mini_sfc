
from minisfc.event import Event
from minisfc.topo import ServiceTopo, SubstrateTopo, Topo
from minisfc.solver import RandomSolver, GreedySolver, Solution, SOLUTION_TYPE
from .drlSfcpSolver.drlSfcpSolver import DrlSfcpSolver
import numpy as np
import networkx as nx
import random
from sko.PSO import PSO
from scipy.optimize import differential_evolution,NonlinearConstraint
import warnings
warnings.filterwarnings("ignore", message="delta_grad == 0.0. Check if the approximated function is linear.")
import copy
import code

class netcalPsoSolver(RandomSolver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo, **kwargs) -> None:
        super().__init__(substrateTopo, serviceTopo, **kwargs)

    def solve_embedding(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfNodeNum = len(self.sfcGraph.nodes)
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        vnfFactorList = np.array([self.vnfManager.vnfPoolDict[vnfId].vnf_factor for vnfId in vnfRequstList])
        vnfFactorList_ex = np.insert(vnfFactorList, 0, 1.0)
        vnfFactorProd = np.cumprod(vnfFactorList_ex)
        vnfFactorStar = np.cumprod(vnfFactorList[::-1])[::-1]
        vnfMassageLenInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][2]
        vnfMassageLenList = np.array([vnfMassageLenInit]*vnfNodeNum)*vnfFactorList
        vnfArriveRateInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][0]
        vnfBurstBitInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][1]

        self.solution.resource['cpu'] = vnfArriveRateInit*vnfFactorProd[0:-1]
        self.solution.resource['ram'] = np.array([vnfArriveRateInit*vnfMassageLenList[i]/self.solution.resource['cpu'][i]+vnfBurstBitInit 
                                                    for i in range(vnfNodeNum)])*vnfFactorProd[:-1]
        self.solution.resource['band'] = np.array([self.solution.resource['cpu'][i]*vnfFactorList[i] for i in range(vnfNodeNum)])
        self.netcalLatency = vnfFactorProd[-1]*vnfBurstBitInit/(self.solution.resource['cpu']*vnfFactorStar).min() \
                            +(vnfMassageLenList/self.solution.resource['cpu']).sum()

        pso = PSO(
    	    func=self.fitness, 
    	    dim=len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes),
            pop=50, 
    	    max_iter=10, 
    	    lb=[0]*(len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes)), 
    	    ub=[1]*(len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes)), 
    	    w=0.8,
    	    c1=0.5, 
    	    c2=0.5)
        pso.run()

        x = np.array(pso.gbest_x)
        x = x.reshape((len(self.sfcGraph.nodes),len(self.substrateTopo.nodes)))
        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = np.where(x[v_node,:]==np.max(x[v_node,:]))[0][0]
        
        for v_link in self.sfcGraph.edges():
            try:
                map_path = nx.dijkstra_path(self.substrateTopo,
                                            self.solution.map_node[v_link[0]],
                                            self.solution.map_node[v_link[1]])
            except:
                self.solution.current_description = SOLUTION_TYPE.SET_FAILED_FOR_LINK_BAND
                break
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        # algorithm end ---------------------------------------------

        if self.solution.current_description == SOLUTION_TYPE.NOTHING:
            self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId]=[self.solution]

        return self.solution
    
    def solve_migration(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfNodeNum = len(self.sfcGraph.nodes)
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        vnfFactorList = np.array([self.vnfManager.vnfPoolDict[vnfId].vnf_factor for vnfId in vnfRequstList])
        vnfFactorList_ex = np.insert(vnfFactorList, 0, 1.0)
        vnfFactorProd = np.cumprod(vnfFactorList_ex)
        vnfFactorStar = np.cumprod(vnfFactorList[::-1])[::-1]
        vnfMassageLenInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][2]
        vnfMassageLenList = np.array([vnfMassageLenInit]*vnfNodeNum)*vnfFactorList
        vnfArriveRateInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][0]
        vnfBurstBitInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][1]

        self.solution.resource['cpu'] = vnfArriveRateInit*vnfFactorProd
        self.solution.resource['ram'] = np.array([vnfArriveRateInit*vnfMassageLenList[i]/self.solution.resource['cpu'][i]+vnfBurstBitInit 
                                                    for i in range(vnfNodeNum)])*vnfFactorProd[:-1]
        self.solution.resource['band'] = np.array([self.solution.resource['cpu'][i]*vnfFactorList[i] for i in range(vnfNodeNum)])
        
        pso = PSO(
    	    func=self.fitness, 
    	    dim=len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes),
            pop=50, 
    	    max_iter=10, 
    	    lb=[0]*(len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes)), 
    	    ub=[1]*(len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes)), 
    	    w=0.8,
    	    c1=0.5, 
    	    c2=0.5)
        pso.run()

        x = np.array(pso.gbest_x)
        x = x.reshape((len(self.sfcGraph.nodes),len(self.substrateTopo.nodes)))
        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = np.where(x[v_node,:]==np.max(x[v_node,:]))[0][0]
        
        for v_link in self.sfcGraph.edges():
            try:
                map_path = nx.dijkstra_path(self.substrateTopo,
                                            self.solution.map_node[v_link[0]],
                                            self.solution.map_node[v_link[1]])
            except:
                self.solution.current_description = SOLUTION_TYPE.CHANGE_FAILED_FOR_LINK_BAND
                break

            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        # algorithm end ---------------------------------------------

        if self.solution.current_description == SOLUTION_TYPE.NOTHING:
            self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.CHANGE_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId].append(self.solution)

        return self.solution
    
    
    def fitness(self,*Args):
        x = np.array(Args)
        x = x.reshape((len(self.sfcGraph.nodes),len(self.substrateTopo.nodes)))
        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = np.where(x[v_node,:]==np.max(x[v_node,:]))[0][0]

        for v_link in self.sfcGraph.edges():
            try:
                map_path = nx.dijkstra_path(self.substrateTopo,
                                            self.solution.map_node[v_link[0]],
                                            self.solution.map_node[v_link[1]])
            except:
                self.solution.current_description = SOLUTION_TYPE.SET_FAILED_FOR_LINK_BAND
                break
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]

        if self.check_constraints(self.event) not in (SOLUTION_TYPE.SET_SUCCESS,SOLUTION_TYPE.CHANGE_SUCCESS,
                                                      SOLUTION_TYPE.SET_FAILED_FOR_LATENCY,SOLUTION_TYPE.CHANGE_FAILED_FOR_LATENCY):
            return float("inf")
        else:
            return self.get_latency_running()-self.event.serviceTopo.plan_qosRequesDict[self.event.serviceTopoId][0]

    def get_latency_running(self) -> float:
        return super().get_latency_running()+self.netcalLatency


class netcalOptSolver(RandomSolver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo, **kwargs) -> None:
        super().__init__(substrateTopo, serviceTopo, **kwargs)
    
    def solve_embedding(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfNodeNum = len(self.sfcGraph.nodes)
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        vnfFactorList = np.array([self.vnfManager.vnfPoolDict[vnfId].vnf_factor for vnfId in vnfRequstList])
        vnfFactorList_ex = np.insert(vnfFactorList, 0, 1.0)
        vnfFactorProd = np.cumprod(vnfFactorList_ex)
        vnfFactorStar = np.cumprod(vnfFactorList[::-1])[::-1]
        vnfMassageLenInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][2]
        vnfMassageLenList = np.array([vnfMassageLenInit]*vnfNodeNum)*vnfFactorList
        vnfArriveRateInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][0]
        vnfBurstBitInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][1]

        try:
            kshortest_paths = self.substrateTopo.get_kshortest_paths(self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][0],
                                                                    self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][1],
                                                                    5)
        except:
            kshortest_paths = []
            self.solution.current_description = SOLUTION_TYPE.SET_FAILED_FOR_LINK_BAND

        for temp_p_nodes in kshortest_paths:
            if vnfNodeNum > len(temp_p_nodes):
                # assume temp_p_nodes = [41, 8, 7, 6] | vnfNode = [0,1,2,3,4,5,6,7,8,9]
                temp_p_node_resource = [self.substrateTopo.opt_node_attrs_value(p_node,'remain_cpu','get') for p_node in temp_p_nodes]
                if sum(temp_p_node_resource) == 0:
                    continue
                temp_p_node_resource_rate = np.array(temp_p_node_resource)/sum(temp_p_node_resource) # [0.178, 0.163, 0.357, 0.300]
                temp_p_node_vnf_node_num = np.rint(temp_p_node_resource_rate*vnfNodeNum)
                temp_p_node_vnf_node_num[-1] = vnfNodeNum-np.sum(temp_p_node_vnf_node_num[0:-1]) # [2,2,4,2]

                temp_p_node_vnf_node = [] # [[0, 1], [2, 3], [4, 5, 6, 7], [8, 9]]
                temp_start = 0
                for node_num in temp_p_node_vnf_node_num:
                    temp_end = temp_start + int(node_num)
                    temp_p_node_vnf_node.append(list(range(vnfNodeNum))[temp_start:temp_end])
                    temp_start = temp_end
            else:
                # assume temp_p_nodes = [41, 8, 32, 18, 5, 6, 2, 23, 3, 10, 7, 6] | vnfNode = [0,1,2,3,4,5,6,7,8,9]
                temp_p_nodes_sort = sorted(temp_p_nodes,
                                        key=lambda x: self.substrateTopo.opt_node_attrs_value(x,'remain_cpu','get'),
                                        reverse=True)[0:vnfNodeNum] # [22, 2, 7, 32, 23, 6, 18, 5, 3, 10]
                temp_p_nodes_choose = []
                for p_node in temp_p_nodes:
                    if p_node in temp_p_nodes_sort:
                        temp_p_nodes_choose.append(p_node)
                temp_p_nodes = temp_p_nodes_choose # [32, 18, 5, 6, 2, 23, 3, 10, 7, 6]
                temp_p_node_vnf_node = [[i] for i in range(vnfNodeNum)] # [[0], [1], [2], [3], [4], [5], [6], [7], [8], [9]]

            for v_node in self.sfcGraph.nodes:
                if v_node == 0:
                    self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][0]
                elif v_node == (len(self.sfcGraph.nodes)-1):
                    self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][1]
                else:
                    for i,sublist in enumerate(temp_p_node_vnf_node):
                        if v_node in sublist:
                            self.solution.map_node[v_node] = temp_p_nodes[i]
                            break
            
            for v_link in self.sfcGraph.edges():
                map_path = nx.dijkstra_path(self.substrateTopo,
                                            self.solution.map_node[v_link[0]],
                                            self.solution.map_node[v_link[1]])
                if len(map_path) == 1: 
                    self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
                else:
                    self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
            
            # begin optimal -----------
            def aim(x):
                return x.sum()
            vnfResourceLimitUp = [self.substrateTopo.opt_node_attrs_value(self.solution.map_node[v_node],'remain_cpu','get') 
                                for v_node in self.sfcGraph.nodes]
            bounds = [(vnfBurstBitInit*vnfFactorProd[v_node], vnfResourceLimitUp[v_node]) for v_node in self.sfcGraph.nodes]
            boundscheckflag = True
            for boundtemp in bounds:
                if not boundtemp[0]<=boundtemp[1]:
                    boundscheckflag = False
                    break
            if boundscheckflag == False:
                self.solution.current_description = SOLUTION_TYPE.SET_FAILED_FOR_NODE_CPU
                continue

            def constr_f(x):
                return vnfFactorProd[-1]*vnfBurstBitInit/(x*vnfFactorStar).min()+(vnfMassageLenList/x).sum()
            
            remain_latency = event.serviceTopo.plan_qosRequesDict[event.serviceTopoId]-super().get_latency_running()
            nlc = NonlinearConstraint(constr_f,0,remain_latency)
            result = differential_evolution(aim, bounds, constraints=(nlc))
            
            self.solution.resource['cpu'] = np.ceil(result.x)
            self.solution.resource['ram'] = np.array([vnfArriveRateInit*vnfMassageLenList[i]/self.solution.resource['cpu'][i]+vnfBurstBitInit 
                                                        for i in range(vnfNodeNum)])*vnfFactorProd[:-1]
            self.solution.resource['band'] = np.array([self.solution.resource['cpu'][i]*vnfFactorList[i] for i in range(vnfNodeNum)])
            self.netcalLatency = constr_f(result.x)
            # end optimal ------------
            if self.check_constraints(event) == SOLUTION_TYPE.SET_SUCCESS: break
        
        # algorithm end ---------------------------------------------

        try:
            if self.solution.current_description == SOLUTION_TYPE.NOTHING:
                self.solution.current_description = self.check_constraints(event)

            if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
                self.solution.current_result = False
            else:
                self.solution.current_result = True
                self.solution.resource['cpu']
            
            self.record_solutions[self.event.serviceTopoId]=[copy.deepcopy(self.solution)]
            
        except:
            code.interact(banner="",local=locals())

        return self.solution

    def solve_migration(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfNodeNum = len(self.sfcGraph.nodes)
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        vnfFactorList = np.array([self.vnfManager.vnfPoolDict[vnfId].vnf_factor for vnfId in vnfRequstList])
        vnfFactorList_ex = np.insert(vnfFactorList, 0, 1.0)
        vnfFactorProd = np.cumprod(vnfFactorList_ex)
        vnfFactorStar = np.cumprod(vnfFactorList[::-1])[::-1]
        vnfMassageLenInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][2]
        vnfMassageLenList = np.array([vnfMassageLenInit]*vnfNodeNum)*vnfFactorList
        vnfArriveRateInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][0]
        vnfBurstBitInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][1]

        try:
            kshortest_paths = self.substrateTopo.get_kshortest_paths(self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][0],
                                                                    self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][1],
                                                                    5)
            
            kshortest_paths = self.substrateTopo.get_kshortest_paths(event.serviceTopo.plan_endPointDict[event.serviceTopoId][0],event.serviceTopo.plan_endPointDict[event.serviceTopoId][1],5)
        except:
            kshortest_paths = []
            self.solution.current_description = SOLUTION_TYPE.CHANGE_FAILED_FOR_LINK_BAND

        for temp_p_nodes in kshortest_paths:
            if vnfNodeNum > len(temp_p_nodes):
                # assume temp_p_nodes = [41, 8, 7, 6] | vnfNode = [0,1,2,3,4,5,6,7,8,9]
                temp_p_node_resource = [self.substrateTopo.opt_node_attrs_value(p_node,'remain_cpu','get') for p_node in temp_p_nodes]
                if sum(temp_p_node_resource) == 0:
                    continue
                temp_p_node_resource_rate = np.array(temp_p_node_resource)/sum(temp_p_node_resource) # [0.178, 0.163, 0.357, 0.300]
                temp_p_node_vnf_node_num = np.rint(temp_p_node_resource_rate*vnfNodeNum)
                temp_p_node_vnf_node_num[-1] = vnfNodeNum-np.sum(temp_p_node_vnf_node_num[0:-1]) # [2,2,4,2]

                temp_p_node_vnf_node = [] # [[0, 1], [2, 3], [4, 5, 6, 7], [8, 9]]
                temp_start = 0
                for node_num in temp_p_node_vnf_node_num:
                    temp_end = temp_start + int(node_num)
                    temp_p_node_vnf_node.append(list(range(vnfNodeNum))[temp_start:temp_end])
                    temp_start = temp_end
            else:
                # assume temp_p_nodes = [41, 8, 32, 18, 5, 6, 2, 23, 3, 10, 7, 6] | vnfNode = [0,1,2,3,4,5,6,7,8,9]
                temp_p_nodes_sort = sorted(temp_p_nodes,
                                        key=lambda x: self.substrateTopo.opt_node_attrs_value(x,'remain_cpu','get'),
                                        reverse=True)[0:vnfNodeNum] # [22, 2, 7, 32, 23, 6, 18, 5, 3, 10]
                temp_p_nodes_choose = []
                for p_node in temp_p_nodes:
                    if p_node in temp_p_nodes_sort:
                        temp_p_nodes_choose.append(p_node)
                temp_p_nodes = temp_p_nodes_choose # [32, 18, 5, 6, 2, 23, 3, 10, 7, 6]
                temp_p_node_vnf_node = [[i] for i in range(vnfNodeNum)] # [[0], [1], [2], [3], [4], [5], [6], [7], [8], [9]]

            for v_node in self.sfcGraph.nodes:
                if v_node == 0:
                    self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][0]
                elif v_node == (len(self.sfcGraph.nodes)-1):
                    self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][1]
                else:
                    for i,sublist in enumerate(temp_p_node_vnf_node):
                        if v_node in sublist:
                            self.solution.map_node[v_node] = temp_p_nodes[i]
                            break
            
            for v_link in self.sfcGraph.edges():
                map_path = nx.dijkstra_path(self.substrateTopo,
                                            self.solution.map_node[v_link[0]],
                                            self.solution.map_node[v_link[1]])
                if len(map_path) == 1: 
                    self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
                else:
                    self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
            
            # begin optimal -----------
            def aim(x):
                return x.sum()
            vnfResourceLimitUp = [self.substrateTopo.opt_node_attrs_value(self.solution.map_node[v_node],'remain_cpu','get') 
                                for v_node in self.sfcGraph.nodes]
            bounds = [(vnfBurstBitInit*vnfFactorProd[v_node], vnfResourceLimitUp[v_node]) for v_node in self.sfcGraph.nodes]
            boundscheckflag = True
            for boundtemp in bounds:
                if not boundtemp[0]<=boundtemp[1]:
                    boundscheckflag = False
                    break
            if boundscheckflag == False:
                self.solution.current_description = SOLUTION_TYPE.CHANGE_FAILED_FOR_NODE_CPU
                continue
            
            def constr_f(x):
                return vnfFactorProd[-1]*vnfBurstBitInit/(x*vnfFactorStar).min()+(vnfMassageLenList/x).sum()
            
            remain_latency = event.serviceTopo.plan_qosRequesDict[event.serviceTopoId]-super().get_latency_running()
            nlc = NonlinearConstraint(constr_f,0,remain_latency)
            result = differential_evolution(aim, bounds, constraints=(nlc))
            
            self.solution.resource['cpu'] = np.ceil(result.x)
            self.solution.resource['ram'] = np.array([vnfArriveRateInit*vnfMassageLenList[i]/self.solution.resource['cpu'][i]+vnfBurstBitInit 
                                                        for i in range(vnfNodeNum)])*vnfFactorProd[:-1]
            self.solution.resource['band'] = np.array([self.solution.resource['cpu'][i]*vnfFactorList[i] for i in range(vnfNodeNum)])
            self.netcalLatency = constr_f(result.x)
            # end optimal ------------
            if self.check_constraints(event) == SOLUTION_TYPE.CHANGE_SUCCESS: break
        
        # algorithm end ---------------------------------------------

        try:
            if self.solution.current_description == SOLUTION_TYPE.NOTHING:
                self.solution.current_description = self.check_constraints(event)

            if self.solution.current_description != SOLUTION_TYPE.CHANGE_SUCCESS:
                self.solution.current_result = False
            else:
                self.solution.current_result = True
                self.solution.resource['cpu']
            
            self.record_solutions[self.event.serviceTopoId].append(copy.deepcopy(self.solution))

        except:
            code.interact(banner='',local=locals())

        return self.solution

    def get_latency_running(self) -> float:
        return super().get_latency_running()+self.netcalLatency


class netcalSfcpSolver(DrlSfcpSolver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo, **kwargs) -> None:
        super().__init__(substrateTopo, serviceTopo, **kwargs)

    def solve_embedding(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfNodeNum = len(self.sfcGraph.nodes)
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        vnfFactorList = np.array([self.vnfManager.vnfPoolDict[vnfId].vnf_factor for vnfId in vnfRequstList])
        vnfFactorList_ex = np.insert(vnfFactorList, 0, 1.0)
        vnfFactorProd = np.cumprod(vnfFactorList_ex)
        vnfFactorStar = np.cumprod(vnfFactorList[::-1])[::-1]
        vnfMassageLenInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][2]
        vnfMassageLenList = np.array([vnfMassageLenInit]*vnfNodeNum)*vnfFactorList
        vnfArriveRateInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][0]
        vnfBurstBitInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][1]

        self.solution.resource['cpu'] = vnfArriveRateInit*vnfFactorProd[0:-1]
        self.solution.resource['ram'] = np.array([vnfArriveRateInit*vnfMassageLenList[i]/self.solution.resource['cpu'][i]+vnfBurstBitInit 
                                                    for i in range(vnfNodeNum)])*vnfFactorProd[:-1]
        self.solution.resource['band'] = np.array([self.solution.resource['cpu'][i]*vnfFactorList[i] for i in range(vnfNodeNum)])
        self.netcalLatency = vnfFactorProd[-1]*vnfBurstBitInit/(self.solution.resource['cpu']*vnfFactorStar).min() \
                            +(vnfMassageLenList/self.solution.resource['cpu']).sum()

        subsolution, subbuffer, lastvalue = self.learn(event,self.solution)
        self.merge_experience(subsolution,subbuffer)

        if self.buffer.size() >= 128:
            self.update()

        if subsolution.result == True:
            for i,node in enumerate(self.sfcGraph.nodes):
                self.solution.map_node[node] = subsolution.selected_actions[i]
        else:
            for i,node in enumerate(self.sfcGraph.nodes):
                self.solution.map_node[node] = random.sample(range(len(self.substrateTopo.nodes)),1)[0]

        for v_link in self.sfcGraph.edges():
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId]=[self.solution]

        return self.solution
    
    def get_latency_running(self) -> float:
        return super().get_latency_running()+self.netcalLatency


class netcalRandomSolver(RandomSolver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo, **kwargs) -> None:
        super().__init__(substrateTopo, serviceTopo, **kwargs)

    def solve_embedding(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfNodeNum = len(self.sfcGraph.nodes)
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        vnfFactorList = np.array([self.vnfManager.vnfPoolDict[vnfId].vnf_factor for vnfId in vnfRequstList])
        vnfFactorList_ex = np.insert(vnfFactorList, 0, 1.0)
        vnfFactorProd = np.cumprod(vnfFactorList_ex)
        vnfFactorStar = np.cumprod(vnfFactorList[::-1])[::-1]
        vnfMassageLenInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][2]
        vnfMassageLenList = np.array([vnfMassageLenInit]*vnfNodeNum)*vnfFactorList
        vnfArriveRateInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][0]
        vnfBurstBitInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][1]

        self.solution.resource['cpu'] = vnfArriveRateInit*vnfFactorProd[0:-1]
        self.solution.resource['ram'] = np.array([vnfArriveRateInit*vnfMassageLenList[i]/self.solution.resource['cpu'][i]+vnfBurstBitInit 
                                                    for i in range(vnfNodeNum)])*vnfFactorProd[:-1]
        self.solution.resource['band'] = np.array([self.solution.resource['cpu'][i]*vnfFactorList[i] for i in range(vnfNodeNum)])
        self.netcalLatency = vnfFactorProd[-1]*vnfBurstBitInit/(self.solution.resource['cpu']*vnfFactorStar).min() \
                            +(vnfMassageLenList/self.solution.resource['cpu']).sum()

        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = random.sample(range(len(self.substrateTopo.nodes)),1)[0]

        for v_link in self.sfcGraph.edges():
            try:
                map_path = nx.dijkstra_path(self.substrateTopo,
                                            self.solution.map_node[v_link[0]],
                                            self.solution.map_node[v_link[1]])
            except:
                self.solution.current_description = SOLUTION_TYPE.SET_FAILED_FOR_LINK_BAND
                break
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # algorithm end ---------------------------------------------

        if self.solution.current_description == SOLUTION_TYPE.NOTHING:
            self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId]=[self.solution]

        return self.solution
    
    def solve_migration(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfNodeNum = len(self.sfcGraph.nodes)
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        vnfFactorList = np.array([self.vnfManager.vnfPoolDict[vnfId].vnf_factor for vnfId in vnfRequstList])
        vnfFactorList_ex = np.insert(vnfFactorList, 0, 1.0)
        vnfFactorProd = np.cumprod(vnfFactorList_ex)
        vnfFactorStar = np.cumprod(vnfFactorList[::-1])[::-1]
        vnfMassageLenInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][2]
        vnfMassageLenList = np.array([vnfMassageLenInit]*vnfNodeNum)*vnfFactorList
        vnfArriveRateInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][0]
        vnfBurstBitInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][1]

        self.solution.resource['cpu'] = vnfArriveRateInit*vnfFactorProd[0:-1]
        self.solution.resource['ram'] = np.array([vnfArriveRateInit*vnfMassageLenList[i]/self.solution.resource['cpu'][i]+vnfBurstBitInit 
                                                    for i in range(vnfNodeNum)])*vnfFactorProd[:-1]
        self.solution.resource['band'] = np.array([self.solution.resource['cpu'][i]*vnfFactorList[i] for i in range(vnfNodeNum)])
        self.netcalLatency = vnfFactorProd[-1]*vnfBurstBitInit/(self.solution.resource['cpu']*vnfFactorStar).min() \
                            +(vnfMassageLenList/self.solution.resource['cpu']).sum()

        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = random.sample(range(len(self.substrateTopo.nodes)),1)[0]

        for v_link in self.sfcGraph.edges():
            try:
                map_path = nx.dijkstra_path(self.substrateTopo,
                                            self.solution.map_node[v_link[0]],
                                            self.solution.map_node[v_link[1]])
            except:
                self.solution.current_description = SOLUTION_TYPE.CHANGE_FAILED_FOR_LINK_BAND
                break
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # algorithm end ---------------------------------------------

        if self.solution.current_description == SOLUTION_TYPE.NOTHING:
            self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.CHANGE_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId].append(self.solution)

        return self.solution
    
    
    def get_latency_running(self) -> float:
        return super().get_latency_running()+self.netcalLatency


class netcalGreedySolver(GreedySolver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo, **kwargs) -> None:
        super().__init__(substrateTopo, serviceTopo, **kwargs)
    
    def solve_embedding(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfNodeNum = len(self.sfcGraph.nodes)
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        vnfFactorList = np.array([self.vnfManager.vnfPoolDict[vnfId].vnf_factor for vnfId in vnfRequstList])
        vnfFactorList_ex = np.insert(vnfFactorList, 0, 1.0)
        vnfFactorProd = np.cumprod(vnfFactorList_ex)
        vnfFactorStar = np.cumprod(vnfFactorList[::-1])[::-1]
        vnfMassageLenInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][2]
        vnfMassageLenList = np.array([vnfMassageLenInit]*vnfNodeNum)*vnfFactorList
        vnfArriveRateInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][0]
        vnfBurstBitInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][1]

        self.solution.resource['cpu'] = vnfArriveRateInit*vnfFactorProd[0:-1]
        self.solution.resource['ram'] = np.array([vnfArriveRateInit*vnfMassageLenList[i]/self.solution.resource['cpu'][i]+vnfBurstBitInit 
                                                    for i in range(vnfNodeNum)])*vnfFactorProd[:-1]
        self.solution.resource['band'] = np.array([self.solution.resource['cpu'][i]*vnfFactorList[i] for i in range(vnfNodeNum)])
        self.netcalLatency = vnfFactorProd[-1]*vnfBurstBitInit/(self.solution.resource['cpu']*vnfFactorStar).min() \
                            +(vnfMassageLenList/self.solution.resource['cpu']).sum()

        temp_subStrateTopo = copy.deepcopy(self.substrateTopo)

        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                subStrateResource_cpu = temp_subStrateTopo.get_all_nodes_attrs_values('remain_cpu')
                subStrateResource_ram = temp_subStrateTopo.get_all_nodes_attrs_values('remain_ram')
                subStrateResource = (np.array(subStrateResource_cpu)+np.array(subStrateResource_ram)).tolist()
                self.solution.map_node[v_node] = subStrateResource.index(max(subStrateResource))
                temp_subStrateTopo.opt_node_attrs_value(self.solution.map_node[v_node],'remain_cpu','decrease',self.solution.resource['cpu'][v_node])
                temp_subStrateTopo.opt_node_attrs_value(self.solution.map_node[v_node],'remain_ram','decrease',self.solution.resource['ram'][v_node])

        for v_link in self.sfcGraph.edges():
            try:
                map_path = nx.dijkstra_path(self.substrateTopo,
                                            self.solution.map_node[v_link[0]],
                                            self.solution.map_node[v_link[1]])
            except:
                self.solution.current_description = SOLUTION_TYPE.SET_FAILED_FOR_LINK_BAND
                break
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # algorithm end ---------------------------------------------

        if self.solution.current_description == SOLUTION_TYPE.NOTHING:
            self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.SET_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId]=[self.solution]

        return self.solution
    
    def solve_migration(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfNodeNum = len(self.sfcGraph.nodes)
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        vnfFactorList = np.array([self.vnfManager.vnfPoolDict[vnfId].vnf_factor for vnfId in vnfRequstList])
        vnfFactorList_ex = np.insert(vnfFactorList, 0, 1.0)
        vnfFactorProd = np.cumprod(vnfFactorList_ex)
        vnfFactorStar = np.cumprod(vnfFactorList[::-1])[::-1]
        vnfMassageLenInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][2]
        vnfMassageLenList = np.array([vnfMassageLenInit]*vnfNodeNum)*vnfFactorList
        vnfArriveRateInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][0]
        vnfBurstBitInit = event.serviceTopo.plan_arriveFunParam[event.serviceTopoId][1]

        self.solution.resource['cpu'] = vnfArriveRateInit*vnfFactorProd[0:-1]
        self.solution.resource['ram'] = np.array([vnfArriveRateInit*vnfMassageLenList[i]/self.solution.resource['cpu'][i]+vnfBurstBitInit 
                                                    for i in range(vnfNodeNum)])*vnfFactorProd[:-1]
        self.solution.resource['band'] = np.array([self.solution.resource['cpu'][i]*vnfFactorList[i] for i in range(vnfNodeNum)])
        self.netcalLatency = vnfFactorProd[-1]*vnfBurstBitInit/(self.solution.resource['cpu']*vnfFactorStar).min() \
                            +(vnfMassageLenList/self.solution.resource['cpu']).sum()

        temp_subStrateTopo = copy.deepcopy(self.substrateTopo)

        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                subStrateResource_cpu = temp_subStrateTopo.get_all_nodes_attrs_values('remain_cpu')
                subStrateResource_ram = temp_subStrateTopo.get_all_nodes_attrs_values('remain_ram')
                subStrateResource = (np.array(subStrateResource_cpu)+np.array(subStrateResource_ram)).tolist()
                self.solution.map_node[v_node] = subStrateResource.index(max(subStrateResource))
                temp_subStrateTopo.opt_node_attrs_value(self.solution.map_node[v_node],'remain_cpu','decrease',self.solution.resource['cpu'][v_node])
                temp_subStrateTopo.opt_node_attrs_value(self.solution.map_node[v_node],'remain_ram','decrease',self.solution.resource['ram'][v_node])

        for v_link in self.sfcGraph.edges():
            try:
                map_path = nx.dijkstra_path(self.substrateTopo,
                                            self.solution.map_node[v_link[0]],
                                            self.solution.map_node[v_link[1]])
            except:
                self.solution.current_description = SOLUTION_TYPE.CHANGE_FAILED_FOR_LINK_BAND
                break
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # algorithm end ---------------------------------------------

        if self.solution.current_description == SOLUTION_TYPE.NOTHING:
            self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.CHANGE_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId].append(self.solution)

        return self.solution

    def get_latency_running(self) -> float:
        return super().get_latency_running()+self.netcalLatency
