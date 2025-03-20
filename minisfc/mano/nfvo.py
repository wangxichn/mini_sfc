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

from minisfc.mano.vnfm import VnfManager
from minisfc.mano.uem import UeManager, Ue
from minisfc.mano.vim import NfvVim, VnfEm

from minisfc.topo import SubstrateTopo, Topo
from minisfc.solver import Solver, Solution
from minisfc.event import Event, EventType
from minisfc.trace import TRACE_RESULT, TRACE_NFVI

import copy

class NfvOrchestrator:
    def __init__(self,vnfManager:VnfManager,nfvVim:NfvVim,sfcSolver:Solver,ueManager:UeManager=None):
        self.vnfManager = vnfManager
        self.ueManager = ueManager
        self.nfvVim = nfvVim
        self.sfcSolver = sfcSolver
    
    def ready(self):
        """
        Initialize the NFV Orchestrator, mainly ready for SFC solver.
        """
        self.vnffg_group:list[VnffgManager] = []
        self.sfcSolver.initialize(self.vnfManager)

        TRACE_RESULT.ready(['Event', 'Time', 'SfcId', 'Result', 'Resource', 'Vnffgs', 'Solution','Reason'])
        contextDict = {'Event':'I','Time':0.00,
                       'Resource':self.nfvVim.substrateTopo.get_sum_resource_list('remain')}
        TRACE_RESULT.write(contextDict)


        TRACE_NFVI.ready(['Event', 'Time']+[element for nfvi in self.nfvVim.nfv_instance_group.values() 
                                                    for element in [nfvi.name+"_cpu", nfvi.name+"_ram", nfvi.name+"_vnfs"]])
        contextDict = {'Event':'I','Time':0.00}
        contextDict.update({
                            key: value for nfvi in self.nfvVim.nfv_instance_group.values() 
                            for key, value in [
                                (nfvi.name + "_cpu", nfvi.cpu_remain),
                                (nfvi.name + "_ram", nfvi.ram_remain),
                                (nfvi.name + "_vnfs", nfvi.get_deployed_vnfs())]
                            })
        TRACE_NFVI.write(contextDict)


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
        vnffg_manager = VnffgManager(self.sfcSolver,self.nfvVim,self.vnfManager,self.ueManager)
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
        if solutions[-1].current_result == True:
            contextDict['Solution'] = solutions[-1].map_node.values()
        else:
            contextDict['Reason'] = solutions[-1].current_description
            
        TRACE_RESULT.write(contextDict)

        contextDict = {'Event':'+','Time':event.time}
        contextDict.update({
                            key: value for nfvi in self.nfvVim.nfv_instance_group.values() 
                            for key, value in [
                                (nfvi.name + "_cpu", nfvi.cpu_remain),
                                (nfvi.name + "_ram", nfvi.ram_remain),
                                (nfvi.name + "_vnfs", nfvi.get_deployed_vnfs())]
                            })
        TRACE_NFVI.write(contextDict)
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
        TRACE_RESULT.write(contextDict)

        contextDict = {'Event':'-','Time':event.time}
        contextDict.update({
                            key: value for nfvi in self.nfvVim.nfv_instance_group.values() 
                            for key, value in [
                                (nfvi.name + "_cpu", nfvi.cpu_remain),
                                (nfvi.name + "_ram", nfvi.ram_remain),
                                (nfvi.name + "_vnfs", nfvi.get_deployed_vnfs())]
                            })
        TRACE_NFVI.write(contextDict)
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
                    if solutions[-1].current_result == True:
                        contextDict['Solution'] = solutions[-1].map_node.values()
                    else:
                        contextDict['Reason'] = solutions[-1].current_description
                    TRACE_RESULT.write(contextDict)

                    contextDict = {'Event':'t','Time':event.time}
                    contextDict.update({
                            key: value for nfvi in self.nfvVim.nfv_instance_group.values() 
                            for key, value in [
                                (nfvi.name + "_cpu", nfvi.cpu_remain),
                                (nfvi.name + "_ram", nfvi.ram_remain),
                                (nfvi.name + "_vnfs", nfvi.get_deployed_vnfs())]
                            })
                    TRACE_NFVI.write(contextDict)
                    # Print Trance End ---------------------------------------------------------------
                    
                    # After processing this SFC migration, need to update the current substrate network state in the event 
                    event.substrateTopo = self.substrateTopo
                    break # check next vnffg_manager

        return self.substrateTopo
        

