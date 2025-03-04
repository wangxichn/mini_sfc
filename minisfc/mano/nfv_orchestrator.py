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

import sys
#添加上级目录
sys.path.append("..//..//")
from minisfc.mano import NfvManager, VnffgManager
from minisfc.topo import SubstrateTopo, ServiceTopo
from minisfc.solver import Solver
from minisfc.event import Event, EventType
from minisfc.trace import TRACER

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
        
