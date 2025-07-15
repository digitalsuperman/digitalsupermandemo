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
            # First, validate if this is an Azure architecture
            validation_result = self._validate_azure_architecture(extracted_content)
            
            if not validation_result['is_azure_architecture']:
                return {
                    'error': 'non_azure_architecture',
                    'error_message': validation_result['error_message'],
                    'detected_platforms': validation_result.get('detected_platforms', []),
                    'suggestion': validation_result.get('suggestion', 'Please upload an Azure architecture diagram.')
                }
            
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
    
    def _validate_azure_architecture(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if the uploaded architecture contains Azure resources
        """
        try:
            # Get the text content for analysis
            content_text = ""
            content_type = extracted_content.get('type', 'unknown')
            
            if 'text' in extracted_content:
                content_text = extracted_content['text']
            elif 'content' in extracted_content:
                content_text = str(extracted_content['content'])
            
            # Special handling for image files
            if content_type == 'image':
                # For images, we have limited text content, so we need to be more permissive
                # but still check for obvious non-Azure indicators
                image_text = content_text.lower()
                
                # Check if image metadata or filename contains clear non-Azure indicators
                metadata = extracted_content.get('metadata', {})
                filename = metadata.get('filename', '').lower()
                
                # Strong indicators of non-Azure platforms
                strong_non_azure_indicators = ['aws', 'amazon', 'gcp', 'google cloud', 'oracle cloud']
                
                # Check filename and available text
                all_text = f"{image_text} {filename}".lower()
                
                for indicator in strong_non_azure_indicators:
                    if indicator in all_text:
                        platform_name = {
                            'aws': 'AWS',
                            'amazon': 'AWS', 
                            'gcp': 'Google Cloud',
                            'google cloud': 'Google Cloud',
                            'oracle cloud': 'Oracle Cloud'
                        }.get(indicator, 'Non-Azure')
                        
                        return {
                            'is_azure_architecture': False,
                            'error_message': f"❌ We only support Azure architecture diagrams. This appears to be a {platform_name} architecture based on the filename or content. Please upload an Azure-specific architecture diagram.",
                            'detected_platforms': [platform_name],
                            'confidence_score': 0.8,
                            'suggestion': "Upload an architecture diagram that primarily uses Azure services like Virtual Machines, App Service, Storage Accounts, SQL Database, etc."
                        }
                
                # For images without clear indicators, we'll allow processing but warn about limitations
                print(f"⚠️ Image file detected - limited validation possible. Proceeding with analysis...")
                return {
                    'is_azure_architecture': True,
                    'confidence_score': 0.5,
                    'note': 'Image file - limited validation performed based on filename only'
                }
            
            # Regular text-based validation for non-image files
            if not content_text.strip():
                # Empty content - let it proceed but with low confidence
                return {
                    'is_azure_architecture': True,
                    'confidence_score': 0.3,
                    'note': 'Empty content detected - validation skipped'
                }
            
            # Create validation prompt
            validation_prompt = f"""
Analyze the following architecture diagram content and determine:
1. Is this primarily an Azure cloud architecture? 
2. What cloud platforms/services are mentioned?
3. Are there any non-Azure cloud services (AWS, GCP, Oracle, etc.)?

Content to analyze:
{content_text[:2000]}  # Limit for faster analysis

Respond in JSON format:
{{
    "is_azure_architecture": true/false,
    "confidence_score": 0.0-1.0,
    "azure_services_found": ["list of Azure services"],
    "non_azure_services_found": ["list of non-Azure services"],
    "detected_platforms": ["Azure", "AWS", "GCP", etc.],
    "primary_platform": "dominant platform name"
}}
"""
            
            # Call OpenAI for validation
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use faster model for validation
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cloud architecture expert. Identify cloud platforms and services in architecture diagrams."
                    },
                    {
                        "role": "user", 
                        "content": validation_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse validation response
            validation_result = self._parse_validation_response(response.choices[0].message.content)
            
            # Determine if this is acceptable Azure architecture
            is_azure = validation_result.get('is_azure_architecture', False)
            confidence = validation_result.get('confidence_score', 0.0)
            non_azure_services = validation_result.get('non_azure_services_found', [])
            detected_platforms = validation_result.get('detected_platforms', [])
            primary_platform = validation_result.get('primary_platform', 'Unknown')
            
            # Create error message if not Azure architecture
            if not is_azure or confidence < 0.6:
                error_message = "❌ We only support Azure architecture diagrams."
                
                if non_azure_services:
                    error_message += f" Detected non-Azure services: {', '.join(non_azure_services[:3])}."
                
                if primary_platform and primary_platform.lower() != 'azure':
                    error_message += f" This appears to be a {primary_platform} architecture."
                
                error_message += " Please upload an Azure-specific architecture diagram."
                
                return {
                    'is_azure_architecture': False,
                    'error_message': error_message,
                    'detected_platforms': detected_platforms,
                    'confidence_score': confidence,
                    'suggestion': "Upload an architecture diagram that primarily uses Azure services like Virtual Machines, App Service, Storage Accounts, SQL Database, etc."
                }
            
            return {
                'is_azure_architecture': True,
                'confidence_score': confidence,
                'azure_services_found': validation_result.get('azure_services_found', [])
            }
            
        except Exception as e:
            print(f"⚠️ Validation error: {str(e)}")
            
            # Check if this was an image file that failed validation
            content_type = extracted_content.get('type', 'unknown')
            if content_type == 'image':
                return {
                    'is_azure_architecture': False,
                    'error_message': "❌ Unable to validate image content. For image files, please ensure the filename clearly indicates it's an Azure architecture (e.g., 'azure-architecture.png') or use text-based formats like .drawio, .svg, or .xml for better validation.",
                    'detected_platforms': ['Unknown'],
                    'confidence_score': 0.0,
                    'suggestion': "Consider using Draw.io (.drawio), SVG, or other text-based diagram formats for better validation, or ensure your image filename contains 'azure' to indicate it's an Azure architecture."
                }
            
            # For non-image files, use fallback method
            fallback_result = self._fallback_validation(content_text if 'content_text' in locals() else str(extracted_content))
            return fallback_result
    
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse the validation response from OpenAI"""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: analyze text content for cloud services
                return self._fallback_validation(response)
        except json.JSONDecodeError:
            return self._fallback_validation(response)
    
    def _fallback_validation(self, response: str) -> Dict[str, Any]:
        """Fallback validation using keyword matching"""
        response_lower = response.lower()
        
        # Azure service keywords
        azure_keywords = [
            'azure', 'microsoft', 'app service', 'virtual machine', 'vm', 'storage account',
            'sql database', 'cosmos db', 'key vault', 'application gateway', 'load balancer',
            'virtual network', 'subnet', 'resource group', 'subscription', 'tenant'
        ]
        
        # Non-Azure cloud keywords
        non_azure_keywords = [
            'aws', 'amazon', 'ec2', 's3', 'lambda', 'rds', 'dynamo',
            'google cloud', 'gcp', 'compute engine', 'cloud storage', 'big query',
            'oracle cloud', 'oci', 'heroku', 'digitalocean', 'alibaba cloud'
        ]
        
        azure_count = sum(1 for keyword in azure_keywords if keyword in response_lower)
        non_azure_count = sum(1 for keyword in non_azure_keywords if keyword in response_lower)
        
        is_azure = azure_count > non_azure_count and azure_count > 0
        confidence = min(azure_count / max(azure_count + non_azure_count, 1), 1.0)
        
        detected_platforms = []
        if azure_count > 0:
            detected_platforms.append('Azure')
        if 'aws' in response_lower or 'amazon' in response_lower:
            detected_platforms.append('AWS')
        if 'google cloud' in response_lower or 'gcp' in response_lower:
            detected_platforms.append('Google Cloud')
        
        return {
            'is_azure_architecture': is_azure,
            'confidence_score': confidence,
            'azure_services_found': [kw for kw in azure_keywords if kw in response_lower],
            'non_azure_services_found': [kw for kw in non_azure_keywords if kw in response_lower],
            'detected_platforms': detected_platforms,
            'primary_platform': 'Azure' if is_azure else (detected_platforms[0] if detected_platforms else 'Unknown')
        }
