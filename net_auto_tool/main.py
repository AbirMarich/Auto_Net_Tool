#!/usr/bin/env python3

import argparse
import os
import sys
import json
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Now import the modules
try:
    from config_parser import parse_any_config
    from config_validator import validate_config, generate_recommendations
    from topology import build_topology, visualize_topology, export_to_packet_tracer
    from ai_analyzer import DeepAIAnalyzer
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Note: {e}")
    AI_AVAILABLE = False
    DeepAIAnalyzer = None

def export_network_documentation(graph, output_path):
    """
    Export comprehensive network documentation
    """
    try:
        with open(output_path, 'w') as f:
            f.write("# Network Documentation\n")
            f.write("=" * 50 + "\n\n")
            f.write("## Device Inventory\n")
            f.write("-" * 20 + "\n\n")
            
            # Group devices by type
            routers = [n for n in graph.nodes() if graph.nodes[n].get('type') == 'Router']
            switches = [n for n in graph.nodes() if graph.nodes[n].get('type') == 'Switch']
            others = [n for n in graph.nodes() if graph.nodes[n].get('type') not in ['Router', 'Switch']]
            
            if routers:
                f.write("### Routers\n")
                for router in routers:
                    device = graph.nodes[router]['device_obj']
                    f.write(f"- **{router}**\n")
                    if hasattr(device, 'model') and device.model != "Unknown":
                        f.write(f"  - Model: {device.model}\n")
                    if hasattr(device, 'routing_protocols') and device.routing_protocols:
                        f.write(f"  - Routing Protocols: {', '.join(device.routing_protocols)}\n")
                    f.write("\n")
            
            if switches:
                f.write("### Switches\n")
                for switch in switches:
                    device = graph.nodes[switch]['device_obj']
                    f.write(f"- **{switch}**\n")
                    if hasattr(device, 'vlans') and device.vlans:
                        f.write(f"  - VLANs: {', '.join(sorted(device.vlans))}\n")
                    f.write("\n")
            
            # Network Connections
            f.write("## Network Connections\n")
            f.write("-" * 20 + "\n\n")
            for u, v, data in graph.edges(data=True):
                if 'interface1' in data and 'interface2' in data:
                    f.write(f"- **{u}** {data['interface1']} ↔ **{v}** {data['interface2']}\n")
                    if 'network' in data:
                        f.write(f"  - Network: {data['network']}\n")
                f.write("\n")
            
            # Configuration Summary
            f.write("## Configuration Summary\n")
            f.write("-" * 20 + "\n\n")
            total_interfaces = 0
            for node in graph.nodes():
                device = graph.nodes[node]['device_obj']
                if hasattr(device, 'interfaces'):
                    total_interfaces += len(device.interfaces)
            
            f.write(f"- Total Devices: {len(graph.nodes())}\n")
            f.write(f"- Total Interfaces: {total_interfaces}\n")
            f.write(f"- Total Connections: {len(graph.edges())}\n")
        
        print(f"📋 Network documentation saved to: {output_path}")
        
    except Exception as e:
        print(f"Error creating documentation: {e}")

