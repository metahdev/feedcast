"""
Fact-checking module for podcast content validation.
Provides multi-source validation and claim verification using Claude AI.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .types import Source, FactCheck, VerificationStatus
from .claude_service import ClaudePodcastService

# Configure logging
logger = logging.getLogger(__name__)


class FactChecker:
    """
    Fact-checking service for podcast content validation.
    
    Uses Claude AI to analyze claims across multiple sources and determine
    verification status, confidence levels, and source agreement.
    """
    
    def __init__(self, claude_service: ClaudePodcastService):
        """
        Initialize the fact checker.
        
        Args:
            claude_service: Claude service instance for AI analysis
        """
        self.claude = claude_service
        logger.info("FactChecker initialized")
    
    async def extract_claims(self, sources: List[Source]) -> List[str]:
        """
        Extract factual claims from sources using Claude.
        
        Args:
            sources: List of sources to analyze
            
        Returns:
            List of extracted factual claims
            
        Raises:
            ValueError: If sources list is empty
            Exception: If claim extraction fails
        """
        if not sources:
            raise ValueError("Sources list cannot be empty")
        
        logger.info(f"Extracting claims from {len(sources)} sources")
        
        try:
            # Prepare source content for analysis
            source_content = []
            for i, source in enumerate(sources):
                source_info = {
                    "index": i,
                    "title": source.title,
                    "publication": source.publication,
                    "url": source.url,
                    "summary": source.content_summary,
                    "credibility_score": source.credibility_score
                }
                source_content.append(source_info)
            
            # Create prompt for claim extraction
            extraction_prompt = f"""Analyze the following sources and extract all factual claims that can be verified or disputed.

Sources:
{json.dumps(source_content, indent=2)}

For each source, identify:
1. Specific factual statements
2. Statistical claims
3. Historical facts
4. Scientific claims
5. Current events
6. Expert opinions presented as facts

Return a JSON array of claims, where each claim is a clear, verifiable statement.
Format: ["claim1", "claim2", "claim3", ...]

Focus on claims that are:
- Specific and measurable
- Potentially verifiable through other sources
- Important for understanding the topic
- Not subjective opinions or speculation"""

            messages = [{"role": "user", "content": extraction_prompt}]
            
            response = await self.claude.generate_completion(
                messages=messages,
                max_tokens=3000,
                temperature=0.3  # Lower temperature for more consistent extraction
            )
            
            # Parse the JSON response
            try:
                claims = json.loads(response)
                if not isinstance(claims, list):
                    raise ValueError("Response is not a list")
                
                # Clean and validate claims
                cleaned_claims = []
                for claim in claims:
                    if isinstance(claim, str) and claim.strip():
                        cleaned_claims.append(claim.strip())
                
                logger.info(f"Extracted {len(cleaned_claims)} claims from sources")
                return cleaned_claims
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse claims JSON: {e}")
                # Fallback: extract claims from text response
                return self._extract_claims_from_text(response)
                
        except Exception as e:
            logger.error(f"Failed to extract claims: {str(e)}")
            raise
    
    async def validate_claim(
        self, 
        claim: str, 
        sources: List[Source]
    ) -> FactCheck:
        """
        Validate a claim across multiple sources using Claude.
        
        Args:
            claim: The factual claim to validate
            sources: List of sources to check against
            
        Returns:
            FactCheck object with validation results
            
        Raises:
            ValueError: If claim is empty or sources list is empty
            Exception: If validation fails
        """
        if not claim or not claim.strip():
            raise ValueError("Claim cannot be empty")
        
        if not sources:
            raise ValueError("Sources list cannot be empty")
        
        logger.info(f"Validating claim: {claim[:100]}...")
        
        try:
            # Prepare source information for analysis
            source_analysis = []
            for i, source in enumerate(sources):
                source_info = {
                    "index": i,
                    "title": source.title,
                    "publication": source.publication,
                    "url": source.url,
                    "summary": source.content_summary,
                    "credibility_score": source.credibility_score,
                    "published_date": source.published_date.isoformat() if source.published_date else None
                }
                source_analysis.append(source_info)
            
            # Create comprehensive validation prompt
            validation_prompt = f"""Analyze the following claim against multiple sources to determine its accuracy and verification status.

