#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XrayR配置管理工具

提供XrayR配置文件的解析、简化、序列化等功能
"""

import yaml
import json
from typing import Dict, Any, Optional
from datetime import datetime


class XrayRConfigParser:
    """XrayR配置解析器"""
    
    @staticmethod
    def parse_yaml_config(yaml_content: str) -> Dict[str, Any]:
        """
        解析YAML配置文件
        
        Args:
            yaml_content: YAML配置文件内容
            
        Returns:
            解析后的配置字典
        """
        try:
            config = yaml.safe_load(yaml_content)
            return config if config else {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析失败: {e}")
    
    @staticmethod
    def simplify_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        简化XrayR配置，提取关键信息
        
        Args:
            config: 完整的配置字典
            
        Returns:
            简化后的配置字典
        """
        simplified = {
            "log": {},
            "core": {},
            "nodes": [],
            "api": {},
            "cert": {}
        }
        
        # 提取日志配置
        if "Log" in config:
            log_config = config["Log"]
            simplified["log"] = {
                "level": log_config.get("Level", "warning"),
                "access_path": log_config.get("AccessPath", ""),
                "error_path": log_config.get("ErrorPath", "")
            }
        
        # 提取核心配置
        if "DnsConfigPath" in config:
            simplified["core"]["dns_config_path"] = config["DnsConfigPath"]
        if "RouteConfigPath" in config:
            simplified["core"]["route_config_path"] = config["RouteConfigPath"]
        if "InboundConfigPath" in config:
            simplified["core"]["inbound_config_path"] = config["InboundConfigPath"]
        if "OutboundConfigPath" in config:
            simplified["core"]["outbound_config_path"] = config["OutboundConfigPath"]
        if "ConnectionConfig" in config:
            simplified["core"]["connection_config"] = config["ConnectionConfig"]
        
        # 提取节点配置
        if "Nodes" in config and isinstance(config["Nodes"], list):
            for node in config["Nodes"]:
                simplified_node = {
                    "panel_type": node.get("PanelType", ""),
                    "api_config": {
                        "api_host": node.get("ApiConfig", {}).get("ApiHost", ""),
                        "api_key": node.get("ApiConfig", {}).get("ApiKey", ""),
                        "node_id": node.get("ApiConfig", {}).get("NodeID", 0),
                        "node_type": node.get("ApiConfig", {}).get("NodeType", ""),
                        "timeout": node.get("ApiConfig", {}).get("Timeout", 30),
                        "enable_vless": node.get("ApiConfig", {}).get("EnableVless", False),
                        "enable_xtls": node.get("ApiConfig", {}).get("EnableXTLS", False)
                    },
                    "controller_config": {
                        "listen_ip": node.get("ControllerConfig", {}).get("ListenIP", "0.0.0.0"),
                        "send_ip": node.get("ControllerConfig", {}).get("SendIP", "0.0.0.0"),
                        "update_period": node.get("ControllerConfig", {}).get("UpdatePeriod", 60),
                        "enable_dns": node.get("ControllerConfig", {}).get("EnableDNS", False),
                        "dns_type": node.get("ControllerConfig", {}).get("DNSType", ""),
                        "enable_proxy_protocol": node.get("ControllerConfig", {}).get("EnableProxyProtocol", False),
                        "auto_speed_limit": node.get("ControllerConfig", {}).get("AutoSpeedLimit", 0),
                        "speed_limit": node.get("ControllerConfig", {}).get("SpeedLimit", 0),
                        "device_limit": node.get("ControllerConfig", {}).get("DeviceLimit", 0),
                        "local_rule_list": node.get("ControllerConfig", {}).get("LocalRuleList", [])
                    },
                    "cert_config": {
                        "cert_mode": node.get("CertConfig", {}).get("CertMode", ""),
                        "cert_domain": node.get("CertConfig", {}).get("CertDomain", ""),
                        "cert_file": node.get("CertConfig", {}).get("CertFile", ""),
                        "key_file": node.get("CertConfig", {}).get("KeyFile", ""),
                        "provider": node.get("CertConfig", {}).get("Provider", ""),
                        "email": node.get("CertConfig", {}).get("Email", ""),
                        "dns_env": node.get("CertConfig", {}).get("DNSEnv", {})
                    }
                }
                simplified["nodes"].append(simplified_node)
        
        return simplified
    
    @staticmethod
    def config_to_yaml(config: Dict[str, Any]) -> str:
        """
        将配置字典转换为YAML格式
        
        Args:
            config: 配置字典
            
        Returns:
            YAML格式的配置字符串
        """
        try:
            return yaml.dump(config, default_flow_style=False, allow_unicode=True, indent=2)
        except Exception as e:
            raise ValueError(f"YAML序列化失败: {e}")
    
    @staticmethod
    def expand_simplified_config(simplified_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        将简化的配置扩展为完整的XrayR配置格式
        
        Args:
            simplified_config: 简化的配置字典
            
        Returns:
            完整的XrayR配置字典
        """
        expanded = {}
        
        # 扩展日志配置
        if "log" in simplified_config:
            log_config = simplified_config["log"]
            expanded["Log"] = {
                "Level": log_config.get("level", "warning"),
                "AccessPath": log_config.get("access_path", ""),
                "ErrorPath": log_config.get("error_path", "")
            }
        
        # 扩展核心配置
        if "core" in simplified_config:
            core_config = simplified_config["core"]
            if "dns_config_path" in core_config:
                expanded["DnsConfigPath"] = core_config["dns_config_path"]
            if "route_config_path" in core_config:
                expanded["RouteConfigPath"] = core_config["route_config_path"]
            if "inbound_config_path" in core_config:
                expanded["InboundConfigPath"] = core_config["inbound_config_path"]
            if "outbound_config_path" in core_config:
                expanded["OutboundConfigPath"] = core_config["outbound_config_path"]
            if "connection_config" in core_config:
                expanded["ConnectionConfig"] = core_config["connection_config"]
        
        # 扩展节点配置
        if "nodes" in simplified_config and isinstance(simplified_config["nodes"], list):
            expanded["Nodes"] = []
            for simplified_node in simplified_config["nodes"]:
                expanded_node = {
                    "PanelType": simplified_node.get("panel_type", ""),
                    "ApiConfig": {
                        "ApiHost": simplified_node.get("api_config", {}).get("api_host", ""),
                        "ApiKey": simplified_node.get("api_config", {}).get("api_key", ""),
                        "NodeID": simplified_node.get("api_config", {}).get("node_id", 0),
                        "NodeType": simplified_node.get("api_config", {}).get("node_type", ""),
                        "Timeout": simplified_node.get("api_config", {}).get("timeout", 30),
                        "EnableVless": simplified_node.get("api_config", {}).get("enable_vless", False),
                        "EnableXTLS": simplified_node.get("api_config", {}).get("enable_xtls", False)
                    },
                    "ControllerConfig": {
                        "ListenIP": simplified_node.get("controller_config", {}).get("listen_ip", "0.0.0.0"),
                        "SendIP": simplified_node.get("controller_config", {}).get("send_ip", "0.0.0.0"),
                        "UpdatePeriod": simplified_node.get("controller_config", {}).get("update_period", 60),
                        "EnableDNS": simplified_node.get("controller_config", {}).get("enable_dns", False),
                        "DNSType": simplified_node.get("controller_config", {}).get("dns_type", ""),
                        "EnableProxyProtocol": simplified_node.get("controller_config", {}).get("enable_proxy_protocol", False),
                        "AutoSpeedLimit": simplified_node.get("controller_config", {}).get("auto_speed_limit", 0),
                        "SpeedLimit": simplified_node.get("controller_config", {}).get("speed_limit", 0),
                        "DeviceLimit": simplified_node.get("controller_config", {}).get("device_limit", 0),
                        "LocalRuleList": simplified_node.get("controller_config", {}).get("local_rule_list", [])
                    },
                    "CertConfig": {
                        "CertMode": simplified_node.get("cert_config", {}).get("cert_mode", ""),
                        "CertDomain": simplified_node.get("cert_config", {}).get("cert_domain", ""),
                        "CertFile": simplified_node.get("cert_config", {}).get("cert_file", ""),
                        "KeyFile": simplified_node.get("cert_config", {}).get("key_file", ""),
                        "Provider": simplified_node.get("cert_config", {}).get("provider", ""),
                        "Email": simplified_node.get("cert_config", {}).get("email", ""),
                        "DNSEnv": simplified_node.get("cert_config", {}).get("dns_env", {})
                    }
                }
                expanded["Nodes"].append(expanded_node)
        
        return expanded
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证XrayR配置的有效性
        
        Args:
            config: 配置字典
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 检查必要的节点配置
            if "nodes" not in config or not isinstance(config["nodes"], list):
                return False, "缺少节点配置"
            
            if len(config["nodes"]) == 0:
                return False, "至少需要一个节点配置"
            
            for i, node in enumerate(config["nodes"]):
                # 检查API配置
                api_config = node.get("api_config", {})
                if not api_config.get("api_host"):
                    return False, f"节点{i+1}: 缺少API主机地址"
                if not api_config.get("api_key"):
                    return False, f"节点{i+1}: 缺少API密钥"
                if not isinstance(api_config.get("node_id"), int) or api_config.get("node_id") <= 0:
                    return False, f"节点{i+1}: 节点ID必须是正整数"
                if not api_config.get("node_type"):
                    return False, f"节点{i+1}: 缺少节点类型"
            
            return True, "配置验证通过"
            
        except Exception as e:
            return False, f"配置验证异常: {e}"


def create_default_xrayr_config() -> Dict[str, Any]:
    """
    创建默认的XrayR配置
    
    Returns:
        默认配置字典
    """
    return {
        "log": {
            "level": "warning",
            "access_path": "",
            "error_path": ""
        },
        "core": {
            "dns_config_path": "",
            "route_config_path": "",
            "inbound_config_path": "",
            "outbound_config_path": "",
            "connection_config": {
                "Handshake": 4,
                "ConnIdle": 30,
                "UplinkOnly": 2,
                "DownlinkOnly": 4,
                "BufferSize": 64
            }
        },
        "nodes": [
            {
                "panel_type": "SSpanel",
                "api_config": {
                    "api_host": "http://127.0.0.1:667",
                    "api_key": "123",
                    "node_id": 1,
                    "node_type": "V2ray",
                    "timeout": 30,
                    "enable_vless": False,
                    "enable_xtls": False
                },
                "controller_config": {
                    "listen_ip": "0.0.0.0",
                    "send_ip": "0.0.0.0",
                    "update_period": 60,
                    "enable_dns": False,
                    "dns_type": "",
                    "enable_proxy_protocol": False,
                    "auto_speed_limit": 0,
                    "speed_limit": 0,
                    "device_limit": 0,
                    "local_rule_list": []
                },
                "cert_config": {
                    "cert_mode": "none",
                    "cert_domain": "",
                    "cert_file": "",
                    "key_file": "",
                    "provider": "",
                    "email": "",
                    "dns_env": {}
                }
            }
        ]
    }