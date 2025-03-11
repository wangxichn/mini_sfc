#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   nfv_orchestrator.py
@Time    :   2024/06/18 19:57:29
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from typing import Tuple

from minisfc.mano import NfvManager
from minisfc.topo import SubstrateTopo, Topo
from minisfc.solver import Solver, Solution
from minisfc.event import Event, EventType
from minisfc.trace import TRACER

import copy

class NfvOrchestrator:
    def __init__(self,nfvManage:NfvManager,sfcSolver:Solver):
        self.nfvManage = nfvManage
        self.sfcSolver = sfcSolver
    
    def ready(self,substrateTopo:SubstrateTopo):
        self.substrateTopo = substrateTopo
        self.vnffg_group:list[VnffgManager] = []
        self.sfcSolver.initialize(self.nfvManage)

        contextDict = {'Event':'I','Time':0.00,
                       'Resource':self.substrateTopo.get_sum_resource_list('remain')}
        TRACER.write(contextDict)

    def handle(self,event:Event) -> SubstrateTopo:
        if event.type == EventType.SFC_ARRIVE:
            return self.__handle_arrive(event)
        elif event.type == EventType.SFC_ENDING:
            return self.__handle_ending(event)
        elif event.type == EventType.TOPO_CHANGE:
            return self.__handle_topochange(event)
    
    def __handle_arrive(self,event:Event) -> SubstrateTopo:
        # Update network state before solve
        self.substrateTopo = event.substrateTopo
        # Create SFC manager
        vnffg_manager = VnffgManager(self.sfcSolver)
        # Update network state after solve
        self.substrateTopo, solutions = vnffg_manager.handle_arrive(event)
        
        if solutions[-1].current_result == True:
            # Embed successfully into management queue 
            self.vnffg_group.append(vnffg_manager)
        else:
            # Embedding failed and did not enter the administrative queue 
            pass

        # Print Trance ------------------------------------------------------------------
        contextDict = {'Event':'+','Time':event.time,'SfcId':event.serviceTopoId,
                       'Result':solutions[-1].current_result,
                       'Resource':self.substrateTopo.get_sum_resource_list('remain'),
                       'Vnffgs':[vnffg.id for vnffg in self.vnffg_group]}
        if solutions[-1].current_result == False:
            contextDict['Reason'] = solutions[-1].current_description
        TRACER.write(contextDict)
        # Print Trance End ------------------------------------------------------------------

        return self.substrateTopo


    def __handle_ending(self,event:Event) -> SubstrateTopo:
        # Update network state before solve
        self.substrateTopo = event.substrateTopo
        solutions = None
        # Find SFC manager related
        vnffg_manager = list(filter(lambda x: x.id == event.serviceTopoId, self.vnffg_group))
        if vnffg_manager != []:
            # SFC ending normally
            vnffg_manager = vnffg_manager[0]
            # Update network state after solve
            self.substrateTopo, solutions = vnffg_manager.handle_ending(event)
            # Remove SFC manager
            # self.vnffg_group = list(filter(lambda x: x.id != event.serviceTopoId, self.vnffg_group))
            self.vnffg_group.remove(vnffg_manager)
        else:
            # SFC has been forcibly ended
            pass

        # Print Trance ------------------------------------------------------------------
        contextDict = {'Event':'-','Time':event.time,'SfcId':event.serviceTopoId,
                       'Resource':self.substrateTopo.get_sum_resource_list('remain'),
                       'Vnffgs':[vnffg.id for vnffg in self.vnffg_group]}
        if solutions == None:
            contextDict['Result'] = False
        else:
            contextDict['Result'] = solutions[-1].current_result
        TRACER.write(contextDict)
        # Print Trance End ------------------------------------------------------------------

        return self.substrateTopo

    def __handle_topochange(self,event:Event) -> SubstrateTopo:
        # update network state
        self.substrateTopo = event.substrateTopo
        # find the vnffg_manager will be affected to do
        for vnffg_manager in self.vnffg_group[:]:
            # Combine all the mapped physical links in the solution into a list using the sum function
            # And then use set to deduplicate, because we don't care about the order of these links
            all_used_phy_edge = list(set(sum(vnffg_manager.recordSolutions[-1].map_link.values(),[])))
            current_phy_net_adjacency = self.substrateTopo.get_adjacency_matrix()
            for edge in all_used_phy_edge:
                if current_phy_net_adjacency[edge[0],edge[1]] == 0:
                    # Topological changes affect this SFC and require migration
                    # The event is originally a topology change type and does not contain SFC information. It needs to be supplemented here. 
                    event.serviceTopoId = vnffg_manager.id
                    self.substrateTopo, solutions = vnffg_manager.handle_topochange(event)

                    if solutions[-1].current_result == True:
                        # Migrate successfully
                        pass
                    else:
                        # Migrate failed and delete it 
                        self.vnffg_group.remove(vnffg_manager)

                    # Print Trance ------------------------------------------------------------------
                    contextDict = {'Event':'t','Time':event.time,'SfcId':event.serviceTopoId,
                                   'Result':solutions[-1].current_result,
                                   'Resource':self.substrateTopo.get_sum_resource_list('remain'),
                                   'Vnffgs':[vnffg.id for vnffg in self.vnffg_group]}
                    if solutions[-1].current_result == False:
                        contextDict['Reason'] = solutions[-1].current_description
                    TRACER.write(contextDict)
                    # Print Trance End ---------------------------------------------------------------
                    
                    # After processing this SFC migration, need to update the current substrate network state in the event 
                    event.substrateTopo = self.substrateTopo
                    break # check next vnffg_manager

        return self.substrateTopo
        