class VnffgManager:
    def __init__(self, solver:Solver, nfvVim:NfvVim, vnfManager:VnfManager, ueManager:UeManager=None) -> None:
        self.solver = solver
        self.recordSolutions:list[Solution] = []
        self.nfvVim = nfvVim
        self.vnfManager = vnfManager
        self.ueManager = ueManager

    
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
            self.nfvVim.update_substrate_topo(self.substrateTopo)
            self.__action_embedding(solution)
            self.substrateTopo = self.nfvVim.get_curent_substrate_topo()
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

        self.nfvVim.update_substrate_topo(self.substrateTopo)
        self.__action_release(solution)
        self.substrateTopo = self.nfvVim.get_curent_substrate_topo()

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
            self.nfvVim.update_substrate_topo(self.substrateTopo)
            self.__action_release(self.recordSolutions[-1]) # use last one solution release resource
            self.__action_embedding(solution)
            self.substrateTopo = self.nfvVim.get_curent_substrate_topo()
        else:
            # Migration failed
            self.nfvVim.update_substrate_topo(self.substrateTopo)
            self.__action_release(self.recordSolutions[-1])
            self.substrateTopo = self.nfvVim.get_curent_substrate_topo()

        # Save the solution
        self.recordSolutions.append(copy.deepcopy(solution))

        return self.substrateTopo,self.recordSolutions


    def __action_embedding(self, solution:Solution):
        req_vnfs_id_list:list[int] = self.event.serviceTopo.plan_vnfRequstDict[self.event.serviceTopoId]
        req_vnfs:list[VnfEm] = [self.vnfManager.get_vnf_from_pool(vnf_id) for vnf_id in req_vnfs_id_list]

        for sfc_node, phy_node in solution.map_node.items():
            req_vnfs[sfc_node].vnf_name = f"f{self.event.serviceTopoId}v{sfc_node}"
            req_vnfs[sfc_node].vnf_cpu = solution.resource['cpu'][sfc_node]
            req_vnfs[sfc_node].vnf_ram = solution.resource['ram'][sfc_node]
            req_vnfs[sfc_node].vnf_rom = 0 # no rom requirement in this demo
            self.nfvVim.deploy_VNF_on_NFVI(req_vnfs[sfc_node], phy_node)

        for i,[sfc_link, phy_links] in enumerate(solution.map_link.items()):
            for phy_link in phy_links:
                self.nfvVim.deploy_service(phy_link[0],phy_link[1],solution.resource['band'][i])

        if self.nfvVim.containernet_handle != None and self.ueManager != None:
            req_ues_pos:list[int] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId]
            req_ues:list[Ue] = [self.ueManager.get_ue_from_pool(ue_id) for ue_id in [0,1]]
            for i,(ue,ue_pos) in enumerate(zip(req_ues,req_ues_pos)):
                ue.ue_name = f"f{self.event.serviceTopoId}u{i}"
                if i == 0: ue.ue_aim = req_vnfs[0]
                self.nfvVim.access_ue_on_NFVI(ue,ue_pos)

            self.vnfManager.set_vnfs_forward_route(req_vnfs,req_ues)
            req_ues[0].start_trasport(self.ueManager.ueServicePoolDict[req_ues[0].ue_id,req_ues[1].ue_id])
            

    def __action_release(self, solution:Solution):
        if self.nfvVim.containernet_handle != None and self.ueManager != None:
            req_ues_pos:list[int] = self.event.serviceTopo.plan_endPointDict[self.event.serviceTopoId]
            for i,ue_pos in enumerate(req_ues_pos):
                ue_name = f"f{self.event.serviceTopoId}u{i}"
                self.nfvVim.unaccess_ue_on_NFVI(ue_name,ue_pos)
    
        for sfc_node, phy_node in solution.map_node.items():
            self.nfvVim.undeploy_VNF_on_NFVI(f"f{self.event.serviceTopoId}v{sfc_node}", phy_node)

        for i,[sfc_link, phy_links] in enumerate(solution.map_link.items()):
            for phy_link in phy_links:
                try: # the link may have been break
                    self.nfvVim.undeploy_service(phy_link[0],phy_link[1],solution.resource['band'][i])
                except:
                    continue
            