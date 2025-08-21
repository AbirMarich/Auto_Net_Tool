import networkx as nx
import matplotlib.pyplot as plt
import ipaddress
import json
import os

def build_topology(device_list):
    """
    Builds network topology with enhanced detection
    """
    G = nx.Graph()
    
    # Add all devices as nodes with their type
    for device in device_list:
        device_type = type(device).__name__
        G.add_node(device.hostname, type=device_type, device_obj=device)
    
    print("[TOPOLOGY] Building links based on IP subnets and descriptions...")
    
    # Link devices based on IP subnets (most accurate)
    links_found = 0
    for i, device1 in enumerate(device_list):
        for intf1, props1 in device1.interfaces.items():
            if props1.get('ip_address') and props1.get('subnet_mask'):
                try:
                    network1 = ipaddress.IPv4Network(f"{props1['ip_address']}/{props1['subnet_mask']}", strict=False)
                    
                    for j, device2 in enumerate(device_list):
                        if i != j:
                            for intf2, props2 in device2.interfaces.items():
                                if props2.get('ip_address'):
                                    try:
                                        if ipaddress.IPv4Address(props2['ip_address']) in network1:
                                            # Found a connection!
                                            G.add_edge(device1.hostname, device2.hostname, 
                                                     interface1=intf1, interface2=intf2,
                                                     network=str(network1))
                                            print(f"    - Linked {device1.hostname}({intf1}) to {device2.hostname}({intf2}) on network {network1}")
                                            links_found += 1
                                            break
                                    except ValueError:
                                        continue
                except ValueError:
                    continue
    
    # Fallback: Use interface descriptions
    for device in device_list:
        for intf_name, props in device.interfaces.items():
            if props.get('description'):
                desc = props['description'].lower()
                # Look for other device names in description
                for other_device in device_list:
                    if (other_device.hostname.lower() in desc and 
                        other_device.hostname != device.hostname and
                        not G.has_edge(device.hostname, other_device.hostname)):
                        G.add_edge(device.hostname, other_device.hostname)
                        print(f"    - Linked {device.hostname} to {other_device.hostname} (via {intf_name}: {props['description']})")
                        break

    return G

def visualize_topology(graph, save_path="output/network_topology.png"):
    """
    Creates a visual diagram that tries to match actual network design
    """
    try:
        plt.figure(figsize=(16, 12))
        
        # Try to load custom layout if exists
        custom_layout = try_load_custom_layout(graph)
        
        if custom_layout:
            pos = custom_layout
            print("[TOPOLOGY] Using custom layout from knowledge base")
        else:
            # Create intelligent layout based on device roles and connections
            pos = create_intelligent_layout(graph)
            print("[TOPOLOGY] Using generated intelligent layout")
        
        # Customize appearance
        node_colors, node_sizes, edge_styles = customize_appearance(graph)
        
        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, 
                              node_color=node_colors, alpha=0.9, edgecolors='black', linewidths=2)
        
        # Draw labels with better formatting
        labels = {node: f"{node}\n({graph.nodes[node].get('type', 'Unknown')})" 
                 for node in graph.nodes()}
        nx.draw_networkx_labels(graph, pos, labels, font_size=9, font_weight='bold')
        
        # Draw edges with styles
        for edge in graph.edges():
            edge_data = graph.get_edge_data(*edge)
            style = edge_styles.get(edge, {'width': 2, 'alpha': 0.7, 'color': 'gray'})
            nx.draw_networkx_edges(graph, pos, edgelist=[edge], **style)
        
        # Draw edge labels (interface names)
        edge_labels = {}
        for u, v, data in graph.edges(data=True):
            if 'interface1' in data and 'interface2' in data:
                edge_labels[(u, v)] = f"{data['interface1']}\n——\n{data['interface2']}"
            elif 'interface1' in data:
                edge_labels[(u, v)] = data['interface1']
        
        nx.draw_networkx_edge_labels(graph, pos, edge_labels, font_size=8, 
                                   bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
        
        # Add legend
        add_legend()
        
        plt.title("Network Topology Diagram\n(Based on Actual Configuration Analysis)", 
                 fontsize=16, pad=20, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        # Save high-quality image
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"[TOPOLOGY] High-quality visualization saved to {save_path}")
        plt.close()
        
    except Exception as e:
        print(f"[TOPOLOGY] Error creating visualization: {e}")
        # Fallback to simple drawing
        simple_visualization(graph, save_path)

def try_load_custom_layout(graph):
    """
    Try to load a pre-defined layout that matches common network designs
    """
    # This would be expanded with more network patterns
    custom_layouts = {
        # Core -> Distribution -> Access pattern
        'core_distribution_access': {
            'R1': (0, 8),    # Core router
            'R2': (4, 8),    # Core router  
            'Switch1': (2, 4),  # Distribution switch
            'Switch2': (6, 4),  # Distribution switch
            'PC1': (1, 0),     # Access devices
            'PC2': (3, 0),
            'Server1': (5, 0)
        },
        # Hub and spoke pattern
        'hub_spoke': {
            'R1': (0, 0),    # Hub
            'R2': (4, 4),    # Spoke
            'R3': (-4, 4),   # Spoke
            'Switch1': (2, 2) # Branch switch
        }
    }
    
    # Try to match device names to known layouts
    for layout_name, layout_pos in custom_layouts.items():
        if all(node in layout_pos for node in graph.nodes()):
            return layout_pos
    
    return None

def create_intelligent_layout(graph):
    """
    Create a layout that makes sense for network devices
    """
    pos = {}
    layer_height = 6
    devices_by_type = {'Router': [], 'Switch': [], 'Other': []}
    
    # Group devices by type
    for node in graph.nodes():
        device_type = graph.nodes[node].get('type', 'Other')
        devices_by_type[device_type].append(node)
    
    # Position routers at the top
    for i, router in enumerate(devices_by_type['Router']):
        pos[router] = (i * 4, layer_height)
    
    # Position switches below routers
    for i, switch in enumerate(devices_by_type['Switch']):
        pos[switch] = (i * 3, layer_height - 2)
    
    # Position other devices at the bottom
    for i, device in enumerate(devices_by_type['Other']):
        pos[device] = (i * 2, layer_height - 4)
    
    return pos

def customize_appearance(graph):
    """Customize visual appearance based on device types"""
    node_colors = []
    node_sizes = []
    edge_styles = {}
    
    for node in graph.nodes():
        device_type = graph.nodes[node].get('type', 'Unknown')
        if device_type == 'Router':
            node_colors.append('#ff6b6b')  # Coral red
            node_sizes.append(3500)
        elif device_type == 'Switch':
            node_colors.append('#4ecdc4')  # Teal
            node_sizes.append(2800)
        else:
            node_colors.append('#45b7d1')  # Light blue
            node_sizes.append(2200)
    
    # Style edges based on connection type
    for u, v, data in graph.edges(data=True):
        if 'network' in data:
            edge_styles[(u, v)] = {'width': 3, 'alpha': 0.8, 'color': '#2ecc71', 'style': 'dashed'}
        else:
            edge_styles[(u, v)] = {'width': 2, 'alpha': 0.6, 'color': '#7f8c8d'}
    
    return node_colors, node_sizes, edge_styles

def add_legend():
    """Add a professional legend"""
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#ff6b6b', label='Routers', edgecolor='black'),
        Patch(facecolor='#4ecdc4', label='Switches', edgecolor='black'),
        Patch(facecolor='#45b7d1', label='End Devices', edgecolor='black'),
        Patch(facecolor='none', label='IP-based Links', edgecolor='#2ecc71', linestyle='dashed'),
        Patch(facecolor='none', label='Description-based Links', edgecolor='#7f8c8d')
    ]
    plt.legend(handles=legend_elements, loc='upper right', framealpha=0.9)

