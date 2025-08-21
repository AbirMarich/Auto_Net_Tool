try:
    from .device import detect_device_type, Switch, Router
    from . import switch_parser
    from . import router_parser
except ImportError:
    from device import detect_device_type, Switch, Router
    import switch_parser
    import router_parser

def parse_any_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            config_text = f.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except UnicodeDecodeError:
        print(f"Error: Could not read {file_path} (encoding issue)")
        return None

    # Skip empty files
    if not config_text.strip():
        print(f"Warning: {file_path} is empty")
        return None

    device_type = detect_device_type(config_text)
    device_obj = None

    if device_type == 'switch':
        device_obj = Switch()
        try:
            switch_parser.parse_switch_config(config_text, device_obj)
            print(f"  ✓ Successfully parsed as Switch")
        except Exception as e:
            print(f"  ✗ Switch parsing failed: {e}")
            return None
            
    elif device_type == 'router':
        device_obj = Router()
        try:
            router_parser.parse_router_config(config_text, device_obj)
            print(f"  ✓ Successfully parsed as Router")
        except Exception as e:
            print(f"  ✗ Router parsing failed: {e}")
            return None
            
    else:
        print(f"  ⚠ Could not determine device type for {os.path.basename(file_path)}")
        return None

    return device_obj