class VnffgManager:
    def __init__(self, solver:Solver) -> None:
        self.solver = solver
        self.recordSolutions:list[Solution] = []

    
    def handle_arrive(self, event:Event) -> Tuple[SubstrateTopo,list[Solution]]:
        self.id = event.serviceTopoId
        # Update event
        self.event = event
        # Update substrate network
        self.substrateTopo = event.substrateTopo

        # Obtain a solution and apply it
        solution:Solution = self.solver.solve_embedding(event)

        if solution.current_result == True:
            # Embedding successful
            self.__action_embedding(solution)
        else:
            # Embedding failed
            pass

        # Save the solution
        self.recordSolutions.append(copy.deepcopy(solution))

        return self.substrateTopo,self.recordSolutions


    def handle_ending(self, event:Event) -> Tuple[SubstrateTopo,list[Solution]]:
        # Update event
        self.event = event
        # Update substrate network
        self.substrateTopo = event.substrateTopo

        # Obtain a solution and apply it
        solution:Solution = self.solver.solve_ending(event)
        self.__action_release(solution)
        # Save the solution
        self.recordSolutions.append(copy.deepcopy(solution))

        return self.substrateTopo,self.recordSolutions


    def handle_topochange(self, event:Event) -> Tuple[SubstrateTopo,list[Solution]]:
        # Update event
        self.event = event
        # Update substrate network
        self.substrateTopo = event.substrateTopo
        # Obtain a solution and apply it
        solution:Solution = self.solver.solve_migration(event)

        if solution.current_result == True:
            # Migration successful
            self.__action_release(self.recordSolutions[-1]) # use last one solution release resource
            try: ##########################################################################################################################  watch
                self.__action_embedding(solution)
            except:
                import code
                code.interact(banner="",local=locals())
        else:
            # Migration failed
            self.__action_release(self.recordSolutions[-1])

        # Save the solution
        self.recordSolutions.append(copy.deepcopy(solution))

        return self.substrateTopo,self.recordSolutions


    def __action_embedding(self, solution:Solution):
        requestSfcGraph:Topo = self.event.serviceTopo.plan_sfcGraph[self.event.serviceTopoId]

        for sfc_node in requestSfcGraph.nodes:
            requestSfcGraph.opt_node_attrs_value(sfc_node,'request_cpu','set',solution.resource['cpu'][sfc_node])
            requestSfcGraph.opt_node_attrs_value(sfc_node,'request_ram','set',solution.resource['ram'][sfc_node])
        for i,sfc_link in enumerate(requestSfcGraph.edges):
            requestSfcGraph.opt_link_attrs_value(sfc_link,'request_band','set',solution.resource['band'][i])

        # first embed nodes
        for sfc_node, phy_node in solution.map_node.items():
            # CPU
            request_cpu_of_node = requestSfcGraph.opt_node_attrs_value(sfc_node,'request_cpu','get')
            self.substrateTopo.opt_node_attrs_value(phy_node,'remain_cpu','decrease',request_cpu_of_node)
            
            # RAM
            request_ram_of_node = requestSfcGraph.opt_node_attrs_value(sfc_node,'request_ram','get')
            self.substrateTopo.opt_node_attrs_value(phy_node,'remain_ram','decrease',request_ram_of_node)

        # second embed links
        for sfc_link, phy_links in solution.map_link.items():
            request_band_of_link = requestSfcGraph.opt_link_attrs_value(sfc_link,'request_band','get')
            for phy_link in phy_links:
                self.substrateTopo.opt_link_attrs_value(phy_link,'remain_band','decrease',request_band_of_link)
        
    def __action_release(self, solution:Solution):
        requestSfcGraph:Topo = self.event.serviceTopo.plan_sfcGraph[self.event.serviceTopoId]

        for sfc_node in requestSfcGraph.nodes:
            requestSfcGraph.opt_node_attrs_value(sfc_node,'request_cpu','set',solution.resource['cpu'][sfc_node])
            requestSfcGraph.opt_node_attrs_value(sfc_node,'request_ram','set',solution.resource['ram'][sfc_node])
        for i,sfc_link in enumerate(requestSfcGraph.edges):
            requestSfcGraph.opt_link_attrs_value(sfc_link,'request_band','set',solution.resource['band'][i])

        # first release nodes
        for sfc_node, phy_node in solution.map_node.items():
            # CPU
            request_cpu_of_node = requestSfcGraph.opt_node_attrs_value(sfc_node,'request_cpu','get')
            self.substrateTopo.opt_node_attrs_value(phy_node,'remain_cpu','increase',request_cpu_of_node)

            # RAM
            request_ram_of_node = requestSfcGraph.opt_node_attrs_value(sfc_node,'request_ram','get')
            self.substrateTopo.opt_node_attrs_value(phy_node,'remain_ram','increase',request_ram_of_node)

        # second release links
        for sfc_link, phy_links in solution.map_link.items():
            request_band_of_link = requestSfcGraph.opt_link_attrs_value(sfc_link,'request_band','get')
            for phy_link in phy_links:
                try: # the link may have been break
                    self.substrateTopo.opt_link_attrs_value(phy_link,'remain_band','increase',request_band_of_link)
                except:
                    continue
            