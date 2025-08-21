import re

def parse_router_config(config_text, router_device):
    """
    Comprehensive router configuration parser
    """
    # Extract Hostname (with better pattern matching)
    hostname_match = re.search(r'hostname\s+(\S+)', config_text, re.IGNORECASE)
    if hostname_match:
        router_device.hostname = hostname_match.group(1).strip()

    # Extract model from version string (if available)
    model_match = re.search(r'(\d{4})\s+(?:router|series)', config_text, re.IGNORECASE)
    if model_match:
        router_device.model = f"Cisco {model_match.group(1)}"

    # Find all interface blocks with better regex
    interface_blocks = re.findall(r'(interface\s+\S+.*?(?=!\s*$|\ninterface\s+\S+|\nend))', config_text, re.DOTALL | re.IGNORECASE)
    
    for block in interface_blocks:
        intf_name_match = re.search(r'interface\s+(\S+)', block, re.IGNORECASE)
        if not intf_name_match:
            continue
            
        intf_name = intf_name_match.group(1)
        
        # Initialize the interface dictionary with all possible fields
        router_device.interfaces[intf_name] = {
            'description': None,
            'ip_address': None,
            'subnet_mask': None,
            'shutdown': False,
            'bandwidth': None,
            'duplex': None,
            'speed': None,
            'encapsulation': None,
            'vrf': None
        }
        
        # Parse shutdown status (multiple patterns)
        shutdown_match = re.search(r'shutdown', block, re.IGNORECASE)
        if shutdown_match:
            router_device.interfaces[intf_name]['shutdown'] = True
        
        # Parse description (handle multi-line descriptions)
        desc_match = re.search(r'description\s+(.+?)(?=\n\S|\n\n|$)', block, re.DOTALL | re.IGNORECASE)
        if desc_match:
            router_device.interfaces[intf_name]['description'] = desc_match.group(1).strip()
            
        # Parse IP address with various formats
        ip_match = re.search(r'ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)', block, re.IGNORECASE)
        if ip_match:
            router_device.interfaces[intf_name]['ip_address'] = ip_match.group(1)
            router_device.interfaces[intf_name]['subnet_mask'] = ip_match.group(2)
        
        # Parse secondary IP addresses
        sec_ip_match = re.search(r'ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+secondary', block, re.IGNORECASE)
        if sec_ip_match:
            # Store secondary IPs in a list
            if 'secondary_ips' not in router_device.interfaces[intf_name]:
                router_device.interfaces[intf_name]['secondary_ips'] = []
            router_device.interfaces[intf_name]['secondary_ips'].append({
                'ip': sec_ip_match.group(1),
                'mask': sec_ip_match.group(2)
            })
            
        # Parse bandwidth
        bw_match = re.search(r'bandwidth\s+(\d+)', block, re.IGNORECASE)
        if bw_match:
            router_device.interfaces[intf_name]['bandwidth'] = bw_match.group(1)
            
        # Parse duplex and speed
        duplex_match = re.search(r'duplex\s+(\S+)', block, re.IGNORECASE)
        if duplex_match:
            router_device.interfaces[intf_name]['duplex'] = duplex_match.group(1)
            
        speed_match = re.search(r'speed\s+(\d+)', block, re.IGNORECASE)
        if speed_match:
            router_device.interfaces[intf_name]['speed'] = speed_match.group(1)

    # Parse OSPF configuration comprehensively
    ospf_blocks = re.findall(r'router\s+ospf\s+(\d+).*?(?=!\s*$|\nrouter\s+\S+)', config_text, re.DOTALL | re.IGNORECASE)
    for ospf_block in ospf_blocks:
        process_id = re.search(r'router\s+ospf\s+(\d+)', ospf_block, re.IGNORECASE)
        if process_id:
            router_device.ospf_process_id = process_id.group(1)
            router_device.routing_protocols.append(f'ospf_{process_id.group(1)}')
            
            # Parse OSPF networks
            network_matches = re.findall(r'network\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+area\s+(\d+)', ospf_block, re.IGNORECASE)
            for network, mask, area in network_matches:
                router_device.routes.append({
                    'network': network,
                    'mask': mask,
                    'type': 'ospf',
                    'area': area
                })

    # Parse BGP configuration
    bgp_blocks = re.findall(r'router\s+bgp\s+(\d+).*?(?=!\s*$|\nrouter\s+\S+)', config_text, re.DOTALL | re.IGNORECASE)
    for bgp_block in bgp_blocks:
        asn_match = re.search(r'router\s+bgp\s+(\d+)', bgp_block, re.IGNORECASE)
        if asn_match:
            router_device.bgp_asn = asn_match.group(1)
            router_device.routing_protocols.append(f'bgp_{asn_match.group(1)}')

    # Parse static routes (multiple formats)
    static_routes = re.findall(r'ip\s+route\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)(?:\s+(\d+))?', config_text, re.IGNORECASE)
    for network, mask, next_hop, admin_distance in static_routes:
        route_info = {
            'network': network,
            'mask': mask,
            'next_hop': next_hop,
            'type': 'static'
        }
        if admin_distance:
            route_info['admin_distance'] = admin_distance
        router_device.routes.append(route_info)

    # Parse default routes
    default_routes = re.findall(r'ip\s+route\s+0\.0\.0\.0\s+0\.0\.0\.0\s+(\S+)', config_text, re.IGNORECASE)
    for next_hop in default_routes:
        router_device.routes.append({
            'network': '0.0.0.0',
            'mask': '0.0.0.0',
            'next_hop': next_hop,
            'type': 'static_default'
        })

    return router_device
