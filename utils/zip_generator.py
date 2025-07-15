"""
ZIP generator utility to create downloadable packages
"""

import os
import zipfile
import json
import tempfile
from typing import Dict, Any
from datetime import datetime

class ZipGenerator:
    def __init__(self):
        self.output_dir = 'output'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_zip_package(self, 
                          bicep_templates: Dict[str, Any], 
                          architecture_analysis: Dict[str, Any],
                          policy_compliance: Dict[str, Any],
                          environment: str) -> str:
        """Create a ZIP package with all generated content"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"digital_superman_{environment}_{timestamp}.zip"
        zip_filepath = os.path.join(self.output_dir, zip_filename)
        
        try:
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add Bicep templates
                self._add_bicep_templates(zipf, bicep_templates, environment)
                
                # Add YAML pipelines
                self._add_yaml_pipelines(zipf, bicep_templates, environment)
                
                # Add scripts
                self._add_scripts(zipf, bicep_templates, environment)
                
                # Add simplified documentation (only 2 files)
                self._add_simplified_documentation(zipf, policy_compliance, environment)
            
            return zip_filename
            
        except Exception as e:
            raise Exception(f"Failed to create ZIP package: {str(e)}")
    
    def _add_bicep_templates(self, zipf: zipfile.ZipFile, templates: Dict[str, Any], environment: str):
        """Add Bicep templates to ZIP"""
        bicep_templates = templates.get('bicep_templates', {})
        
        for template_name, template_content in bicep_templates.items():
            if template_name.endswith('/'):
                # Handle directory structure
                continue
            
            if isinstance(template_content, dict):
                # Handle nested structure like modules/
                for sub_name, sub_content in template_content.items():
                    if isinstance(sub_content, str):
                        zipf.writestr(f"bicep/{template_name}/{sub_name}", sub_content)
            else:
                zipf.writestr(f"bicep/{template_name}", template_content)
        
        # Handle modules directory
        modules = bicep_templates.get('modules/', {})
        for module_name, module_content in modules.items():
            zipf.writestr(f"bicep/modules/{module_name}", module_content)
        
        # Handle parameters directory - only include environment-specific parameters
        parameters = bicep_templates.get('parameters/', {})
        for param_name, param_content in parameters.items():
            # Only include parameters for the target environment
            if environment in param_name or not any(env in param_name for env in ['dev', 'staging', 'prod']):
                zipf.writestr(f"bicep/parameters/{param_name}", param_content)
    
    def _add_yaml_pipelines(self, zipf: zipfile.ZipFile, templates: Dict[str, Any], environment: str):
        """Add environment-specific YAML pipelines to ZIP"""
        yaml_pipelines = templates.get('yaml_pipelines', {})
        
        for pipeline_name, pipeline_content in yaml_pipelines.items():
            # Only include pipelines that match the target environment or are generic
            if environment in pipeline_name or 'azure-pipelines.' in pipeline_name:
                if isinstance(pipeline_content, dict):
                    # Handle nested structure like pipelines/
                    for sub_name, sub_content in pipeline_content.items():
                        if isinstance(sub_content, str) and (environment in sub_name or 'main' in sub_name):
                            zipf.writestr(f"pipelines/{sub_name}", sub_content)
                else:
                    zipf.writestr(f"pipelines/{pipeline_name}", pipeline_content)
    
    def _add_simplified_documentation(self, zipf: zipfile.ZipFile, compliance: Dict[str, Any], environment: str):
        """Add only essential documentation - Policy Compliance Report and README"""
        
        # 1. Policy Compliance Report with table format (includes auto-fix info)
        compliance_report = self._generate_policy_compliance_table(compliance, environment)
        zipf.writestr("POLICY_COMPLIANCE_REPORT.md", compliance_report)
        
        # 2. Auto-fix summary if fixes were applied
        if compliance.get('fixes_applied'):
            autofix_report = self._generate_autofix_summary(compliance.get('fixes_applied', []))
            zipf.writestr("AUTOFIX_SUMMARY.md", autofix_report)
        
        # 3. Simple README with usage instructions
        readme = self._generate_simple_readme()
        zipf.writestr("README.md", readme)
    
    def _generate_policy_compliance_table(self, compliance: Dict[str, Any], environment: str) -> str:
        """Generate a clean policy compliance report with tables"""
        
        overall = compliance.get('overall_compliance', {})
        violations = compliance.get('violations', [])
        recommendations = compliance.get('recommendations', [])
        fixes_applied = compliance.get('fixes_applied', [])
        post_fix_compliance = compliance.get('post_fix_compliance', {})
        
        # Use post-fix compliance if available
        if post_fix_compliance:
            overall = post_fix_compliance.get('overall_compliance', overall)
            remaining_violations = post_fix_compliance.get('violations', [])
        else:
            remaining_violations = violations
        
        report = f"""# Policy Compliance Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Environment:** {environment.title()}  
