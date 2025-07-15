"""
AI Agent 3: Bicep Generator
Generates Azure Bicep templates and YAML pipelines based on architecture analysis and compliance checks
"""

import json
import os
from typing import Dict, List, Any
import openai
from dotenv import load_dotenv

load_dotenv()

class BicepGenerator:
    def __init__(self):
        # Check if Azure AI Foundry configuration is available
        self.azure_endpoint = os.getenv('AZURE_AI_AGENT3_ENDPOINT')
        self.azure_key = os.getenv('AZURE_AI_AGENT3_KEY')
        self.azure_deployment = os.getenv('AZURE_AI_AGENT3_DEPLOYMENT', 'gpt-4')
        
        if self.azure_endpoint and self.azure_key:
            # Use Azure AI Foundry endpoint
            self.openai_client = openai.AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_key,
                api_version="2024-02-01"
            )
            self.model_name = self.azure_deployment
            print(f"✅ Bicep Generator: Using Azure AI Foundry endpoint")
        else:
            # Fallback to OpenAI
            self.openai_client = openai.OpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
            self.model_name = "gpt-4"
            print(f"⚠️ Bicep Generator: Using OpenAI fallback (configure Azure AI Foundry for production)")
        
        # Load Bicep templates
        self.bicep_templates = self._load_bicep_templates()
    
    def generate_bicep_templates(self, architecture_analysis: Dict[str, Any], policy_compliance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Bicep templates and YAML pipelines based on analysis and compliance
        """
        try:
            # Create generation prompt
            generation_prompt = self._create_generation_prompt(
                architecture_analysis,
                policy_compliance
            )
            
            # Call OpenAI API for Bicep generation
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Azure DevOps engineer and Bicep template specialist. Generate production-ready Bicep templates and Azure DevOps YAML pipelines."
                    },
                    {
                        "role": "user",
                        "content": generation_prompt
                    }
                ],
                temperature=0.1
            )
            
            # Parse generation results
            generation_result = self._parse_generation_response(
                response.choices[0].message.content,
                architecture_analysis,
                policy_compliance
            )
            
            return generation_result
            
        except Exception as e:
            return {
                'error': f'Bicep generation failed: {str(e)}',
                'bicep_templates': {},
                'yaml_pipelines': {},
                'documentation': {}
            }
    
    def _load_bicep_templates(self) -> Dict[str, str]:
        """Load Bicep template snippets"""
        return {
            'resource_group': """
@description('Name of the resource group')
param resourceGroupName string = 'rg-${uniqueString(subscription().id)}'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment (dev, staging, prod)')
param environment string = 'dev'

@description('Common tags for all resources')
param tags object = {
  Environment: environment
  CreatedBy: 'DigitalSuperman'
  Project: 'Infrastructure'
}
""",
            'storage_account': """
@description('Storage account name')
param storageAccountName string = 'st${uniqueString(resourceGroup().id)}'

@description('Storage account type')
param storageAccountType string = 'Standard_LRS'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: storageAccountType
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        file: {
          enabled: true
        }
        blob: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}
""",
            'app_service': """
@description('App Service plan name')
param appServicePlanName string = 'asp-${uniqueString(resourceGroup().id)}'

@description('App Service name')
param appServiceName string = 'app-${uniqueString(resourceGroup().id)}'

@description('App Service plan SKU')
param appServicePlanSku string = 'B1'

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: appServicePlanSku
  }
  kind: 'app'
}

resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: appServiceName
  location: location
  tags: tags
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
    }
  }
}
"""
        }
    
    def _create_generation_prompt(self, analysis: Dict[str, Any], compliance: Dict[str, Any]) -> str:
        """Create Bicep generation prompt"""
        
        prompt = f"""
        Please generate complete Azure Bicep templates and Azure DevOps YAML pipelines based on the following:
        
        Architecture Analysis:
        {json.dumps(analysis, indent=2)}
        
        Policy Compliance Results:
        {json.dumps(compliance, indent=2)}
        
        Please provide the response in the following JSON structure:
        {{
            "bicep_templates": {{
                "main.bicep": "main bicep template content",
                "modules/": {{
                    "network.bicep": "network module content",
                    "compute.bicep": "compute module content",
                    "storage.bicep": "storage module content",
                    "security.bicep": "security module content"
                }},
                "parameters/": {{
                    "dev.parameters.json": "development parameters",
                    "prod.parameters.json": "production parameters"
                }}
            }},
            "yaml_pipelines": {{
                "azure-pipelines.yml": "main pipeline content",
                "pipelines/": {{
                    "build.yml": "build pipeline content",
                    "deploy-dev.yml": "development deployment pipeline",
                    "deploy-prod.yml": "production deployment pipeline"
                }}
            }},
            "documentation": {{
                "README.md": "comprehensive documentation",
                "DEPLOYMENT.md": "deployment instructions",
                "COMPLIANCE.md": "compliance documentation"
            }},
            "scripts": {{
                "deploy.ps1": "PowerShell deployment script",
                "validate.ps1": "PowerShell validation script"
            }}
        }}
        
        Requirements:
        1. Generate production-ready Bicep templates with proper parameterization
        2. Include security best practices from compliance analysis
        3. Create modular Bicep templates for maintainability
        4. Generate Azure DevOps YAML pipelines for CI/CD
        5. Include proper parameter files for different environments
        6. Add comprehensive documentation
        7. Include validation and deployment scripts
        8. Follow Azure Well-Architected Framework principles
        9. Implement all compliance recommendations where possible
        10. Use latest Azure resource API versions
        
        Focus on:
        - Infrastructure as Code best practices
        - Security and compliance requirements
        - Scalability and maintainability
        - Cost optimization
        - Monitoring and logging
        - Disaster recovery considerations
        """
        
        return prompt
    
    def _parse_generation_response(self, response: str, analysis: Dict[str, Any], compliance: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the generation response"""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                generation_data = json.loads(json_match.group())
                generation_data['metadata'] = {
                    'generated_timestamp': self._get_timestamp(),
                    'source_analysis': analysis,
                    'compliance_check': compliance
                }
                return generation_data
            else:
                return self._fallback_generation_parse(response, analysis, compliance)
        except json.JSONDecodeError:
            return self._fallback_generation_parse(response, analysis, compliance)
    
    def _fallback_generation_parse(self, response: str, analysis: Dict[str, Any], compliance: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback parsing for generation response"""
        return {
            'bicep_templates': {
                'main.bicep': self._generate_fallback_bicep(analysis)
            },
            'yaml_pipelines': {
                'azure-pipelines.yml': self._generate_fallback_pipeline()
            },
            'documentation': {
                'README.md': self._generate_fallback_readme()
            },
            'scripts': {
                'deploy.ps1': self._generate_fallback_deploy_script()
            },
            'metadata': {
                'generated_timestamp': self._get_timestamp(),
                'source_analysis': analysis,
                'compliance_check': compliance,
                'parsing_note': 'Used fallback templates due to JSON parsing error'
            },
            'raw_response': response
        }
    
    def _generate_fallback_bicep(self, analysis: Dict[str, Any]) -> str:
        """Generate fallback Bicep template"""
        components = analysis.get('components', [])
        
        bicep_content = """
@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment (dev, staging, prod)')
param environment string = 'dev'

@description('Common tags for all resources')
param tags object = {
  Environment: environment
  CreatedBy: 'DigitalSuperman'
  Project: 'Infrastructure'
}
"""
        
        # Add basic resources based on detected components
        for component in components:
            component_type = component.get('type', '').lower()
            if 'storage' in component_type:
                bicep_content += "\n" + self.bicep_templates['storage_account']
            elif 'app' in component_type or 'web' in component_type:
                bicep_content += "\n" + self.bicep_templates['app_service']
        
        return bicep_content
    
    def _generate_fallback_pipeline(self) -> str:
        """Generate fallback Azure DevOps pipeline"""
        return """
trigger:
  branches:
    include:
    - main
    - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  azureSubscription: 'Azure-Service-Connection'
  resourceGroupName: 'rg-digitalsuperman'
  location: 'East US'

stages:
- stage: Build
  displayName: 'Build and Validate'
  jobs:
  - job: ValidateBicep
    displayName: 'Validate Bicep Templates'
    steps:
    - task: AzureCLI@2
      displayName: 'Validate Bicep Templates'
      inputs:
        azureSubscription: $(azureSubscription)
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          az bicep build --file main.bicep
          az deployment group validate --resource-group $(resourceGroupName) --template-file main.bicep

- stage: Deploy
  displayName: 'Deploy Infrastructure'
  dependsOn: Build
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - deployment: DeployInfrastructure
    displayName: 'Deploy to Azure'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureCLI@2
            displayName: 'Deploy Bicep Templates'
            inputs:
              azureSubscription: $(azureSubscription)
              scriptType: 'bash'
              scriptLocation: 'inlineScript'
              inlineScript: |
                az deployment group create --resource-group $(resourceGroupName) --template-file main.bicep
"""
    
    def _generate_fallback_readme(self) -> str:
        """Generate fallback README"""
        return """
# Digital Superman - Azure Infrastructure

This repository contains the Azure infrastructure templates generated by Digital Superman.

## Overview

This infrastructure was automatically generated based on your Azure architecture diagram analysis.

## Structure

- `main.bicep` - Main Bicep template
- `azure-pipelines.yml` - Azure DevOps CI/CD pipeline
- `deploy.ps1` - PowerShell deployment script

## Deployment

### Prerequisites

- Azure CLI installed and configured
- Azure subscription with appropriate permissions
- Azure DevOps project (for CI/CD)

### Manual Deployment

1. Login to Azure:
   ```bash
   az login
   ```

2. Create resource group:
   ```bash
   az group create --name rg-digitalsuperman --location "East US"
   ```

3. Deploy template:
   ```bash
   az deployment group create --resource-group rg-digitalsuperman --template-file main.bicep
   ```

### CI/CD Deployment

1. Set up Azure DevOps service connection
2. Import the pipeline from `azure-pipelines.yml`
3. Configure pipeline variables
4. Run the pipeline

## Security

This infrastructure follows Azure security best practices and compliance requirements.

## Support

For issues or questions, please refer to the compliance documentation.
"""
    
    def _generate_fallback_deploy_script(self) -> str:
        """Generate fallback deployment script"""
        return """
param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$Location,
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev"
)

