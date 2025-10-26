"""
Hybrid Intent Classifier
Fast rule-based pre-check + LLM reasoning for ambiguous queries
"""

import re
import json
import asyncio
from typing import Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class IntentClassifier:
    """Hybrid intent classifier with rule-based pre-check and LLM reasoning"""
    
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Fast rule-based patterns for obvious live queries
        self.LIVE_PATTERNS = [
            r"current \w+ price",
            r"latest \w+ news", 
            r"right now",
            r"today",
            r"currently",
            r"what's happening",
            r"live \w+",
            r"real-time",
            r"stock market",
            r"crypto price",
            r"weather",
            r"breaking news",
            r"price of \w+",
            r"\w+ price",
            r"cost of \w+",
            r"value of \w+"
        ]
        
        # Patterns for obvious knowledge queries
        self.KNOWLEDGE_PATTERNS = [
            r"what is \w+",
            r"define \w+",
            r"explain \w+",
            r"how does \w+ work",
            r"history of \w+",
            r"tell me about \w+",
            r"what are \w+",
            r"difference between"
        ]
    
    def pre_classify(self, query: str) -> str:
        """Fast rule-based pre-classification"""
        query_lower = query.lower()
        
        # Check for obvious live patterns
        for pattern in self.LIVE_PATTERNS:
            if re.search(pattern, query_lower):
                return "LIVE"
        
        # Check for obvious knowledge patterns
        for pattern in self.KNOWLEDGE_PATTERNS:
            if re.search(pattern, query_lower):
                return "KNOWLEDGE"
        
        return "AMBIGUOUS"
    
    async def ask_llm_reasoner(self, query: str) -> Dict[str, Any]:
        """Ask LLMReasoner for ambiguous queries with confidence scoring"""
        
        prompt = f"""You are LLMReasoner, an intelligent reasoning engine that determines whether a user's query requires **real-time live search** or can be answered from **existing knowledge/memory**.

Rules:
1. Queries about current events, prices, live news, "right now", "today", "currently" → LIVE
2. Queries about definitions, explanations, general knowledge, concepts, history → KNOWLEDGE
3. If ambiguous, reason carefully and provide a confidence score (0–1)

Return strictly in JSON format:
{{
  "decision": "LIVE" | "KNOWLEDGE",
  "confidence": 0.0–1.0,
  "reasoning": "1–2 sentence explanation for your decision"
}}

Examples:
Query: "What is the capital of France?"
Output: {{"decision": "KNOWLEDGE", "confidence": 1.0, "reasoning": "Factual question about general knowledge; no live info needed."}}

Query: "Latest AI news today?"
Output: {{"decision": "LIVE", "confidence": 1.0, "reasoning": "Explicitly asks for news from today, requires live info."}}

Query: "Tell me about Bitcoin prices."
Output: {{"decision": "LIVE", "confidence": 0.9, "reasoning": "Asking for current Bitcoin prices implies real-time data."}}

Query: "{query}"
Output:"""

        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text.strip()
            
            # Try to parse JSON response
            try:
                intent_json = json.loads(result_text)
                return intent_json
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                if "LIVE" in result_text.upper():
                    return {"decision": "LIVE", "confidence": 0.7, "reasoning": "LLM indicated live data needed"}
                else:
                    return {"decision": "KNOWLEDGE", "confidence": 0.7, "reasoning": "LLM indicated knowledge response"}
                    
        except Exception as e:
            return {"decision": "KNOWLEDGE", "confidence": 0.5, "reasoning": f"Fallback due to error: {str(e)}"}
    
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """Main hybrid classification method"""
        
        # Phase 1: Fast rule-based pre-check
        rule_decision = self.pre_classify(query)
        
        if rule_decision == "LIVE":
            return {
                "decision": "LIVE", 
                "confidence": 1.0, 
                "reasoning": "Matched rule-based pattern for live data",
                "method": "rule-based"
            }
        elif rule_decision == "KNOWLEDGE":
            return {
                "decision": "KNOWLEDGE", 
                "confidence": 1.0, 
                "reasoning": "Matched rule-based pattern for knowledge",
                "method": "rule-based"
            }
        
        # Phase 2: LLM reasoning for ambiguous queries
        llm_result = await self.ask_llm_reasoner(query)
        llm_result["method"] = "llm-reasoning"
        return llm_result

# Global instance
intent_classifier = IntentClassifier()

async def classify_query_intent(query: str) -> Dict[str, Any]:
    """Convenience function for intent classification"""
    return await intent_classifier.classify_intent(query)

# Test function
async def test_intent_classifier():
    """Test the intent classifier with various queries"""
    test_queries = [
        "What's the current Bitcoin price?",
        "What is the capital of France?", 
        "Latest AI news today?",
        "Tell me about Python programming",
        "What's happening with the stock market?",
        "Explain quantum computing",
        "Current weather in New York",
        "What is MCP (model context protocol)?"
    ]
    
    print("🧪 Testing Intent Classifier")
    print("=" * 60)
    
    for query in test_queries:
        result = await classify_query_intent(query)
        print(f"Query: {query}")
        print(f"Decision: {result['decision']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Method: {result['method']}")
        print(f"Reasoning: {result['reasoning']}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_intent_classifier())
