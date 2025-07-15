"""
AI Agent 2: Policy Checker
Checks the analyzed architecture against Microsoft Azure policies for compliance
"""

import json
import os
from typing import Dict, List, Any
import openai
from dotenv import load_dotenv

load_dotenv()

class PolicyChecker:
    def __init__(self):
        # Check if Azure AI Foundry configuration is available
        self.azure_endpoint = os.getenv('AZURE_AI_AGENT2_ENDPOINT')
        self.azure_key = os.getenv('AZURE_AI_AGENT2_KEY')
        self.azure_deployment = os.getenv('AZURE_AI_AGENT2_DEPLOYMENT', 'gpt-4')
        
        if self.azure_endpoint and self.azure_key:
            # Use Azure AI Foundry endpoint
            self.openai_client = openai.AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_key,
                api_version="2024-02-01"
            )
            self.model_name = self.azure_deployment
            print(f"✅ Policy Checker: Using Azure AI Foundry endpoint")
        else:
            # Fallback to OpenAI
            self.openai_client = openai.OpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
            self.model_name = "gpt-4"
            print(f"⚠️ Policy Checker: Using OpenAI fallback (configure Azure AI Foundry for production)")
        
        # Load policy templates
        self.policy_templates = self._load_policy_templates()
    
    def check_compliance(self, architecture_analysis: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """
        Check architecture compliance against Azure policies
        """
        try:
            # Get environment-specific policies
            applicable_policies = self._get_environment_policies(environment)
            
            # Create compliance check prompt
            compliance_prompt = self._create_compliance_prompt(
                architecture_analysis, 
                applicable_policies, 
                environment
            )
            
            # Call OpenAI API for compliance analysis
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an Azure compliance expert. Analyze the architecture against Microsoft Azure policies and provide detailed compliance recommendations."
                    },
                    {
                        "role": "user",
                        "content": compliance_prompt
                    }
                ],
                temperature=0.1
            )
            
            # Parse compliance results
            compliance_result = self._parse_compliance_response(
                response.choices[0].message.content,
                environment
            )
            
            return compliance_result
            
        except Exception as e:
            return {
                'error': f'Policy compliance check failed: {str(e)}',
                'compliant': False,
                'violations': [],
                'recommendations': []
            }
    
    def _load_policy_templates(self) -> Dict[str, Any]:
        """Load Azure policy templates"""
        return {
            'development': {
                'security': [
                    'Enable encryption at rest for all storage accounts',
                    'Use managed identities for service authentication',
                    'Implement network security groups (NSGs)',
                    'Enable Azure Security Center recommendations'
                ],
                'networking': [
                    'Use private endpoints for PaaS services',
                    'Implement proper subnet segmentation',
                    'Configure Azure Firewall or NSGs for traffic filtering'
                ],
                'governance': [
                    'Apply consistent resource tagging',
                    'Use Azure Policy for governance enforcement',
                    'Implement resource locks for critical resources'
                ],
                'cost_optimization': [
                    'Use appropriate VM sizes for workloads',
                    'Implement auto-scaling where applicable',
                    'Use Azure Reserved Instances for predictable workloads'
                ]
            },
            'production': {
                'security': [
                    'Enable encryption at rest and in transit',
                    'Use Azure Key Vault for secrets management',
                    'Implement multi-factor authentication',
                    'Enable Azure Security Center Standard tier',
                    'Use managed identities exclusively',
                    'Implement Azure Sentinel for SIEM',
                    'Enable audit logging for all resources'
                ],
                'networking': [
                    'Use private endpoints for all PaaS services',
                    'Implement network segmentation with NSGs',
                    'Use Azure Firewall for centralized traffic filtering',
                    'Implement DDoS protection',
                    'Use Application Gateway with WAF'
                ],
                'governance': [
                    'Apply comprehensive resource tagging strategy',
                    'Use Azure Policy for strict governance enforcement',
                    'Implement resource locks for all critical resources',
                    'Use Azure Blueprints for consistent deployments',
                    'Implement proper RBAC with least privilege'
                ],
                'availability': [
                    'Implement multi-region deployment',
                    'Use availability zones where supported',
                    'Implement backup and disaster recovery',
                    'Use Azure Site Recovery for business continuity'
                ],
                'cost_optimization': [
                    'Use appropriate VM sizes with monitoring',
                    'Implement comprehensive auto-scaling',
                    'Use Azure Reserved Instances for stable workloads',
                    'Implement Azure Cost Management alerts'
                ]
            }
        }
    
    def _get_environment_policies(self, environment: str) -> Dict[str, List[str]]:
        """Get policies specific to the environment"""
        return self.policy_templates.get(environment.lower(), self.policy_templates['development'])
    
    def _create_compliance_prompt(self, analysis: Dict[str, Any], policies: Dict[str, List[str]], environment: str) -> str:
        """Create compliance check prompt"""
        
        prompt = f"""
        Please analyze the following Azure architecture for compliance with Microsoft Azure policies.
        
        Environment: {environment.upper()}
        
        Architecture Analysis:
        {json.dumps(analysis, indent=2)}
        
        Applicable Policies:
        {json.dumps(policies, indent=2)}
        
        Please provide a detailed compliance analysis in the following JSON structure:
        {{
            "overall_compliance": {{
                "compliant": boolean,
                "compliance_score": "percentage",
                "critical_violations": number,
                "warnings": number
            }},
            "category_compliance": {{
                "security": {{
                    "compliant": boolean,
                    "violations": [],
                    "recommendations": []
                }},
                "networking": {{
                    "compliant": boolean,
                    "violations": [],
                    "recommendations": []
                }},
                "governance": {{
                    "compliant": boolean,
                    "violations": [],
                    "recommendations": []
                }},
                "cost_optimization": {{
                    "compliant": boolean,
                    "violations": [],
                    "recommendations": []
                }},
                "availability": {{
                    "compliant": boolean,
                    "violations": [],
                    "recommendations": []
                }}
            }},
            "violations": [
                {{
                    "severity": "critical|warning|info",
                    "category": "security|networking|governance|cost|availability",
                    "component": "affected_component_name",
                    "description": "violation_description",
                    "recommendation": "how_to_fix",
                    "policy_reference": "azure_policy_reference"
                }}
            ],
            "recommendations": [
                {{
                    "priority": "high|medium|low",
                    "category": "security|networking|governance|cost|availability",
                    "component": "affected_component_name",
                    "description": "recommendation_description",
                    "implementation": "how_to_implement",
                    "benefits": "expected_benefits"
                }}
            ]
        }}
        
        Focus on:
        1. Security best practices and compliance
        2. Network security and segmentation
        3. Governance and resource management
        4. Cost optimization opportunities
        5. High availability and disaster recovery
        6. Specific {environment} environment requirements
        """
        
        return prompt
    
    def _parse_compliance_response(self, response: str, environment: str) -> Dict[str, Any]:
        """Parse the compliance response"""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                compliance_data = json.loads(json_match.group())
                compliance_data['environment'] = environment
                compliance_data['check_timestamp'] = self._get_timestamp()
                return compliance_data
            else:
                return self._fallback_compliance_parse(response, environment)
        except json.JSONDecodeError:
            return self._fallback_compliance_parse(response, environment)
    
    def _fallback_compliance_parse(self, response: str, environment: str) -> Dict[str, Any]:
        """Fallback parsing for compliance response"""
        return {
            'overall_compliance': {
                'compliant': False,
                'compliance_score': 'Unknown',
                'critical_violations': 0,
                'warnings': 0
            },
            'category_compliance': {},
            'violations': [],
            'recommendations': [],
            'environment': environment,
            'check_timestamp': self._get_timestamp(),
            'raw_response': response,
            'parsing_note': 'Used fallback parsing due to JSON parsing error'
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_compliance_report(self, compliance_result: Dict[str, Any]) -> str:
        """Generate a human-readable compliance report"""
        report = f"""
# Azure Architecture Compliance Report

## Environment: {compliance_result.get('environment', 'Unknown').upper()}
## Generated: {compliance_result.get('check_timestamp', 'Unknown')}

## Overall Compliance Summary
- **Compliant**: {compliance_result.get('overall_compliance', {}).get('compliant', 'Unknown')}
- **Compliance Score**: {compliance_result.get('overall_compliance', {}).get('compliance_score', 'Unknown')}
- **Critical Violations**: {compliance_result.get('overall_compliance', {}).get('critical_violations', 0)}
- **Warnings**: {compliance_result.get('overall_compliance', {}).get('warnings', 0)}

## Violations Found
"""
        
        violations = compliance_result.get('violations', [])
        for i, violation in enumerate(violations, 1):
            report += f"""
### {i}. {violation.get('severity', 'Unknown').upper()} - {violation.get('category', 'Unknown').title()}
- **Component**: {violation.get('component', 'Unknown')}
- **Description**: {violation.get('description', 'No description')}
- **Recommendation**: {violation.get('recommendation', 'No recommendation')}
- **Policy Reference**: {violation.get('policy_reference', 'Not specified')}
"""
        
        report += "\n## Recommendations\n"
        recommendations = compliance_result.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            report += f"""
### {i}. {rec.get('priority', 'Unknown').upper()} Priority - {rec.get('category', 'Unknown').title()}
- **Component**: {rec.get('component', 'Unknown')}
- **Description**: {rec.get('description', 'No description')}
- **Implementation**: {rec.get('implementation', 'No implementation details')}
- **Benefits**: {rec.get('benefits', 'No benefits listed')}
"""
        
        return report