**Compliance Status:** {'✅ COMPLIANT' if overall.get('compliant', False) else '❌ NON-COMPLIANT'}  
**Compliance Score:** {overall.get('compliance_score', 'Unknown')}
**Auto-Fixes Applied:** {len(fixes_applied)} {'🔧' if fixes_applied else ''}

---

## 📊 Compliance Summary

| Metric | Original | After Auto-Fix | Status |
|--------|----------|----------------|--------|
| 🔴 Critical Violations | {len([v for v in violations if v.get('severity') == 'critical'])} | {len([v for v in remaining_violations if v.get('severity') == 'critical'])} | {'✅ Improved' if len(fixes_applied) > 0 else '❌ Action Required' if len(remaining_violations) > 0 else '✅ Clean'} |
| 🟡 Warnings | {len([v for v in violations if v.get('severity') in ['medium', 'warning']])} | {len([v for v in remaining_violations if v.get('severity') in ['medium', 'warning']])} | {'✅ Improved' if len(fixes_applied) > 0 else '⚠️ Review Needed' if len(remaining_violations) > 0 else '✅ Clean'} |
| 💡 Recommendations | {len(recommendations)} | {len(recommendations)} | {'📝 Available' if len(recommendations) > 0 else '✅ None'} |
| 📋 Total Issues | {len(violations)} | {len(remaining_violations)} | {'� Auto-Fixed' if len(fixes_applied) > 0 else '�🔍 Review Required' if len(remaining_violations) > 0 else '✅ All Clear'} |

---

"""

        # Auto-fix summary section
        if fixes_applied:
            report += f"""## 🔧 Auto-Fix Summary

**{len(fixes_applied)} violations were automatically resolved:**

| Component | Fix Applied | Status |
|-----------|-------------|--------|
"""
            for fix in fixes_applied:
                component = fix.get('component', 'Unknown')
                fix_desc = fix.get('fix_applied', 'Security enhancement applied')
                report += f"| {component} | {fix_desc} | ✅ Fixed |\n"
            
            report += "\n💡 *See AUTOFIX_SUMMARY.md for detailed fix information*\n\n---\n\n"

        if remaining_violations:
            report += """## 🚨 Remaining Policy Violations

| Severity | Component | Category | Issue | Recommendation |
|----------|-----------|----------|-------|----------------|
"""
            for violation in remaining_violations:
                severity_icon = {
                    'critical': '🔴',
                    'high': '🟠', 
                    'medium': '🟡',
                    'low': '🟢',
                    'info': 'ℹ️'
                }.get(violation.get('severity', 'unknown').lower(), '❓')
                
                component = violation.get('component', 'Unknown')[:30]
                category = violation.get('category', 'Unknown')[:20]
                description = violation.get('description', 'No description')[:50] + ('...' if len(violation.get('description', '')) > 50 else '')
                recommendation = violation.get('recommendation', 'No recommendation')[:60] + ('...' if len(violation.get('recommendation', '')) > 60 else '')
                
                report += f"| {severity_icon} {violation.get('severity', 'Unknown').title()} | `{component}` | {category} | {description} | {recommendation} |\n"
            
            report += "\n---\n\n"
        else:
            report += """## ✅ Policy Violations

No policy violations detected! Your architecture follows Azure best practices.

---

"""

        if recommendations:
            report += """## 💡 Optimization Recommendations

