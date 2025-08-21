# Import the device classes
try:
    from .device import Switch, Router
except ImportError:
    from device import Switch, Router

def validate_config(device):
    findings = []
    
    if isinstance(device, Switch):
        # Switch validations (existing code)
        for intf_name, props in device.interfaces.items():
            if props.get('description') and any(word in props['description'].lower() for word in ['rtr', 'router', 'to r']):
                if props.get('mode') == 'access':
                    findings.append({
                        'type': 'WARNING',
                        'message': f"{device.hostname}: Interface {intf_name} ({props['description']}) is an access port connected to a router. Should be a trunk.",
                        'component': 'Interface Configuration'
                    })
            if not props.get('shutdown') and props.get('mode') is None and not props.get('description'):
                findings.append({
                    'type': 'INFO',
                    'message': f"{device.hostname}: Interface {intf_name} is active but unused. Consider shutting down.",
                    'component': 'Security'
                })
    
    elif isinstance(device, Router):
        # Enhanced router validations
        print(f"  [DEBUG] Validating router {device.hostname} with {len(device.interfaces)} interfaces")
        
        # Check for interfaces without IP addresses (WAN links might be OK)
        for intf_name, props in device.interfaces.items():
            if not props.get('shutdown') and not props.get('ip_address'):
                # Skip serial interfaces which might use PPP/HDLC
                if not intf_name.lower().startswith('serial'):
                    findings.append({
                        'type': 'INFO',
                        'message': f"{device.hostname}: Interface {intf_name} is active but has no IP address configured.",
                        'component': 'IP Configuration'
                    })
            
            # Check for missing descriptions
            if not props.get('description') and not props.get('shutdown'):
                findings.append({
                    'type': 'INFO',
                    'message': f"{device.hostname}: Interface {intf_name} has no description. Add documentation.",
                    'component': 'Documentation'
                })
        
        # Check routing protocol configuration
        if not device.routing_protocols and len(device.routes) > 5:
            findings.append({
                'type': 'RECOMMENDATION',
                'message': f"{device.hostname}: Using only static routes. Consider dynamic routing (OSPF/BGP) for better scalability.",
                'component': 'Routing'
            })
        
        # Check for default route
        has_default_route = any(route['network'] == '0.0.0.0' for route in device.routes)
        if not has_default_route:
            findings.append({
                'type': 'INFO',
                'message': f"{device.hostname}: No default route configured. Ensure internet connectivity is properly routed.",
                'component': 'Routing'
            })
    
    return findings

def generate_recommendations(device):
    recs = []
    
    if isinstance(device, Switch):
        if hasattr(device, 'stp_mode') and device.stp_mode == 'pvst':
            recs.append(f"{device.hostname}: Consider using 'spanning-tree mode rapid-pvst' for faster convergence.")
    
    elif isinstance(device, Router):
        # Router-specific recommendations
        if hasattr(device, 'routes') and len(device.routes) > 10:
            if not any('ospf' in proto for proto in device.routing_protocols):
                recs.append(f"{device.hostname}: Many routes detected. Implement OSPF for dynamic routing.")
        
        # Check for BGP vs OSPF recommendation
        if hasattr(device, 'routes') and len(device.routes) > 50:
            if not any('bgp' in proto for proto in device.routing_protocols):
                recs.append(f"{device.hostname}: Very large routing table. Consider BGP for enterprise networks.")
    
    return recs
