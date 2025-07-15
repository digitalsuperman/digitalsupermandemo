"""
AI Agent 1: Architecture Analyzer
Analyzes Azure architecture diagrams and extracts components, relationships, and configurations
"""

import json
import re
from typing import Dict, List, Any
import openai
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

class ArchitectureAnalyzer:
    def __init__(self):
        # Check if Azure AI Foundry configuration is available
        self.azure_endpoint = os.getenv('AZURE_AI_AGENT1_ENDPOINT')
        self.azure_key = os.getenv('AZURE_AI_AGENT1_KEY')
        self.azure_deployment = os.getenv('AZURE_AI_AGENT1_DEPLOYMENT', 'gpt-4')
        
        if self.azure_endpoint and self.azure_key:
            # Use Azure AI Foundry endpoint
            self.openai_client = openai.AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_key,
                api_version="2024-02-01"
            )
            self.model_name = self.azure_deployment
            print(f"✅ Architecture Analyzer: Using Azure AI Foundry endpoint")
        else:
            # Fallback to OpenAI
            self.openai_client = openai.OpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
            self.model_name = "gpt-4"
            print(f"⚠️ Architecture Analyzer: Using OpenAI fallback (configure Azure AI Foundry for production)")
        
        # Simple cache for repeated content
        self._cache = {}
        self._max_cache_size = 100  # Limit cache size
    
    def _get_cache_key(self, content):
        """Generate cache key from content"""
        return hashlib.md5(str(content).encode()).hexdigest()
    
    def _get_from_cache(self, cache_key):
        """Get cached result if available"""
        return self._cache.get(cache_key)
    
    def _save_to_cache(self, cache_key, result):
        """Save result to cache"""
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[cache_key] = result

    def analyze_architecture(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the extracted architecture diagram content
        """
        # Check cache first
        cache_key = self._get_cache_key(extracted_content)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            print("📋 Architecture Analyzer: Using cached result")
            return cached_result
        
        try:
            # Prepare the prompt for OpenAI
            analysis_prompt = self._create_analysis_prompt(extracted_content)
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Azure architect. Analyze the provided architecture diagram and extract all Azure components, their configurations, and relationships."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.1
            )
            
            # Parse the response
            analysis_result = self._parse_analysis_response(response.choices[0].message.content)
            
            # Save to cache
            self._save_to_cache(cache_key, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            return {
                'error': f'Architecture analysis failed: {str(e)}',
                'components': [],
                'relationships': [],
                'configurations': {}
            }
    
    def _create_analysis_prompt(self, content: Dict[str, Any]) -> str:
        """Create a detailed prompt for architecture analysis"""
        
        prompt = f"""
        Please analyze the following Azure architecture diagram content and provide a structured analysis:

        Content Type: {content.get('type', 'unknown')}
        Text Content: {content.get('text', 'No text found')}
        Metadata: {json.dumps(content.get('metadata', {}), indent=2)}
        
        Please provide the analysis in the following JSON structure:
        {{
            "components": [
                {{
                    "name": "component_name",
                    "type": "azure_service_type",
                    "configuration": {{
                        "sku": "service_tier",
                        "region": "azure_region",
                        "settings": {{}}
                    }},
                    "dependencies": ["dependent_component_names"]
                }}
            ],
            "relationships": [
                {{
                    "source": "source_component",
                    "target": "target_component",
                    "type": "relationship_type",
                    "configuration": {{}}
                }}
            ],
            "network_topology": {{
                "vnets": [],
                "subnets": [],
                "nsgs": [],
                "routing": []
            }},
            "security_configuration": {{
                "authentication": [],
                "authorization": [],
                "encryption": []
            }},
            "estimated_costs": {{
                "monthly_estimate": "TBD",
                "cost_factors": []
            }}
        }}
        
        Focus on identifying:
        1. Azure services (VMs, Storage, Databases, App Services, etc.)
        2. Network components (VNets, Subnets, Load Balancers, etc.)
        3. Security components (Key Vault, NSGs, App Gateway, etc.)
        4. Data flow and dependencies
        5. Configuration details where visible
        """
        
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the OpenAI response into structured format"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing if JSON not found
                return self._fallback_parse(response)
        except json.JSONDecodeError:
            return self._fallback_parse(response)
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails"""
        return {
            'components': [],
            'relationships': [],
            'network_topology': {},
            'security_configuration': {},
            'estimated_costs': {},
            'raw_analysis': response,
            'parsing_note': 'Used fallback parsing due to JSON parsing error'
        }
    
    def get_component_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of analyzed components"""
        components = analysis.get('components', [])
        
        summary = {
            'total_components': len(components),
            'service_types': {},
            'regions': set(),
            'dependencies_count': 0
        }
        
        for component in components:
            service_type = component.get('type', 'unknown')
            if service_type in summary['service_types']:
                summary['service_types'][service_type] += 1
            else:
                summary['service_types'][service_type] = 1
            
            region = component.get('configuration', {}).get('region')
            if region:
                summary['regions'].add(region)
            
            dependencies = component.get('dependencies', [])
            summary['dependencies_count'] += len(dependencies)
        
        summary['regions'] = list(summary['regions'])
        return summary
