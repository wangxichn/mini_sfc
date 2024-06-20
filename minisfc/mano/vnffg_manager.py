#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   vnffg_manager.py
@Time    :   2024/06/18 20:30:20
@Author  :   Wang Xi
@Version :   0.0
@Contact :   wangxi_chn@foxmail.com
@License :   (C)Copyright 2023-2024, Wang Xi
@Desc    :   None
'''

from typing import Tuple
import copy
from minisfc.mano import NfvManager
from minisfc.topo import SubstrateTopo, ServiceTopo, Topo
from minisfc.solver import Solver, Solution
from minisfc.event import Event, EventType

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
            self.__action_embedding(solution)
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




