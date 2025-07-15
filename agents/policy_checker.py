"""
AI Agent 2: Policy Checker
Checks the analyzed architecture against Microsoft Azure policies for compliance
"""

import json
import os
from typing import Dict, List, Any
import openai
from dotenv import load_dotenv
import hashlib

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
        
        # Simple cache for policy checks
        self._cache = {}
        self._max_cache_size = 50
    
    def check_compliance(self, architecture_analysis: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """
        Check architecture compliance against Azure policies
        """
        # Check cache first
        cache_key = self._get_cache_key(architecture_analysis, environment)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            print("🔍 Policy Checker: Using cached result")
            return cached_result
        
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
            
            # Save to cache
            self._save_to_cache(cache_key, compliance_result)
            
            return compliance_result
            
        except Exception as e:
            return {
                'error': f'Policy compliance check failed: {str(e)}',
                'compliant': False,
                'violations': [],
                'recommendations': []
            }
    
    def _load_policy_templates(self) -> Dict[str, Any]:
        """Load Azure policy templates with environment-specific compliance levels"""
        return {
            'development': {
                'compliance_level': 'relaxed',
                'required_policies': 5,  # Minimum policies to enforce
                'security': {
                    'level': 'basic',
                    'policies': [
                        'Enable encryption at rest for storage accounts',
                        'Use managed identities where possible',
                        'Implement basic network security groups (NSGs)',
                        'Enable Azure Security Center free tier'
                    ]
                },
                'networking': {
                    'level': 'basic',
                    'policies': [
                        'Implement basic subnet segmentation',
                        'Configure NSGs for traffic filtering'
                    ]
                },
                'governance': {
                    'level': 'basic',
                    'policies': [
                        'Apply basic resource tagging (Environment, CreatedBy)',
                        'Use resource locks for critical resources only'
                    ]
                },
                'cost_optimization': {
                    'level': 'basic',
                    'policies': [
                        'Use appropriate VM sizes for development workloads',
                        'Consider auto-scaling for variable workloads'
                    ]
                }
            },
            'staging': {
                'compliance_level': 'moderate',
                'required_policies': 8,  # More policies required
                'security': {
                    'level': 'moderate',
                    'policies': [
                        'Enable encryption at rest and in transit',
                        'Use Azure Key Vault for secrets management',
                        'Use managed identities exclusively',
                        'Enable Azure Security Center Standard tier',
                        'Implement basic audit logging'
                    ]
                },
                'networking': {
                    'level': 'moderate',
                    'policies': [
                        'Use private endpoints for PaaS services',
                        'Implement proper subnet segmentation',
                        'Configure Azure Firewall or advanced NSGs',
                        'Consider DDoS protection'
                    ]
                },
                'governance': {
                    'level': 'moderate',
                    'policies': [
                        'Apply comprehensive resource tagging',
                        'Use Azure Policy for governance enforcement',
                        'Implement resource locks for all important resources',
                        'Implement proper RBAC'
                    ]
                },
                'availability': {
                    'level': 'moderate',
                    'policies': [
                        'Consider availability zones',
                        'Implement backup strategies'
                    ]
                },
                'cost_optimization': {
                    'level': 'moderate',
                    'policies': [
                        'Use appropriate VM sizes with monitoring',
                        'Implement auto-scaling',
                        'Consider Azure Reserved Instances'
                    ]
                }
            },
            'production': {
                'compliance_level': 'strict',
                'required_policies': 15,  # Maximum compliance required
                'security': {
                    'level': 'strict',
                    'policies': [
                        'Enable encryption at rest and in transit (MANDATORY)',
                        'Use Azure Key Vault for ALL secrets management (MANDATORY)',
                        'Implement multi-factor authentication (MANDATORY)',
                        'Enable Azure Security Center Standard tier (MANDATORY)',
                        'Use managed identities exclusively (MANDATORY)',
                        'Implement Azure Sentinel for SIEM (MANDATORY)',
                        'Enable comprehensive audit logging (MANDATORY)',
                        'Implement security monitoring and alerting (MANDATORY)'
                    ]
                },
                'networking': {
                    'level': 'strict',
                    'policies': [
                        'Use private endpoints for ALL PaaS services (MANDATORY)',
                        'Implement strict network segmentation with NSGs (MANDATORY)',
                        'Use Azure Firewall for centralized traffic filtering (MANDATORY)',
                        'Implement DDoS protection (MANDATORY)',
                        'Use Application Gateway with WAF (MANDATORY)'
                    ]
                },
                'governance': {
                    'level': 'strict',
                    'policies': [
                        'Apply comprehensive resource tagging strategy (MANDATORY)',
                        'Use Azure Policy for strict governance enforcement (MANDATORY)',
                        'Implement resource locks for ALL critical resources (MANDATORY)',
                        'Use Azure Blueprints for consistent deployments (MANDATORY)',
                        'Implement proper RBAC with least privilege (MANDATORY)'
                    ]
                },
                'availability': {
                    'level': 'strict',
                    'policies': [
                        'Implement multi-region deployment (MANDATORY)',
                        'Use availability zones where supported (MANDATORY)',
                        'Implement backup and disaster recovery (MANDATORY)',
                        'Use Azure Site Recovery for business continuity (MANDATORY)'
                    ]
                },
                'cost_optimization': {
                    'level': 'strict',
                    'policies': [
                        'Use appropriate VM sizes with comprehensive monitoring (MANDATORY)',
                        'Implement comprehensive auto-scaling (MANDATORY)',
                        'Use Azure Reserved Instances for stable workloads (MANDATORY)',
                        'Implement Azure Cost Management alerts (MANDATORY)'
                    ]
                }
            }
        }
    
    def _get_environment_policies(self, environment: str) -> Dict[str, List[str]]:
        """Get policies specific to the environment"""
        return self.policy_templates.get(environment.lower(), self.policy_templates['development'])
    
    def _create_compliance_prompt(self, analysis: Dict[str, Any], policies: Dict[str, Any], environment: str) -> str:
        """Create compliance check prompt"""
        
        compliance_level = policies.get('compliance_level', 'basic')
        required_policies = policies.get('required_policies', 5)
        
        prompt = f"""
        Please analyze the following Azure architecture for compliance with Microsoft Azure policies.
        
        ENVIRONMENT: {environment.upper()}
        COMPLIANCE LEVEL: {compliance_level.upper()}
        REQUIRED POLICIES TO PASS: {required_policies}
        
        IMPORTANT: Apply {compliance_level} compliance standards for {environment} environment:
        - DEVELOPMENT: Relaxed standards, focus on basic security and functionality
        - STAGING: Moderate standards, balance between security and development needs  
        - PRODUCTION: STRICT standards, maximum security and compliance required
        
        Architecture Analysis:
        {json.dumps(analysis, indent=2)}
        
        Environment-Specific Policy Requirements:
        {json.dumps(policies, indent=2)}
        
        Please provide a detailed compliance analysis in the following JSON structure:
        {{
            "overall_compliance": {{
                "compliant": boolean,
                "compliance_score": "percentage (0-100)",
                "compliance_level": "{compliance_level}",
                "environment": "{environment}",
                "critical_violations": number,
                "warnings": number,
                "required_policies_met": number,
                "total_required_policies": {required_policies}
            }},
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
    
    def _get_cache_key(self, architecture_analysis, environment):
        """Generate cache key from analysis and environment"""
        key_data = f"{str(architecture_analysis)}{environment}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key):
        """Get cached result if available"""
        return self._cache.get(cache_key)
    
    def _save_to_cache(self, cache_key, result):
        """Save result to cache"""
        if len(self._cache) >= self._max_cache_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[cache_key] = result
