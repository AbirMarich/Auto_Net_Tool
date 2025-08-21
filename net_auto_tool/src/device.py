class NetworkDevice:
    def __init__(self, hostname="Unknown"):
        self.hostname = hostname
        self.vendor = "Unknown"
        self.interfaces = {}
        self.model = "Unknown"

    def __str__(self):
        return f"{self.vendor} {type(self).__name__}: {self.hostname}"

class Switch(NetworkDevice):
    def __init__(self, hostname="Unknown"):
        super().__init__(hostname)
        self.vendor = "Cisco"
        self.vlans = set()
        self.stp_mode = None

class Router(NetworkDevice):
    def __init__(self, hostname="Unknown"):
        super().__init__(hostname)
        self.vendor = "Cisco"
        self.routing_protocols = []
        self.routes = []
        self.bgp_asn = None
        self.ospf_process_id = None

def detect_device_type(config_text):
    """
    Enhanced device type detection with multiple indicators
    """
    config_text_lower = config_text.lower()
    
    # Strong indicators for switches
    switch_indicators = [
        'switchport', 'spanning-tree', 'vtp mode', 
        'vlan database', 'show mac address-table'
    ]
    
    # Strong indicators for routers
    router_indicators = [
        'router ospf', 'router bgp', 'router eigrp', 
        'ip route ', 'interface serial', 'ppp authentication',
        'frame-relay', 'ip nat', 'ipsec', 'crypto map'
    ]
    
    switch_score = sum(1 for indicator in switch_indicators if indicator in config_text_lower)
    router_score = sum(1 for indicator in router_indicators if indicator in config_text_lower)
    
    # Additional checks for ambiguous cases
    has_routing_protocol = any(x in config_text_lower for x in ['ospf', 'bgp', 'eigrp', 'rip'])
    has_switch_commands = any(x in config_text_lower for x in ['vlan', 'switchport'])
    
    if router_score > switch_score:
        return 'router'
    elif switch_score > router_score:
        return 'switch'
    elif has_routing_protocol and not has_switch_commands:
        return 'router'
    elif has_switch_commands and not has_routing_protocol:
        return 'switch'
    else:
        # Look for interface types
        if 'interface serial' in config_text_lower or 'interface tunnel' in config_text_lower:
            return 'router'
        elif 'interface vlan' in config_text_lower or 'interface port-channel' in config_text_lower:
            return 'switch'
        return 'unknown'
