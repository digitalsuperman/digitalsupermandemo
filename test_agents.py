#!/usr/bin/env python3
"""
Test script to verify Azure AI Foundry agent connectivity
"""

import os
import sys
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

def test_agent(agent_name, endpoint_var, key_var, deployment_var):
    """Test connectivity to a specific Azure AI agent"""
    print(f"\n🧪 Testing {agent_name}...")
    
    endpoint = os.getenv(endpoint_var)
    key = os.getenv(key_var)
    deployment = os.getenv(deployment_var, 'gpt-4')
    
    if not endpoint or not key:
        print(f"❌ {agent_name}: Missing configuration")
        print(f"   Endpoint: {'✅' if endpoint else '❌'} {endpoint_var}")
        print(f"   Key: {'✅' if key else '❌'} {key_var}")
        return False
    
    try:
        # Extract base endpoint from full URL if needed
        if "/chat/completions" in endpoint:
            base_endpoint = endpoint.split("/openai/deployments")[0] + "/"
        else:
            base_endpoint = endpoint
            
        print(f"   🔗 Endpoint: {base_endpoint}")
        print(f"   🔑 Key: {key[:8]}...{key[-8:] if len(key) > 16 else key}")
        print(f"   🤖 Deployment: {deployment}")
        
        # Create Azure OpenAI client
        client = openai.AzureOpenAI(
            azure_endpoint=base_endpoint,
            api_key=key,
            api_version="2024-02-01"
        )
        
        # Test with a simple request
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Hello! Please respond with 'Connection successful' if you can read this."
                }
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        print(f"   ✅ {agent_name}: Connection successful!")
        print(f"   📝 Response: {result}")
        return True
        
    except Exception as e:
        print(f"   ❌ {agent_name}: Connection failed")
        print(f"   🚨 Error: {str(e)}")
        return False

def main():
    """Test all three Azure AI agents"""
    print("🚀 Digital Superman - Azure AI Foundry Agent Connectivity Test")
    print("=" * 60)
    
    # Test each agent
    agents = [
        ("Architecture Analyzer", "AZURE_AI_AGENT1_ENDPOINT", "AZURE_AI_AGENT1_KEY", "AZURE_AI_AGENT1_DEPLOYMENT"),
        ("Policy Checker", "AZURE_AI_AGENT2_ENDPOINT", "AZURE_AI_AGENT2_KEY", "AZURE_AI_AGENT2_DEPLOYMENT"),
        ("Bicep Generator", "AZURE_AI_AGENT3_ENDPOINT", "AZURE_AI_AGENT3_KEY", "AZURE_AI_AGENT3_DEPLOYMENT")
    ]
    
    results = []
    for agent_name, endpoint_var, key_var, deployment_var in agents:
        success = test_agent(agent_name, endpoint_var, key_var, deployment_var)
        results.append((agent_name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("-" * 30)
    
    all_success = True
    for agent_name, success in results:
        status = "✅ Connected" if success else "❌ Failed"
        print(f"   {agent_name}: {status}")
        if not success:
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("🎉 All agents are connected and ready!")
        print("✅ Your Digital Superman app can now use Azure AI Foundry!")
    else:
        print("⚠️  Some agents failed to connect.")
        print("Please check your .env configuration and Azure AI Foundry setup.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