CLAIM TO VALIDATE: "{claim}"

SOURCES TO CHECK:
{json.dumps(source_analysis, indent=2)}

For each source, determine:
1. Does this source SUPPORT the claim?
2. Does this source CONTRADICT the claim?
3. Does this source provide NEUTRAL/INSUFFICIENT information?
4. What is the source's credibility level?

Based on your analysis, provide a JSON response with:
{{
    "claim": "{claim}",
    "confidence": "high|medium|low",
    "verification_status": "verified|partially_verified|unverified|disputed",
    "supporting_sources": [list of source indices that support the claim],
    "contradicting_sources": [list of source indices that contradict the claim],
    "neutral_sources": [list of source indices with neutral/insufficient info],
    "analysis": "Detailed explanation of the validation reasoning",
    "notes": "Additional context or limitations"
}}

Confidence levels:
- HIGH: Multiple credible sources agree, claim is well-supported
- MEDIUM: Some sources support, some are neutral, or limited sources
- LOW: Contradictory sources, low credibility sources, or insufficient evidence

Verification status:
- VERIFIED: Claim is supported by credible sources
- PARTIALLY_VERIFIED: Claim is partially supported or has some limitations
- UNVERIFIED: Insufficient evidence to determine accuracy
- DISPUTED: Sources contradict each other or claim is disputed"""

            messages = [{"role": "user", "content": validation_prompt}]
            
            response = await self.claude.generate_completion(
                messages=messages,
                max_tokens=4000,
                temperature=0.2  # Very low temperature for consistent validation
            )
            
            # Parse the validation response
            try:
                validation_data = json.loads(response)
                
                # Map confidence string to numeric value
                confidence_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
                confidence = confidence_map.get(validation_data.get("confidence", "low"), 0.3)
                
                # Map verification status
                status_map = {
                    "verified": VerificationStatus.VERIFIED,
                    "partially_verified": VerificationStatus.PARTIALLY_VERIFIED,
                    "unverified": VerificationStatus.UNVERIFIED,
                    "disputed": VerificationStatus.DISPUTED
                }
                verification_status = status_map.get(
                    validation_data.get("verification_status", "unverified"),
                    VerificationStatus.UNVERIFIED
                )
                
                # Get relevant sources based on validation results
                supporting_indices = validation_data.get("supporting_sources", [])
                contradicting_indices = validation_data.get("contradicting_sources", [])
                
                relevant_sources = []
                for idx in supporting_indices + contradicting_indices:
                    if 0 <= idx < len(sources):
                        relevant_sources.append(sources[idx])
                
                # Create FactCheck object
                fact_check = FactCheck(
                    claim=claim,
                    confidence=confidence,
                    verification_status=verification_status,
                    sources=relevant_sources,
                    notes=validation_data.get("notes", "")
                )
                
                logger.info(f"Claim validation completed: {verification_status.value} (confidence: {confidence})")
                return fact_check
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse validation JSON: {e}")
                # Fallback: create basic fact check
                return self._create_fallback_fact_check(claim, sources)
                
        except Exception as e:
            logger.error(f"Failed to validate claim '{claim}': {str(e)}")
            raise
    
    async def validate_all_claims(self, sources: List[Source]) -> List[FactCheck]:
        """
        Validate all claims extracted from sources.
        
        Args:
            sources: List of sources to analyze
            
        Returns:
            List of FactCheck objects for all validated claims
            
        Raises:
            Exception: If validation process fails
        """
        if not sources:
            raise ValueError("Sources list cannot be empty")
        
        logger.info(f"Starting comprehensive fact-checking of {len(sources)} sources")
        
        try:
            # Step 1: Extract all claims
            claims = await self.extract_claims(sources)
            
            if not claims:
                logger.warning("No claims extracted from sources")
                return []
            
            # Step 2: Validate each claim
            fact_checks = []
            for i, claim in enumerate(claims):
                try:
                    logger.info(f"Validating claim {i+1}/{len(claims)}: {claim[:50]}...")
                    fact_check = await self.validate_claim(claim, sources)
                    fact_checks.append(fact_check)
                    
                    # Add small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to validate claim {i+1}: {str(e)}")
                    # Create a fallback fact check for failed validations
                    fallback_check = FactCheck(
                        claim=claim,
                        confidence=0.0,
                        verification_status=VerificationStatus.UNVERIFIED,
                        sources=[],
                        notes=f"Validation failed: {str(e)}"
                    )
                    fact_checks.append(fallback_check)
            
            # Step 3: Sort by confidence and verification status
            fact_checks.sort(
                key=lambda x: (x.confidence, x.verification_status.value),
                reverse=True
            )
            
            logger.info(f"Fact-checking completed: {len(fact_checks)} claims validated")
            return fact_checks
            
        except Exception as e:
            logger.error(f"Failed to validate all claims: {str(e)}")
            raise
    
    def _extract_claims_from_text(self, text: str) -> List[str]:
        """
        Fallback method to extract claims from text response.
        
        Args:
            text: Raw text response from Claude
            
        Returns:
            List of extracted claims
        """
        logger.warning("Using fallback claim extraction from text")
        
        # Simple extraction logic - look for numbered items or bullet points
        lines = text.split('\n')
        claims = []
        
        for line in lines:
            line = line.strip()
            # Look for numbered items (1., 2., etc.) or bullet points (-, •)
            if (line and 
                (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or
                 line.startswith(('-', '•', '*')))):
                # Remove numbering/bullets and clean
                claim = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                if claim:
                    claims.append(claim)
        
        return claims[:10]  # Limit to 10 claims for fallback
    
    def _create_fallback_fact_check(
        self, 
        claim: str, 
        sources: List[Source]
    ) -> FactCheck:
        """
        Create a fallback fact check when JSON parsing fails.
        
        Args:
            claim: The claim to check
            sources: Available sources
            
        Returns:
            Basic FactCheck object
        """
        logger.warning(f"Creating fallback fact check for claim: {claim[:50]}...")
        
        return FactCheck(
            claim=claim,
            confidence=0.0,
            verification_status=VerificationStatus.UNVERIFIED,
            sources=[],
            notes="Validation failed - using fallback result"
        )
    
    async def get_validation_summary(self, fact_checks: List[FactCheck]) -> Dict[str, Any]:
        """
        Generate a summary of fact-checking results.
        
        Args:
            fact_checks: List of completed fact checks
            
        Returns:
            Summary statistics and insights
        """
        if not fact_checks:
            return {"total_claims": 0, "summary": "No claims to analyze"}
        
        # Calculate statistics
        total_claims = len(fact_checks)
        verified_count = sum(1 for fc in fact_checks if fc.verification_status == VerificationStatus.VERIFIED)
        disputed_count = sum(1 for fc in fact_checks if fc.verification_status == VerificationStatus.DISPUTED)
        unverified_count = sum(1 for fc in fact_checks if fc.verification_status == VerificationStatus.UNVERIFIED)
        
        avg_confidence = sum(fc.confidence for fc in fact_checks) / total_claims
        
        # Find most/least confident claims
        most_confident = max(fact_checks, key=lambda x: x.confidence)
        least_confident = min(fact_checks, key=lambda x: x.confidence)
        
        summary = {
            "total_claims": total_claims,
            "verified_claims": verified_count,
            "disputed_claims": disputed_count,
            "unverified_claims": unverified_count,
            "average_confidence": round(avg_confidence, 3),
            "verification_rate": round(verified_count / total_claims, 3),
            "most_confident_claim": {
                "claim": most_confident.claim,
                "confidence": most_confident.confidence,
                "status": most_confident.verification_status.value
            },
            "least_confident_claim": {
                "claim": least_confident.claim,
                "confidence": least_confident.confidence,
                "status": least_confident.verification_status.value
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Validation summary: {verified_count}/{total_claims} claims verified")
        return summary
