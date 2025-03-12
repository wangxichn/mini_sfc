
from minisfc.event import Event
from minisfc.topo import ServiceTopo, SubstrateTopo, Topo
from minisfc.solver import RadomSolver, Solution, SOLUTION_TYPE
import numpy as np
import networkx as nx
from sko.PSO import PSO
import code

class PsoSolver(RadomSolver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo) -> None:
        super().__init__(substrateTopo, serviceTopo)

    def solve_embedding(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.vnfManager.vnfPoolDict[vnfId]['cpu'] for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.vnfManager.vnfPoolDict[vnfId]['ram'] for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.vnfManager.vnfServicePoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        pso = PSO(
    	    func=self.fitness, 
    	    dim=len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes),
            pop=100, 
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
    
    def solve_migration(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.vnfManager.vnfPoolDict[vnfId]['cpu'] for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.vnfManager.vnfPoolDict[vnfId]['ram'] for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.vnfManager.vnfServicePoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        pso = PSO(
    	    func=self.fitness, 
    	    dim=len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes),
            pop=100, 
    	    max_iter=10, 
    	    lb=[0]*(len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes)), 
    	    ub=[1]*(len(self.sfcGraph.nodes)*len(self.substrateTopo.nodes)), 
    	    w=0.8,
    	    c1=0.5, 
    	    c2=0.5)
        pso.run()

        x = np.array(pso.gbest_x)
        x = x.reshape((len(self.sfcGraph.nodes),len(self.substrateTopo.nodes)))
        for v_node in len(self.sfcGraph.nodes):
            if v_node == 0:
                self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = np.where(x[v_node,:]==np.max(x[v_node,:]))[0][0]
        
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
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]

        if self.check_constraints(self.event) not in (SOLUTION_TYPE.SET_SUCCESS,SOLUTION_TYPE.CHANGE_SUCCESS,
                                                      SOLUTION_TYPE.SET_FAILED_FOR_LATENCY,SOLUTION_TYPE.CHANGE_FAILED_FOR_LATENCY):
            return float("inf")
        else:
            return self.get_latency_running() -self.event.serviceTopo.plan_qosRequesDict[self.event.serviceTopoId][0]



