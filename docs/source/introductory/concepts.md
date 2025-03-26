# 相关概念

## 核心架构概念

### 服务功能链 (Service Function Chaining, SFC)
将多个虚拟网络功能(VNF)按业务需求编排成有序处理链的技术。典型特征包括：
- **服务抽象**：将网络功能解耦为独立模块
- **动态编排**：支持运行时链结构调整
- **流量导向**：通过SDN控制器实现业务流按路径转发

相关参考资料：
- [SFC 教程资料](https://www.yuque.com/wangxi_chn/iku3gm/wx39lox90a9xa80m#)

### 网络功能虚拟化 (NFV)
传统硬件网络功能的软件化实现，关键特性：
- **弹性扩展**：可根据负载动态伸缩实例
- **独立生命周期**：每个VNF可单独启停/升级
- **服务示例**：防火墙、NAT、负载均衡、IDS等

相关参考资料：
- [SFC 技术基础](https://www.yuque.com/wangxi_chn/iku3gm/fsac3vx8e6r1t2ed#)

### 软件定义网络 (SDN)
实现SFC的关键使能技术，核心特征：
- **控制面与数据面分离**
- **集中式网络视图**
- **可编程流量调度**（通过OpenFlow等协议）

相关参考资料：
- [SDN 基本概念](https://www.yuque.com/wangxi_chn/iku3gm/abfw3a#)
- [SFC 技术基础](https://www.yuque.com/wangxi_chn/iku3gm/fsac3vx8e6r1t2ed#)

### 典型SFC应用场景
1. **边缘计算**：UE→防火墙→视频优化→基站
2. **云安全**：流量→IPS→WAF→审计系统
3. **5G核心网**：UPF→SMF→AMF链式处理

## MANO架构
ETSI提出的NFV管理与编排框架，包含三个核心组件：
- **NFV Orchestrator (NFVO)**：负责全局资源编排
- **VNF Manager (VNFM)**：管理虚拟网络功能生命周期
- **Virtualized Infrastructure Manager (VIM)**：管理计算/存储/网络资源

相关参考资料：
- [NFV MANO架构](https://www.yuque.com/wangxi_chn/iku3gm/vv92zv8l5u2iwns4#)

## 仿真技术维度

### 离散事件仿真
- 基于事件队列的时间推进机制
- 忽略物理时间消耗，关注逻辑正确性
- 适合大规模拓扑的理论验证
- 典型工具：纯Python实现或Matlab仿真

### 容器化实时仿真
- 使用Docker等容器技术构建实例
- 真实协议栈支持（TCP/IP等）
- 可注入实际流量测试
- 典型工具：Containernet

## 关键术语对照
| 术语 | 英文全称 | 说明 |
|------|---------|------|
| VNF  | Virtualized Network Function | 虚拟化网络功能 |
| NFV  | Network Functions Virtualization | 网络功能虚拟化 |
| SFC  | Service Function Chaining | 服务功能链 |
| MANO | Management and Orchestration | 管理与编排 |

> 注：MiniSFC框架同时支持理论研究（离散事件仿真）和实践验证（容器仿真）两种研究范式