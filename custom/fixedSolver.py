import sys
sys.path.append("..//")
from minisfc.event import Event
from minisfc.topo import ServiceTopo, SubstrateTopo, Topo
from minisfc.solver import RadomSolver, Solution, SOLUTION_TYPE
import networkx as nx
import random

class FixedSolver(RadomSolver):
    def __init__(self, substrateTopo: SubstrateTopo, serviceTopo: ServiceTopo) -> None:
        super().__init__(substrateTopo, serviceTopo)

    def solve_embedding(self, event: Event) -> Solution:
        self.event = event
        self.solution = Solution()
        
        self.sfcGraph: Topo = event.serviceTopo.plan_sfcGraph[event.serviceTopoId]
        self.substrateTopo = event.substrateTopo

        # algorithm begin ---------------------------------------------
        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = random.sample(range(len(self.substrateTopo.nodes)),1)[0]

        for v_link in self.sfcGraph.edges():
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        
        # If the fixed VNF resource allocation in the original SFC problem is used:
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.nfvManager.vnfPoolDict[vnfId]['cpu'] for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.nfvManager.vnfPoolDict[vnfId]['ram'] for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.nfvManager.vnfPoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        # If the dynamic resource allocation of each VNF is implemented in the solver algorithm:
        # self.solution.resource['cpu'] = 
        # self.solution.resource['ram'] = 
        # self.solution.resource['band'] = 
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
        for v_node in self.sfcGraph.nodes:
            if v_node == 0:
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][0]
            elif v_node == (len(self.sfcGraph.nodes)-1):
                self.solution.map_node[v_node] = event.serviceTopo.plan_endPointDict[event.serviceTopoId][1]
            else:
                self.solution.map_node[v_node] = random.sample(range(len(self.substrateTopo.nodes)),1)[0]

        for v_link in self.sfcGraph.edges():
            map_path = nx.dijkstra_path(self.substrateTopo,
                                        self.solution.map_node[v_link[0]],
                                        self.solution.map_node[v_link[1]])
            
            if len(map_path) == 1: 
                self.solution.map_link[v_link] = [(map_path[0],map_path[0])]
            else:
                self.solution.map_link[v_link] = [(map_path[i],map_path[i+1]) for i in range(len(map_path)-1)]
        

        # If the fixed VNF resource allocation in the original SFC problem is used:
        vnfRequstList = event.serviceTopo.plan_vnfRequstDict[event.serviceTopoId]
        self.solution.resource['cpu'] = [self.nfvManager.vnfPoolDict[vnfId]['cpu'] for vnfId in vnfRequstList]
        self.solution.resource['ram'] = [self.nfvManager.vnfPoolDict[vnfId]['ram'] for vnfId in vnfRequstList]
        self.solution.resource['band'] = [self.nfvManager.vnfPoolDict[vnfRequstList[i],vnfRequstList[i+1]]['band'] 
                                          for i in range(len(vnfRequstList)-1)]

        # If the dynamic resource allocation of each VNF is implemented in the solver algorithm:
        # self.solution.resource['cpu'] = 
        # self.solution.resource['ram'] = 
        # self.solution.resource['band'] = 
        # algorithm end ---------------------------------------------

        self.solution.current_description = self.check_constraints(event)

        if self.solution.current_description != SOLUTION_TYPE.CHANGE_SUCCESS:
            self.solution.current_result = False
        else:
            self.solution.current_result = True
        
        self.record_solutions[self.event.serviceTopoId].append(self.solution)

        return self.solution
    
    