# Check if Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI is not installed. Please install Azure CLI first."
    exit 1
}

# Check if logged in to Azure
$account = az account show --query "id" -o tsv
if (-not $account) {
    Write-Host "Not logged in to Azure. Please login first."
    az login
}

# Create resource group if it doesn't exist
Write-Host "Creating resource group: $ResourceGroupName"
az group create --name $ResourceGroupName --location $Location

# Deploy Bicep template
Write-Host "Deploying Bicep template..."
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file main.bicep `
    --parameters environment=$Environment

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
} else {
    Write-Error "Deployment failed!"
    exit 1
}
"""
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_deployment_guide(self, templates: Dict[str, Any]) -> str:
        """Generate deployment guide"""
        guide = """
# Azure Infrastructure Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the generated Azure infrastructure.

## Prerequisites
- Azure CLI 2.0 or later
- Azure subscription with Contributor permissions
- PowerShell 5.1 or later (for Windows users)

## Deployment Steps

### 1. Prepare Environment
```bash
# Login to Azure
az login

# Set subscription (if you have multiple)
az account set --subscription "your-subscription-id"

# Install Bicep CLI
az bicep install
```

### 2. Validate Templates
```bash
# Validate main template
az bicep build --file main.bicep

# Validate deployment (dry run)
az deployment group validate \\
    --resource-group your-rg-name \\
    --template-file main.bicep \\
    --parameters @parameters/dev.parameters.json
```

### 3. Deploy Infrastructure
```bash
# Create resource group
az group create --name your-rg-name --location "East US"

# Deploy template
az deployment group create \\
    --resource-group your-rg-name \\
    --template-file main.bicep \\
    --parameters @parameters/dev.parameters.json
```

### 4. Verify Deployment
```bash
# Check deployment status
az deployment group show \\
    --resource-group your-rg-name \\
    --name main

# List created resources
az resource list --resource-group your-rg-name --output table
```

## Troubleshooting

### Common Issues
1. **Permission Denied**: Ensure you have Contributor role on the subscription
2. **Resource Already Exists**: Use unique names or update existing resources
3. **Quota Exceeded**: Check your Azure quotas and limits

### Validation Commands
```bash
# Check resource health
az resource list --resource-group your-rg-name --query "[].{Name:name,Type:type,Status:properties.provisioningState}" --output table

# View deployment logs
az deployment group show --resource-group your-rg-name --name main --query "properties.error"
```

## Clean Up
```bash
# Delete resource group and all resources
az group delete --name your-rg-name --yes --no-wait
```
"""
        return guide