def run_web_dashboard(port=8080):
    """Start a simple web dashboard to view results"""
    try:
        # Change to output directory to serve files
        os.chdir('output')
        
        class DashboardHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory='.', **kwargs)
            
            def log_message(self, format, *args):
                # Suppress server logs
                pass
        
        server = HTTPServer(('localhost', port), DashboardHandler)
        print(f"🌐 Web dashboard available at: http://localhost:{port}")
        print("   Press Ctrl+C to stop the server")
        
        # Open browser automatically
        webbrowser.open(f'http://localhost:{port}')
        
        server.serve_forever()
        
    except OSError as e:
        print(f"❌ Could not start web server: {e}")
        print("   Another process might be using port 8080")
    except Exception as e:
        print(f"❌ Web dashboard error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Network Configuration Analysis Tool - Validates configs and builds network topology',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python main.py configs/                         # Basic analysis
  python main.py configs/ --ai --verbose          # AI analysis with details
  python main.py configs/ --visualize --document  # Full analysis with docs
  python main.py --web-dashboard                  # Start web interface
        '''
    )
    parser.add_argument('config_path', nargs='?', help='Path to config file or directory containing config files')
    parser.add_argument('--visualize', '-v', action='store_true', help='Generate topology visualization (requires multiple devices)')
    parser.add_argument('--output', '-o', help='Output directory for reports', default='output')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output information')
    parser.add_argument('--document', '-d', action='store_true', help='Generate comprehensive network documentation')
    parser.add_argument('--ai', action='store_true', help='Enable AI-powered analysis using DeepAI')
    parser.add_argument('--web-dashboard', action='store_true', help='Start web dashboard to view results')
    parser.add_argument('--port', type=int, default=8080, help='Port for web dashboard (default: 8080)')
    
    args = parser.parse_args()

    # Handle web dashboard mode
    if args.web_dashboard:
        if not os.path.exists('output'):
            print("❌ No output directory found. Run analysis first to generate reports.")
            return
        run_web_dashboard(args.port)
        return

    # Check if config_path is provided for analysis mode
    if not args.config_path:
        parser.print_help()
        print(f"\n❌ Error: config_path argument is required for analysis mode")
        print("   Use --web-dashboard to view existing results")
        return

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        if args.verbose:
            print(f"Created output directory: {args.output}")

    # Find all config files
    config_files = []
    if os.path.isfile(args.config_path):
        config_files.append(args.config_path)
    elif os.path.isdir(args.config_path):
        for file in os.listdir(args.config_path):
            if file.endswith(('.txt', '.config', '.dump', '.cfg', '.conf')):
                full_path = os.path.join(args.config_path, file)
                config_files.append(full_path)
    else:
        print(f"Error: '{args.config_path}' is not a valid file or directory")
        return

    if not config_files:
        print("No configuration files found")
        return

    print(f"🔍 Analyzing {len(config_files)} configuration file(s)...")
    
    all_findings = []
    all_recommendations = []
    all_devices = []

    for config_file in config_files:
        filename = os.path.basename(config_file)
        if args.verbose:
            print(f"\n=== Analyzing {filename} ===")
        else:
            print(f"\n{filename}:")
        
        device = parse_any_config(config_file)
        if not device:
            print("  ✗ Failed to parse")
            continue
            
        findings = validate_config(device)
        recommendations = generate_recommendations(device)
        
        all_findings.extend(findings)
        all_recommendations.extend(recommendations)
        all_devices.append(device)
        
        print(f"  ✓ {device.hostname} ({type(device).__name__})")
        
        if args.verbose:
            # Show device details in verbose mode
            if hasattr(device, 'interfaces'):
                print(f"    Interfaces: {len(device.interfaces)}")
            if hasattr(device, 'routes'):
                print(f"    Routes: {len(device.routes)}")
            if hasattr(device, 'routing_protocols') and device.routing_protocols:
                print(f"    Routing Protocols: {', '.join(device.routing_protocols)}")
        
        # Show findings for this device
        for finding in findings:
            emoji = "❌" if finding['type'] == 'ERROR' else "⚠️ " if finding['type'] == 'WARNING' else "ℹ️ "
            print(f"  {emoji} {finding['message']}")
        
        for rec in recommendations:
            print(f"  💡 {rec}")

    # Summary report
    error_count = sum(1 for f in all_findings if f['type'] == 'ERROR')
    warning_count = sum(1 for f in all_findings if f['type'] == 'WARNING')
    info_count = sum(1 for f in all_findings if f['type'] == 'INFO')
    
    print(f"\n📊 === SUMMARY ===")
    print(f"Devices analyzed: {len(all_devices)}")
    print(f"Findings: {error_count} errors, {warning_count} warnings, {info_count} info")
    print(f"Recommendations: {len(all_recommendations)}")

    # Save summary to file
    try:
        summary_file = os.path.join(args.output, 'validation_summary.txt')
        with open(summary_file, 'w') as f:
            f.write("Network Configuration Validation Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Devices analyzed: {len(all_devices)}\n")
            f.write(f"Errors: {error_count}\n")
            f.write(f"Warnings: {warning_count}\n")
            f.write(f"Info: {info_count}\n")
            f.write(f"Recommendations: {len(all_recommendations)}\n\n")
            
            if all_findings:
                f.write("DETAILED FINDINGS:\n")
                f.write("-" * 30 + "\n")
                for finding in all_findings:
                    f.write(f"[{finding['type']}] {finding['message']}\n")
            
            if all_recommendations:
                f.write("\nRECOMMENDATIONS:\n")
                f.write("-" * 30 + "\n")
                for rec in all_recommendations:
                    f.write(f"{rec}\n")
        
        print(f"📄 Report saved to: {summary_file}")
    except Exception as e:
        print(f"Error saving report: {e}")

    # Topology generation (only if we have multiple devices)
    if len(all_devices) > 1:
        print(f"\n🌐 === TOPOLOGY GENERATION ===")
        try:
            network_graph = build_topology(all_devices)
            print(f"Topology built with {network_graph.number_of_nodes()} nodes and {network_graph.number_of_edges()} links.")
            
            # Generate and save visualization if requested
            if args.visualize:
                viz_path = os.path.join(args.output, 'network_topology.png')
                visualize_topology(network_graph, viz_path)
                print(f"📊 Visualization saved to: {viz_path}")
            
            # Export Packet Tracer guide
            try:
                pt_guide_path = os.path.join(args.output, 'packet_tracer_guide.txt')
                export_to_packet_tracer(network_graph, pt_guide_path)
                print(f"📋 Packet Tracer setup guide: {pt_guide_path}")
            except Exception as e:
                print(f"Note: Could not create Packet Tracer guide: {e}")
            
            # Generate comprehensive documentation if requested
            if args.document:
                try:
                    doc_path = os.path.join(args.output, 'network_documentation.md')
                    export_network_documentation(network_graph, doc_path)
                    print(f"📚 Network documentation: {doc_path}")
                except Exception as e:
                    print(f"Note: Could not create documentation: {e}")
            
        except Exception as e:
            print(f"Error generating topology: {e}")
    elif len(all_devices) <= 1:
        print(f"\nℹ️  Topology generation requires at least 2 devices (found {len(all_devices)})")
    
    # AI ANALYSIS SECTION
    if args.ai and AI_AVAILABLE and all_devices:
        print(f"\n🧠 === AI-POWERED ANALYSIS ===")
        ai_analyzer = DeepAIAnalyzer()
        
        # Prepare network data for AI analysis
        network_data = {
            "devices": all_devices,
            "findings": all_findings,
            "recommendations": all_recommendations
        }
        
        ai_result = ai_analyzer.analyze_network_config(network_data)
        
        if ai_result.get('success'):
            print("✅ AI analysis completed successfully!")
            print("\n" + "="*60)
            print("🤖 AI NETWORK ANALYSIS REPORT")
            print("="*60)
            print(ai_result.get('ai_analysis', ''))
            
            # Save AI analysis to file
            ai_report_path = os.path.join(args.output, 'ai_analysis_report.txt')
            with open(ai_report_path, 'w', encoding='utf-8') as f:
                f.write("AI-Powered Network Analysis Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(ai_result.get('ai_analysis', ''))
            print(f"📋 AI report saved to: {ai_report_path}")
            
        else:
            print(f"❌ AI analysis failed: {ai_result.get('error', 'Unknown error')}")
            if 'details' in ai_result:
                print(f"Details: {ai_result['details']}")
    elif args.ai and not AI_AVAILABLE:
        print(f"\n❌ AI analysis requested but ai_analyzer module not available")
    elif args.ai and not all_devices:
        print(f"\n❌ AI analysis requested but no devices were parsed successfully")

    # Show tips for better results
    if len(all_devices) > 0:
        print(f"\n💡 TIPS FOR BETTER RESULTS:")
        print(f"   - Ensure all config files have unique hostnames")
        print(f"   - Use descriptive interface descriptions (e.g., 'to Router1')")
        print(f"   - Include IP addresses on connected interfaces")
        print(f"   - Use --verbose for detailed parsing information")
        print(f"   - Use --ai for AI-powered analysis")
        print(f"   - Use --web-dashboard to view results in browser")

    # Final status
    if error_count == 0 and warning_count == 0:
        print(f"\n🎉 Validation completed successfully!")
    elif error_count == 0:
        print(f"\n✅ Validation completed with {warning_count} warning(s)")
    else:
        print(f"\n⚠️  Validation completed with {error_count} error(s) and {warning_count} warning(s)")

    # Suggest web dashboard if output files were created
    if os.path.exists(args.output) and any(os.listdir(args.output)):
        print(f"\n🌐 Run 'python main.py --web-dashboard' to view results in your browser!")

if __name__ == '__main__':
    main()