| Priority | Component | Category | Recommendation | Implementation |
|----------|-----------|----------|----------------|----------------|
"""
            for rec in recommendations:
                priority_icon = {
                    'high': '🔴',
                    'medium': '🟡', 
                    'low': '🟢'
                }.get(rec.get('priority', 'unknown').lower(), '📌')
                
                component = rec.get('component', 'Unknown')[:25]
                category = rec.get('category', 'Unknown')[:20]
                description = rec.get('description', 'No description')[:45] + ('...' if len(rec.get('description', '')) > 45 else '')
                implementation = rec.get('implementation', 'No details')[:50] + ('...' if len(rec.get('implementation', '')) > 50 else '')
                
                report += f"| {priority_icon} {rec.get('priority', 'Unknown').title()} | `{component}` | {category} | {description} | {implementation} |\n"
            
            report += "\n---\n\n"
        else:
            report += """## 💡 Optimization Recommendations

No additional recommendations at this time. Your architecture is well-optimized!

---

"""

        report += """## 📋 Next Steps

1. **Address Critical Issues** - Fix any critical violations immediately
2. **Review Warnings** - Evaluate warnings and apply fixes where appropriate  
3. **Implement Recommendations** - Consider optimization suggestions for better performance
4. **Deploy Infrastructure** - Use the provided Bicep templates and pipelines
5. **Monitor Compliance** - Regularly review your infrastructure against Azure policies

## 🔗 Additional Resources

- [Azure Policy Documentation](https://docs.microsoft.com/en-us/azure/governance/policy/)
- [Azure Well-Architected Framework](https://docs.microsoft.com/en-us/azure/architecture/framework/)
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)

---

*Report generated by Digital Superman - Azure Architecture to Infrastructure Code*
"""
        
        return report
    
    def _generate_simple_readme(self) -> str:
        """Generate a simple README with usage instructions"""
        return """# Digital Superman - Infrastructure Code Package

🚀 **Ready-to-deploy Azure infrastructure code generated from your architecture diagram**

## 📦 Package Contents

```
├── bicep/                     # 🏗️ Bicep Infrastructure Templates
│   ├── main.bicep            # Main deployment template
│   ├── modules/              # Reusable modules
│   └── parameters/           # Environment-specific parameters
├── pipelines/                # 🔄 Azure DevOps CI/CD Pipelines
│   └── azure-pipelines.yml  # Complete deployment pipeline
├── scripts/                  # 🛠️ PowerShell Deployment Scripts
│   ├── deploy.ps1           # One-click deployment
│   └── validate.ps1         # Template validation
├── POLICY_COMPLIANCE_REPORT.md  # 📋 Security & compliance analysis
├── AUTOFIX_SUMMARY.md        # 🔧 Auto-applied security fixes (if any)
└── README.md                 # 📖 This file
```

## 🚀 Quick Start (3 Steps)

### Step 1: Review Compliance & Auto-Fixes
```bash
# Check the compliance report first
cat POLICY_COMPLIANCE_REPORT.md

# If auto-fixes were applied, review them
cat AUTOFIX_SUMMARY.md
```

### Step 2: Deploy Infrastructure
```powershell
# Option A: One-click deployment script
cd scripts
./deploy.ps1 -ResourceGroupName "my-rg" -Location "East US"

# Option B: Manual Azure CLI deployment
az deployment group create \
  --resource-group my-rg \
  --template-file bicep/main.bicep \
  --parameters @bicep/parameters/dev.parameters.json
```

### Step 3: Set Up CI/CD Pipeline
```yaml
# Import pipelines/azure-pipelines.yml into Azure DevOps
# Configure service connections and run the pipeline
```

## ⚙️ Customization

### Environment Parameters
Edit parameter files for your environment:
- `bicep/parameters/dev.parameters.json` - Development
- `bicep/parameters/prod.parameters.json` - Production

### Common Customizations
```json
{
  "location": "East US",
  "resourcePrefix": "myapp",
  "environment": "dev",
  "skuSize": "Standard"
}
```

## 🔧 Prerequisites

- **Azure CLI** - [Install here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- **Bicep CLI** - Run `az bicep install`
- **PowerShell** - For deployment scripts
- **Azure Subscription** - With appropriate permissions

## 🛡️ Security Notes

🔧 **Auto-Fix Information:**
- Policy violations are automatically fixed when possible
- Review AUTOFIX_SUMMARY.md to understand applied changes
- Auto-fixes follow Azure security best practices
- Manual review is still recommended for production deployments

⚠️ **Before deployment:**
- Review all generated templates
- Update default passwords in parameter files
- Configure proper access controls
- Enable monitoring and logging

## 📞 Support

**Need help?**
1. Check `POLICY_COMPLIANCE_REPORT.md` for known issues
2. Validate templates: `./scripts/validate.ps1`
3. Review Azure documentation links in the compliance report

---

*Generated by Digital Superman v1.0.0*  
*Transform your Azure architecture diagrams into production-ready infrastructure code*
"""
    
    def _add_scripts(self, zipf: zipfile.ZipFile, templates: Dict[str, Any], environment: str):
        """Add environment-specific scripts to ZIP"""
        scripts = templates.get('scripts', {})
        
        for script_name, script_content in scripts.items():
            # Only include scripts for the target environment
            if environment in script_name or 'main' in script_name or not any(env in script_name for env in ['dev', 'staging', 'prod']):
                zipf.writestr(f"scripts/{script_name}", script_content)
    
    def _generate_deploy_script(self) -> str:
        """Generate deployment script"""
        return """param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$Location,
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$TemplateFile = "../bicep/main.bicep",
    
    [Parameter(Mandatory=$false)]
    [string]$ParametersFile = "../bicep/parameters/$Environment.parameters.json"
)

Write-Host "🚀 Digital Superman - Infrastructure Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Azure CLI not found. Please install Azure CLI."
    exit 1
}

