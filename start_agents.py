#!/usr/bin/env python3
"""
PACoS Brain Agent Startup Script
Properly starts both agents with correct communication setup
"""

import asyncio
import time
import subprocess
import sys
import os
from pathlib import Path

def start_knowledge_agent():
    """Start the KnowledgeAgent"""
    print("🧠 Starting KnowledgeAgent...")
    try:
        # Start KnowledgeAgent in background
        process = subprocess.Popen([
            sys.executable, "knowledge_agent.py"
        ], cwd=Path(__file__).parent)
        print(f"✅ KnowledgeAgent started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Failed to start KnowledgeAgent: {e}")
        return None

def start_voice_agent():
    """Start the VoiceClientAgent"""
    print("🎤 Starting VoiceClientAgent...")
    try:
        # Start VoiceClientAgent in background
        process = subprocess.Popen([
            sys.executable, "voice_agent.py"
        ], cwd=Path(__file__).parent)
        print(f"✅ VoiceClientAgent started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Failed to start VoiceClientAgent: {e}")
        return None

def main():
    """Main startup function"""
    print("🚀 Starting PACoS Brain Agents...")
    print("=" * 50)
    
    # Start KnowledgeAgent first
    ka_process = start_knowledge_agent()
    if not ka_process:
        print("❌ Failed to start KnowledgeAgent. Exiting.")
        return
    
    # Wait for KnowledgeAgent to initialize
    print("⏳ Waiting for KnowledgeAgent to initialize...")
    time.sleep(3)
    
    # Start VoiceClientAgent
    va_process = start_voice_agent()
    if not va_process:
        print("❌ Failed to start VoiceClientAgent. Exiting.")
        ka_process.terminate()
        return
    
    print("=" * 50)
    print("✅ Both agents started successfully!")
    print("🧠 KnowledgeAgent: Processing queries with LLM reasoning")
    print("🎤 VoiceClientAgent: Handling user input/output")
    print("🔗 A2A Communication: Active")
    print("=" * 50)
    print("Press Ctrl+C to stop both agents")
    
    try:
        # Keep both processes running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if ka_process.poll() is not None:
                print("❌ KnowledgeAgent stopped unexpectedly")
                break
            if va_process.poll() is not None:
                print("❌ VoiceClientAgent stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down agents...")
        ka_process.terminate()
        va_process.terminate()
        print("✅ Agents stopped successfully")

if __name__ == "__main__":
    main()
