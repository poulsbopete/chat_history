#!/usr/bin/env python3

import os
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False
    return True

def setup_env_file():
    """Setup environment file"""
    env_file = ".env"
    env_example = ".env.example"
    
    if os.path.exists(env_file):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists(env_example):
        print("📝 Creating .env file from .env.example")
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("⚠️  Please edit .env file with your actual API keys:")
        print("   - OPENAI_API_KEY")
        print("   - ANTHROPIC_API_KEY") 
        print("   - GOOGLE_API_KEY")
        print("   - ELASTICSEARCH_URL")
        print("   - ELASTICSEARCH_API_KEY")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def main():
    print("🚀 Setting up AI Chat History application...")
    
    if not install_requirements():
        sys.exit(1)
    
    if not setup_env_file():
        sys.exit(1)
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: python chat_history.py")
    print("3. For MCP server: python mcp_server.py")

if __name__ == "__main__":
    main()