if (-not (Get-Command bicep -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Bicep CLI..." -ForegroundColor Yellow
    az bicep install
}

# Create resource group if it doesn't exist
Write-Host "Creating resource group: $ResourceGroupName" -ForegroundColor Green
az group create --name $ResourceGroupName --location $Location

# Validate template
Write-Host "Validating Bicep template..." -ForegroundColor Green
$validationResult = az deployment group validate `
    --resource-group $ResourceGroupName `
    --template-file $TemplateFile `
    --parameters @$ParametersFile `
    --output json | ConvertFrom-Json

if ($validationResult.error) {
    Write-Error "❌ Template validation failed:"
    Write-Error $validationResult.error.message
    exit 1
}

Write-Host "✅ Template validation successful!" -ForegroundColor Green

# Deploy infrastructure
Write-Host "Deploying infrastructure..." -ForegroundColor Green
$deploymentResult = az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file $TemplateFile `
    --parameters @$ParametersFile `
    --output json | ConvertFrom-Json

if ($deploymentResult.properties.provisioningState -eq "Succeeded") {
    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Cyan
    Write-Host "Location: $Location" -ForegroundColor Cyan
    Write-Host "Environment: $Environment" -ForegroundColor Cyan
} else {
    Write-Error "❌ Deployment failed!"
    Write-Error $deploymentResult.properties.error.message
    exit 1
}
"""

    def _generate_validation_script(self) -> str:
        """Generate validation script"""
        return """param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$TemplateFile = "../bicep/main.bicep",
    
    [Parameter(Mandatory=$false)]
    [string]$ParametersFile = "../bicep/parameters/dev.parameters.json"
)

Write-Host "🔍 Digital Superman - Template Validation" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if Azure CLI is available
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Azure CLI not found. Please install Azure CLI."
    exit 1
}

# Check if Bicep CLI is available
if (-not (Get-Command bicep -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Bicep CLI..." -ForegroundColor Yellow
    az bicep install
}

# Validate Bicep syntax
Write-Host "Validating Bicep syntax..." -ForegroundColor Green
bicep build $TemplateFile

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Bicep syntax validation failed!"
    exit 1
}

# Validate ARM template
Write-Host "Validating ARM template..." -ForegroundColor Green
$validationResult = az deployment group validate `
    --resource-group $ResourceGroupName `
    --template-file $TemplateFile `
    --parameters @$ParametersFile `
    --output json | ConvertFrom-Json

if ($validationResult.error) {
    Write-Error "❌ ARM template validation failed:"
    Write-Error $validationResult.error.message
    exit 1
}

Write-Host "✅ Validation completed successfully!" -ForegroundColor Green
Write-Host "Templates are ready for deployment." -ForegroundColor Green
"""
