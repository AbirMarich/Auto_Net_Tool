import re

def parse_switch_config(config_text, switch_device):
    # Extract Hostname
    hostname_match = re.search(r'hostname (\S+)', config_text)
    if hostname_match:
        switch_device.hostname = hostname_match.group(1)

    # Find all interface blocks
    interface_blocks = re.findall(r'(interface \S+\n(?: .*\n)*?!)', config_text)
    
    for block in interface_blocks:
        intf_name_match = re.search(r'interface (\S+)', block)
        if not intf_name_match:
            continue
        intf_name = intf_name_match.group(1)
        
        # Initialize the interface dictionary
        switch_device.interfaces[intf_name] = {
            'description': None,
            'mode': None,
            'access_vlan': None,
            'shutdown': 'shutdown' in block
        }
        
        # Parse description
        desc_match = re.search(r'description (.+)$', block, re.MULTILINE)
        if desc_match:
            switch_device.interfaces[intf_name]['description'] = desc_match.group(1).strip()
            
        # Parse switchport mode
        mode_match = re.search(r'switchport mode (\S+)', block)
        if mode_match:
            switch_device.interfaces[intf_name]['mode'] = mode_match.group(1)
            
        # Parse access VLAN
        vlan_match = re.search(r'switchport access vlan (\S+)', block)
        if vlan_match:
            vlan_id = vlan_match.group(1)
            switch_device.interfaces[intf_name]['access_vlan'] = vlan_id
            switch_device.vlans.add(vlan_id)
