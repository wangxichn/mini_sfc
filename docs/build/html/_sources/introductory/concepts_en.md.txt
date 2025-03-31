[中文](./concepts_zh.md) | [English](./concepts_en.md)

# Concepts

## Core Architectural Concepts

### Service Function Chaining (SFC)
Technology that orchestrates multiple Virtual Network Functions (VNFs) into ordered processing chains according to business requirements. Key characteristics:
- **Service Abstraction**: Decouples network functions into independent modules
- **Dynamic Orchestration**: Supports runtime chain restructuring
- **Traffic Steering**: Implements service flow path forwarding via SDN controllers

Reference materials:
- [SFC Tutorial](https://www.yuque.com/wangxi_chn/iku3gm/wx39lox90a9xa80m#)

### Network Functions Virtualization (NFV)
Software-based implementation of traditional hardware network functions. Key features:
- **Elastic Scaling**: Dynamically scales instances based on load
- **Independent Lifecycle**: Individual VNFs can be started/stopped/upgraded separately
- **Service Examples**: Firewall, NAT, Load Balancer, IDS, etc.

Reference materials:
- [SFC Technical Fundamentals](https://www.yuque.com/wangxi_chn/iku3gm/fsac3vx8e6r1t2ed#)

### Software-Defined Networking (SDN)
Key enabling technology for SFC implementation. Core features:
- **Control Plane and Data Plane Separation**
- **Centralized Network View**
- **Programmable Traffic Scheduling** (via protocols like OpenFlow)

Reference materials:
- [SDN Basic Concepts](https://www.yuque.com/wangxi_chn/iku3gm/abfw3a#)
- [SFC Technical Fundamentals](https://www.yuque.com/wangxi_chn/iku3gm/fsac3vx8e6r1t2ed#)

### Typical SFC Application Scenarios
1. **Edge Computing**: UE → Firewall → Video Optimizer → Base Station
2. **Cloud Security**: Traffic → IPS → WAF → Audit System
3. **5G Core Network**: UPF → SMF → AMF Chained Processing

## MANO Architecture
ETSI-proposed NFV Management and Orchestration framework comprising three core components:
- **NFV Orchestrator (NFVO)**: Responsible for global resource orchestration
- **VNF Manager (VNFM)**: Manages VNF lifecycle
- **Virtualized Infrastructure Manager (VIM)**: Manages compute/storage/network resources

Reference materials:
- [NFV MANO Architecture](https://www.yuque.com/wangxi_chn/iku3gm/vv92zv8l5u2iwns4#)

## Simulation Technology Dimensions

### Discrete Event Simulation
- Event queue-based time advancement mechanism
- Ignores physical time consumption, focuses on logical correctness
- Suitable for theoretical validation of large-scale topologies
- Typical tools: Pure Python implementations or Matlab simulations

### Container-based Real-time Simulation
- Uses container technologies (e.g., Docker) to build instances
- Supports real protocol stacks (TCP/IP, etc.)
- Enables actual traffic injection testing
- Typical tools: Containernet

> Note: The Mini-SFC framework supports both research paradigms - theoretical study (discrete event simulation) and practical validation (container simulation)