def simple_visualization(graph, save_path):
    """Fallback simple visualization"""
    try:
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(graph, seed=42)
        nx.draw(graph, pos, with_labels=True, node_color='lightblue', 
               node_size=2000, font_size=8)
        plt.savefig(save_path, dpi=100)
        print(f"[TOPOLOGY] Simple visualization saved to {save_path}")
        plt.close()
    except:
        print("[TOPOLOGY] Could not generate visualization")

def export_to_packet_tracer(graph, output_path="output/topology_for_pt.txt"):
    """
    Creates a detailed guide for recreating in Packet Tracer
    """
    try:
        with open(output_path, 'w') as f:
            f.write("Packet Tracer Recreation Guide\n")
            f.write("=" * 40 + "\n\n")
            f.write("Based on actual network configuration analysis\n\n")
            
            # Device inventory
            f.write("DEVICE INVENTORY:\n")
            f.write("-" * 20 + "\n")
            
            routers = [n for n in graph.nodes() if graph.nodes[n].get('type') == 'Router']
            switches = [n for n in graph.nodes() if graph.nodes[n].get('type') == 'Switch']
            others = [n for n in graph.nodes() if graph.nodes[n].get('type') not in ['Router', 'Switch']]
            
            if routers:
                f.write("\nRouters:\n")
                for router in routers:
                    f.write(f"  - {router}\n")
            
            if switches:
                f.write("\nSwitches:\n")
                for switch in switches:
                    f.write(f"  - {switch}\n")
            
            if others:
                f.write("\nOther Devices:\n")
                for device in others:
                    f.write(f"  - {device}\n")
            
            # Connections with interface details
            f.write("\nCONNECTIONS:\n")
            f.write("-" * 20 + "\n")
            for u, v, data in graph.edges(data=True):
                if 'interface1' in data and 'interface2' in data:
                    f.write(f"  {u} {data['interface1']} <——> {v} {data['interface2']}\n")
                    if 'network' in data:
                        f.write(f"    Network: {data['network']}\n")
                else:
                    f.write(f"  {u} <——> {v} (generic connection)\n")
            
            f.write("\nRECOMMENDED LAYOUT:\n")
            f.write("-" * 20 + "\n")
            f.write("Place routers at the top, switches in the middle, end devices at bottom\n")
            f.write("Use the interface information above for accurate cabling\n")
        
        print(f"[TOPOLOGY] Detailed Packet Tracer guide saved to {output_path}")
        
    except Exception as e:
        print(f"Error exporting to Packet Tracer: {e}")
