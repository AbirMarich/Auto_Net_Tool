#!/usr/bin/env python3

import os
import json
import requests
from typing import Dict, List, Any

class DeepAIAnalyzer:
    def __init__(self):
        self.api_key = self._load_api_key()
        self.api_url = "https://api.deepai.org/api/chat"
        self.headers = {
            'Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _load_api_key(self) -> str:
        """Load API key from secure location"""
        try:
            # Try environment variable first
            api_key = os.getenv('DEEPAI_API_KEY')
            if api_key:
                return api_key
            
            # Try config file
            config_path = os.path.expanduser('~/.net_auto_tool/config')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.startswith('DEEPAI_API_KEY='):
                            return line.strip().split('=', 1)[1]
            
            return None
        except:
            return None
    
    def analyze_network_config(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze network configuration using DeepAI
        """
        if not self.api_key:
            return {"error": "DeepAI API key not configured. Create ~/.net_auto_tool/config with DEEPAI_API_KEY=your_key"}
        
        # Prepare the prompt for AI analysis
        prompt = self._create_analysis_prompt(network_data)
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_ai_response(result, network_data)
            else:
                return {"error": f"API request failed: {response.status_code}", "details": response.text}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _create_analysis_prompt(self, network_data: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for AI analysis"""
        
        prompt = """You are an expert Cisco network engineer and security analyst. 
        Analyze this network configuration and provide professional recommendations.

        NETWORK CONFIGURATION ANALYSIS:
        ==============================

        DEVICES FOUND:
        """
        
        # Add device information - handle both dict and object devices
        for device in network_data.get('devices', []):
            # Get device attributes safely
            hostname = getattr(device, 'hostname', 'Unknown')
            device_type = type(device).__name__
            
            prompt += f"\n- {hostname} ({device_type})"
            
            # Add interface count if available
            interfaces = getattr(device, 'interfaces', {})
            if interfaces:
                prompt += f" - {len(interfaces)} interfaces"
            
            # Add route count if available
            routes = getattr(device, 'routes', [])
            if routes:
                prompt += f" - {len(routes)} routes"
            
            # Add routing protocols if available
            protocols = getattr(device, 'routing_protocols', [])
            if protocols:
                prompt += f" - Protocols: {', '.join(protocols)}"
        
        prompt += "\n\nCONFIGURATION ISSUES FOUND:"
        for finding in network_data.get('findings', []):
            # Handle both dict and object findings
            if hasattr(finding, 'get'):
                finding_type = finding.get('type', 'INFO')
                message = finding.get('message', '')
            else:
                finding_type = getattr(finding, 'type', 'INFO')
                message = getattr(finding, 'message', '')
            prompt += f"\n- [{finding_type}] {message}"
        
        prompt += "\n\nRECOMMENDATIONS:"
        for recommendation in network_data.get('recommendations', []):
            # Handle both string and object recommendations
            if isinstance(recommendation, str):
                prompt += f"\n- {recommendation}"
            else:
                rec_text = getattr(recommendation, 'message', str(recommendation))
                prompt += f"\n- {rec_text}"
        
        prompt += """

        PLEASE PROVIDE EXPERT ANALYSIS:
        1. SECURITY ASSESSMENT: Identify vulnerabilities and suggest fixes
        2. PERFORMANCE OPTIMIZATION: Suggest performance improvements  
        3. BEST PRACTICES: Cisco best practice recommendations
        4. SCALABILITY: Advice for future network growth
        5. PRIORITIZED ACTION PLAN: Critical fixes first

        Format with clear sections and bullet points. Be specific and actionable.
        Focus on Cisco networking technologies.
        """
        
        return prompt
    
    def _parse_ai_response(self, ai_response: Dict, network_data: Dict) -> Dict:
        """Parse and structure the AI response"""
        
        try:
            # Extract the AI's message content
            if isinstance(ai_response, dict) and 'output' in ai_response:
                ai_message = ai_response['output']
            else:
                ai_message = str(ai_response)
            
            return {
                "success": True,
                "ai_analysis": ai_message,
                "summary": self._extract_summary(ai_message),
                "original_data": network_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse AI response: {str(e)}",
                "raw_response": ai_response
            }
    
    def _extract_summary(self, ai_message: str) -> str:
        """Extract summary from AI response"""
        lines = ai_message.split('\n')
        summary_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('#', '-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                summary_lines.append(line)
            if len(summary_lines) >= 3:  # Get first 3 meaningful lines
                break
        return '\n'.join(summary_lines) if summary_lines else "No summary available"

# Test function
def test_ai_analysis():
    """Test the AI analyzer with proper device objects"""
    # Create mock device objects like your actual ones
    class MockDevice:
        def __init__(self, hostname, device_type):
            self.hostname = hostname
            self.interfaces = {'Gig0/1': {}, 'Gig0/2': {}}
            self.routes = []
            self.routing_protocols = []
    
    class MockFinding:
        def __init__(self, type, message):
            self.type = type
            self.message = message
    
    # Test with object-based data (like your real data)
    mock_devices = [MockDevice("TestSwitch", "Switch"), MockDevice("TestRouter", "Router")]
    mock_findings = [MockFinding("WARNING", "Router interface missing description")]
    mock_recommendations = ["Enable rapid-PVST", "Add interface descriptions"]
    
    sample_network = {
        "devices": mock_devices,
        "findings": mock_findings,
        "recommendations": mock_recommendations
    }
    
    analyzer = DeepAIAnalyzer()
    result = analyzer.analyze_network_config(sample_network)
    print("AI Test Result:", json.dumps(result, indent=2))

if __name__ == "__main__":
    test_ai_analysis()
