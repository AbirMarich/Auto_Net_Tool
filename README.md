# Auto Net Tool

**Auto Net Tool** is a Python-based network configuration analysis and documentation tool for Cisco networks. It validates device configs, builds network topology, generates documentation, and provides AI-powered recommendations.

## Features

- **Config Validation:** Checks Cisco router and switch configs for errors, warnings, and best practices.
- **Topology Builder:** Automatically builds a network topology graph from multiple device configs.
- **Visualization:** Generates a PNG image of your network topology.
- **Documentation:** Creates Markdown documentation and Packet Tracer setup guides.
- **AI Analysis:** Uses DeepAI to provide expert recommendations and security assessments.
- **Web Dashboard:** View results and reports in your browser.

## Folder Structure

```
net_auto_tool/
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
├── configs/                 # Example config files (.txt, .cfg, .conf, .pkt)
├── output/                  # Generated reports and visualizations
├── src/                     # Source code modules
│   ├── config_parser.py
│   ├── config_validator.py
│   ├── topology.py
│   ├── ai_analyzer.py
│   ├── device.py
│   ├── router_parser.py
│   ├── switch_parser.py
│   └── web_dashboard.py
└── Test1/                   # Example output folder
```

## Quick Start

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Run basic analysis:**
   ```sh
   python main.py configs/
   ```

3. **Enable verbose output:**
   ```sh
   python main.py configs/ --verbose
   ```

4. **Generate topology visualization and documentation:**
   ```sh
   python main.py configs/ --visualize --document
   ```

5. **AI-powered analysis (requires DeepAI API key):**
   ```sh
   python main.py configs/ --ai
   ```

6. **View results in browser:**
   ```sh
   python main.py --web-dashboard
   ```

## AI Analysis Setup

- Set your DeepAI API key as an environment variable:
  ```sh
  set DEEPAI_API_KEY=your_api_key_here
  ```
- Or add it to `~/.net_auto_tool/config`:
  ```
  DEEPAI_API_KEY=your_api_key_here
  ```

## Supported Config File Types

- `.txt`, `.cfg`, `.conf`, `.config`, `.dump` (Cisco running configs)
- `.pkt` (Packet Tracer files, limited support)

## Output

- `output/validation_summary.txt` — Validation report
- `output/network_topology.png` — Topology visualization
- `output/packet_tracer_guide.txt` — Packet Tracer setup guide
- `output/network_documentation.md` — Markdown documentation
- `output/ai_analysis_report.txt` — AI-powered analysis (if enabled)

## Extending

- Add new device types or parsers in `src/device.py`, `src/router_parser.py`, `src/switch_parser.py`.
- Customize validation logic in `src/config_validator.py`.
- Enhance AI analysis in `src/ai_analyzer.py`.

## Requirements

- Python 3.7+
- See `requirements.txt` for dependencies (e.g., `networkx`, `matplotlib`, `requests`, `flask` for web dashboard).

## License

MIT License

---

**Auto Net Tool** — Automate your Cisco network documentation and validation!
