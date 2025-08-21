# src/advanced_analyzer.py
class NetworkIntelligenceEngine:
    def __init__(self):
        self.knowledge_base = self.load_knowledge_base()
        
    def load_knowledge_base(self):
        """Load best practices, common misconfigurations, and optimization rules"""
        return {
            'common_misconfigs': [
                {
                    'pattern': 'router-on-access-port',
                    'description': 'Router connected to access port instead of trunk',
                    'severity': 'HIGH',
                    'fix': 'Convert access port to trunk port'
                },
                {
                    'pattern': 'duplicate-ip',
                    'description': 'Duplicate IP address detected',
                    'severity': 'CRITICAL', 
                    'fix': 'Assign unique IP addresses'
                },
                # ... more patterns
            ],
            'optimization_rules': [
                {
                    'condition': 'static_routes > 10',
                    'recommendation': 'Implement OSPF for dynamic routing',
                    'benefit': 'Reduced management overhead, automatic failover'
                }
            ]
        }
    
    def generate_health_score(self, network_data):
        """Calculate network health score (0-100)"""
        score = 100
        for finding in network_data['findings']:
            if finding['severity'] == 'CRITICAL': score -= 20
            elif finding['severity'] == 'HIGH': score -= 10
            elif finding['severity'] == 'MEDIUM': score -= 5
        return max(0, score)
    
    def generate_improvement_plan(self, network_data):
        """Create prioritized improvement plan"""
        plan = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for finding in network_data['findings']:
            plan[finding['severity'].lower()].append({
                'issue': finding['description'],
                'fix': finding.get('fix', 'Review configuration'),
                'impact': 'High' if finding['severity'] in ['CRITICAL', 'HIGH'] else 'Medium'
            })
        
        return plan
