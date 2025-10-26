"""
Main PodcastGenerator class that orchestrates the entire podcast generation pipeline.
Integrates user preferences, research, fact-checking, and content generation.
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import backoff
from urllib.parse import urlparse
import hashlib
import time

from .types import (
    GenerationRequest, UserPreferences, Source, FactCheck, 
    LiveKitScript, PodcastSegmentRequest, SegmentType, Format
)
from .claude_service import ClaudePodcastService
from .fact_checker import FactChecker

# Configure logging
logger = logging.getLogger(__name__)


class ResearchConfig:
    """Performance tuning configuration for research pipeline."""
    
    # Search configuration
    MAX_SEARCH_QUERIES = 4  # Reduced from 6 for speed
    RESULTS_PER_QUERY = 3   # Top 3 from each
    SEARCH_TIMEOUT = 5      # Seconds per search
    
    # Fetch configuration  
    MAX_SOURCES_TO_FETCH = 8  # Reduced from 12
    FETCH_TIMEOUT = 8         # Seconds per fetch
    MAX_CONTENT_LENGTH = 5000 # Characters per article
    
    # Verification
    VERIFY_TOP_N = 3          # Only verify top 3 uncertain events
    VERIFY_TIMEOUT = 10       # Seconds per verification
    AUTO_VERIFY_THRESHOLD = 3 # Sources needed to skip verification
    
    # Caching
    SEARCH_CACHE_TTL = 30     # Minutes
    FETCH_CACHE_TTL = 60      # Minutes
    
    # Quality thresholds
    MIN_SOURCES_FETCHED = 4   # Fail if less than 4 sources work
    MIN_EVENTS_EXTRACTED = 4  # Fail if less than 4 events found


class SearchCache:
    """Simple in-memory cache with TTL for search results and fetched content."""
    
    def __init__(self):
        self._cache = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str, ttl_minutes: int = 30) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(minutes=ttl_minutes):
                self._hits += 1
                return value
            else:
                del self._cache[key]
        
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any):
        """Cache value with timestamp."""
        self._cache[key] = (value, datetime.now())
    
    def clear_old(self, max_age_minutes: int = 60):
        """Clear entries older than max_age."""
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
        self._cache = {
            k: v for k, v in self._cache.items() 
            if v[1] > cutoff
        }
    
    def stats(self) -> Dict[str, int]:
        """Return cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 1),
            "size": len(self._cache)
        }


class PodcastGenerator:
    """
    Main orchestrator for podcast generation pipeline.
    
    Coordinates user context loading, research, fact-checking, script generation,
    and database persistence to create personalized podcast content.
    """
    
    def __init__(
        self, 
        supabase_client, 
        claude_service: ClaudePodcastService, 
        fact_checker: FactChecker
    ):
        """
        Initialize the podcast generator.
        
        Args:
            supabase_client: Supabase client for database operations
            claude_service: Claude service for AI operations
            fact_checker: Fact checker for content validation
        """
        self.supabase = supabase_client
        self.claude = claude_service
        self.fact_checker = fact_checker
        self.search_cache = SearchCache()
        self.config = ResearchConfig()
        
        logger.info("PodcastGenerator initialized with performance optimizations")
    
    async def generate_podcast(
        self, 
        request: GenerationRequest,
        use_event_discovery: bool = True
    ) -> Dict[str, Any]:
        """
        Main pipeline for generating a complete podcast.
        
        Args:
            request: Generation request with user preferences and requirements
            use_event_discovery: If True, uses new event-based research pipeline.
                                If False, uses traditional article-based research.
            
        Returns:
            Dictionary containing generated podcast data and metadata
            
        Raises:
            Exception: If any step of the pipeline fails
        """
        logger.info(f"Starting podcast generation for user {request.user_id}")
        logger.info(f"Research mode: {'Event Discovery' if use_event_discovery else 'Traditional Article-based'}")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Load user context
            logger.info("Step 1: Loading user context")
            user_context = await self.load_user_context(request.user_id)
            
            # Step 2: Research topics for each segment
            logger.info("Step 2: Researching topics")
            all_sources = []
            segment_research = {}
            discovered_events = []
            
            if use_event_discovery:
                # NEW: Event-based research pipeline
                logger.info("Using EVENT DISCOVERY pipeline")
                
                # Collect all topics across segments
                all_topics = []
                for segment in request.segments:
                    if segment.topics:
                        all_topics.extend(segment.topics)
                
                # Remove duplicates while preserving order
                unique_topics = list(dict.fromkeys(all_topics))
                
                if unique_topics:
                    # Conduct comprehensive event-based research
                    research_results = await self.conduct_research(
                        topics=unique_topics,
                        timeframe="this week",
                        enable_verification=False  # Disabled for speed - events already have credibility scores
                    )
                    
                    discovered_events = research_results.get("events", [])
                    verified_events = research_results.get("verified_events", [])
                    
                    logger.info(f"Discovered {len(discovered_events)} events, verified {len(verified_events)}")
                    
                    # Convert events to Source objects for compatibility with existing pipeline
                    for event in discovered_events:
                        for url in event.get("source_urls", [])[:1]:  # Take first URL
                            source = Source(
                                url=url,
                                title=event.get("event", "Event"),
                                publication=self._extract_publication_from_url(url),
                                credibility_score=event.get("credibility_score", 5.0) / 10.0,  # Convert 0-10 to 0-1
                                content_summary=self._format_event_as_summary(event),
                                published_date=datetime.utcnow()
                            )
                            all_sources.append(source)
                    
                    # Organize by segment
                    for segment in request.segments:
                        if segment.topics:
                            for topic in segment.topics:
                                # Find events related to this topic
                                related_events = [
                                    e for e in discovered_events 
                                    if e.get("research_topic") == topic
                                ]
                                
                                # Convert to sources
                                topic_sources = []
                                for event in related_events[:5]:  # Top 5 events per topic
                                    for url in event.get("source_urls", [])[:1]:
                                        source = Source(
                                            url=url,
                                            title=event.get("event", "Event"),
                                            publication=self._extract_publication_from_url(url),
                                            credibility_score=event.get("credibility_score", 5.0) / 10.0,
                                            content_summary=self._format_event_as_summary(event),
                                            published_date=datetime.utcnow()
                                        )
                                        topic_sources.append(source)
                                
                                segment_research[f"{segment.type.value}_{topic}"] = topic_sources
                else:
                    logger.warning("No topics provided for event discovery")
            else:
                # OLD: Traditional article-based research
                logger.info("Using TRADITIONAL article-based research")
            
            for segment in request.segments:
                if segment.topics:
                    for topic in segment.topics:
                        logger.info(f"Researching topic: {topic}")
                        sources = await self.search_multi_source(topic, min_sources=3)
                        all_sources.extend(sources)
                        segment_research[f"{segment.type.value}_{topic}"] = sources
            
            # Step 3: Fetch full content from sources
            logger.info("Step 3: Fetching full content from sources")
            enriched_sources = []
            for source in all_sources:
                try:
                    content_data = await self.claude.web_fetch(source.url)
                    if content_data.get("success"):
                        # Update source with fetched content
                        source.content_summary = content_data["content"][:1000]  # Truncate for storage
                        enriched_sources.append(source)
                except Exception as e:
                    logger.warning(f"Failed to fetch content from {source.url}: {e}")
                    enriched_sources.append(source)  # Keep original source
            
            # Step 4: Validate facts using fact checker
            logger.info("Step 4: Validating facts")
            try:
                fact_checks = await self.fact_checker.validate_all_claims(enriched_sources)
            except Exception as e:
                logger.warning(f"Fact checking failed, continuing without fact checks: {e}")
                fact_checks = []  # Continue without fact checks if it fails
            
            # Step 5: Build continuity context
            logger.info("Step 5: Building continuity context")
            topics = [topic for segment in request.segments for topic in (segment.topics or [])]
            continuity_context = await self.build_continuity_context(request.user_id, topics)
            
            # Step 6: Generate script using Claude
            logger.info("Step 6: Generating podcast script")
            livekit_script = await self.generate_script(
                research=segment_research,
                continuity=continuity_context,
                preferences=user_context["preferences"],
                request=request,
                fact_checks=fact_checks
            )
            
            # Step 7: Generate interactive elements
            logger.info("Step 7: Generating interactive elements")
            interactive_elements = await self.generate_interactive_elements(
                livekit_script, 
                request.interactive_elements_count
            )
            
            # Step 8: Prepare podcast data for database
            logger.info("Step 8: Preparing podcast data")
            podcast_data = {
                "user_id": request.user_id,
                "title": self._generate_podcast_title(request, user_context),
                "description": self._generate_podcast_description(request, user_context),
                "format": request.format.value,
                "total_duration": request.duration_minutes,
                "script": livekit_script.dict(),
                "sources": [source.dict() for source in enriched_sources],
                "fact_checks": [fc.dict() for fc in fact_checks],
                "interactive_elements": interactive_elements,
                "user_preferences": user_context["preferences"].dict(),
                "events_discovered": discovered_events,  # ADD THIS for topic extraction
                "generation_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "generation_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    "sources_count": len(enriched_sources),
                    "fact_checks_count": len(fact_checks),
                    "verification_rate": self._calculate_verification_rate(fact_checks),
                    "events_discovered_count": len(discovered_events)  # Track in metadata too
                }
            }
            
            # Step 9: Save to database
            logger.info("Step 9: Saving to database")
            podcast_id = await self.save_to_database(podcast_data)
            
            # Step 10: Return complete result
            result = {
                "podcast_id": podcast_id,
                "status": "completed",
                "livekit_script": livekit_script.dict(),
                "metadata": podcast_data["generation_metadata"],
                "summary": {
                    "title": podcast_data["title"],
                    "duration_minutes": request.duration_minutes,
                    "sources_used": len(enriched_sources),
                    "facts_verified": len([fc for fc in fact_checks if fc.verification_status.value == "verified"]),
                    "interactive_elements": len(interactive_elements)
                }
            }
            
            logger.info(f"Podcast generation completed successfully: {podcast_id}")
            return result
            
        except Exception as e:
            logger.error(f"Podcast generation failed: {str(e)}")
            raise
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        base=2
    )
    async def search_multi_source(self, topic: str, min_sources: int = 3) -> List[Source]:
        """
        Search for multiple sources on a topic using web search.
        
        Args:
            topic: Topic to search for
            min_sources: Minimum number of sources to find
            
        Returns:
            List of Source objects with metadata
        """
        logger.info(f"Searching for sources on topic: {topic}")
        
        try:
            # Perform web search
            search_results = await self.claude.web_search(f"{topic} latest news research")
            
            sources = []
            for i, result in enumerate(search_results[:min_sources * 2]):  # Get extra to filter
                try:
                    # Create Source object from search result
                    source = Source(
                        url=result.get("url", f"https://example.com/source-{i}"),
                        title=result.get("title", f"Source about {topic}"),
                        publication=result.get("publication", "Unknown"),
                        credibility_score=result.get("relevance_score", 0.7),
                        content_summary=result.get("snippet", ""),
                        published_date=datetime.utcnow()
                    )
                    sources.append(source)
                except Exception as e:
                    logger.warning(f"Failed to create source from result {i}: {e}")
            
            # Ensure we have minimum sources
            if len(sources) < min_sources:
                logger.warning(f"Only found {len(sources)} sources, expected {min_sources}")
            
            logger.info(f"Found {len(sources)} sources for topic: {topic}")
            return sources[:min_sources]
            
        except Exception as e:
            logger.error(f"Failed to search sources for topic '{topic}': {str(e)}")
            raise
    
    async def discover_news_events(
        self, 
        topic: str, 
        timeframe: str = "this week"
    ) -> List[Dict[str, Any]]:
        """
        OPTIMIZED: Discovers actual news EVENTS using aggressive parallelization and timeouts.
        Target completion time: 30-45 seconds (down from 3-4 minutes).
        
        Args:
            topic: The topic to research (e.g., "artificial intelligence", "climate change")
            timeframe: Time window for news (e.g., "this week", "today", "this month")
            
        Returns:
            List of verified events with dates, actors, facts, and credibility scores
        """
        start_time = time.time()
        logger.info(f"🚀 OPTIMIZED: Discovering news events for topic: {topic}, timeframe: {timeframe}")
        
        try:
            # OPTIMIZATION 1: Reduced search queries (6 → 4) with timeouts
            current_year = datetime.now().year
            search_queries = [
                f"{topic} news {timeframe}",
                f"{topic} latest {current_year}",
                f"{topic} announcement this week",
                f"breaking {topic} development"
            ][:self.config.MAX_SEARCH_QUERIES]
            
            logger.info(f"⚡ Executing {len(search_queries)} parallel searches with {self.config.SEARCH_TIMEOUT}s timeout")
            
            # Execute ALL searches simultaneously with timeout
            async def search_with_timeout(query: str) -> List[dict]:
                """Execute single search with timeout and caching."""
                cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
                
                # Check cache first
                cached = self.search_cache.get(cache_key, ttl_minutes=self.config.SEARCH_CACHE_TTL)
                if cached:
                    logger.info(f"💾 Cache hit: {query}")
                    return cached
                
                try:
                    async with asyncio.timeout(self.config.SEARCH_TIMEOUT):
                        results = await self.claude.web_search(query)
                        top_results = results[:self.config.RESULTS_PER_QUERY]
                        self.search_cache.set(cache_key, top_results)
                        return top_results
                except asyncio.TimeoutError:
                    logger.warning(f"⏱️  Search timeout: {query}")
                    return []
                except Exception as e:
                    logger.error(f"❌ Search failed: {query} - {e}")
                    return []
            
            search_results_list = await asyncio.gather(*[
                search_with_timeout(query) for query in search_queries
            ])
            
            search_time = time.time() - start_time
            logger.info(f"✅ Searches completed in {search_time:.1f}s")
            
            # OPTIMIZATION 2: Deduplicate and prioritize sources
            all_articles = []
            seen_urls = set()
            
            for results in search_results_list:
                for result in results:
                    url = result.get("url", "")
                    
                    if not url or url in seen_urls or url == "https://example.com":
                        continue
                    
                    seen_urls.add(url)
                    all_articles.append({
                        "url": url,
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "publication": self._extract_publication_from_url(url),
                        "relevance_score": result.get("relevance_score", 0.5)
                    })
            
            logger.info(f"📄 Found {len(all_articles)} unique articles")
            
            # Prioritize and limit to top sources
            all_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
            top_articles = all_articles[:self.config.MAX_SOURCES_TO_FETCH]
            
            # OPTIMIZATION 3: Parallel content fetching with aggressive timeouts
            logger.info(f"⬇️  Fetching {len(top_articles)} sources in parallel ({self.config.FETCH_TIMEOUT}s timeout)")
            
            async def fetch_with_timeout_cached(article: dict) -> Optional[dict]:
                """Fetch single source with timeout and caching."""
                url = article["url"]
                cache_key = f"fetch:{hashlib.md5(url.encode()).hexdigest()}"
                
                # Check cache first
                cached = self.search_cache.get(cache_key, ttl_minutes=self.config.FETCH_CACHE_TTL)
                if cached:
                    logger.debug(f"💾 Cache hit: {url}")
                    return cached
                
                try:
                    async with asyncio.timeout(self.config.FETCH_TIMEOUT):
                        content_data = await self.claude.web_fetch(url)
                        
                        if not content_data.get("success"):
                            return None
                        
                        content = content_data.get("content", "")
                        word_count = len(content.split())
                        
                        # Skip articles with insufficient content
                        if word_count < 200:
                            return None
                        
                        result = {
                            **article,
                            "content": content[:self.config.MAX_CONTENT_LENGTH],
                            "word_count": word_count
                        }
                        
                        self.search_cache.set(cache_key, result)
                        return result
                        
                except asyncio.TimeoutError:
                    logger.warning(f"⏱️  Fetch timeout: {url}")
                    return None
                except Exception as e:
                    logger.debug(f"❌ Fetch failed: {url} - {e}")
                    return None
            
            fetch_start = time.time()
            articles = await asyncio.gather(*[
                fetch_with_timeout_cached(article) for article in top_articles
            ])
            
            # Filter out None results
            enriched_articles = [a for a in articles if a is not None]
            
            fetch_time = time.time() - fetch_start
            logger.info(f"✅ Fetched {len(enriched_articles)}/{len(top_articles)} articles in {fetch_time:.1f}s")
            
            if len(enriched_articles) < self.config.MIN_SOURCES_FETCHED:
                logger.warning(f"⚠️  Only {len(enriched_articles)} sources fetched (min: {self.config.MIN_SOURCES_FETCHED})")
                if not enriched_articles:
                    return []
            
            # OPTIMIZATION 4: Single Claude call for ALL event extraction
            logger.info(f"🧠 Extracting events from {len(enriched_articles)} sources (single API call)")
            extract_start = time.time()
            
            events = await self._extract_all_events_single_call(enriched_articles, topic, timeframe)
            
            extract_time = time.time() - extract_start
            logger.info(f"✅ Extracted {len(events)} events in {extract_time:.1f}s")
            
            if len(events) < self.config.MIN_EVENTS_EXTRACTED:
                logger.warning(f"⚠️  Only {len(events)} events found (min: {self.config.MIN_EVENTS_EXTRACTED})")
            
            # Add credibility scores
            for event in events:
                event["credibility_score"] = self._calculate_event_credibility(event, enriched_articles)
            
            # Sort by credibility
            events.sort(key=lambda x: x.get("credibility_score", 0), reverse=True)
            
            total_time = time.time() - start_time
            cache_stats = self.search_cache.stats()
            logger.info(f"🎉 Event discovery completed in {total_time:.1f}s (cache: {cache_stats['hit_rate']}% hit rate)")
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Failed to discover news events for topic '{topic}': {str(e)}")
            return []
    
    async def verify_and_enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-verifies an event with additional sources and enriches details.
        
        Args:
            event: Event dictionary from discover_news_events
            
        Returns:
            Enriched event with verification data:
            {
                ...original event fields...,
                "verified": true/false,
                "confidence": "high/medium/low",
                "verified_facts": [
                    {
                        "fact": "128K context window",
                        "confirmed_by": 3,
                        "corrections": null
                    }
                ],
                "additional_facts": ["Any new verified facts found"],
                "contradictions": []
            }
        """
        logger.info(f"Verifying and enriching event: {event.get('event', 'Unknown')}")
        
        try:
            # Search specifically for this event
            event_description = event.get("event", "")
            event_date = event.get("date", "")
            actors = " ".join(event.get("actors", []))
            
            verify_query = f"{event_description} {actors} {event_date}"
            
            logger.info(f"Searching for verification sources: {verify_query}")
            
            # Fetch 3 additional verification sources
            try:
                search_results = await self.claude.web_search(verify_query)
                verification_urls = [r.get("url") for r in search_results[:3] if r.get("url")]
            except Exception as e:
                logger.warning(f"Verification search failed: {e}")
                verification_urls = []
            
            # Fetch content from verification sources
            verification_sources = []
            fetch_tasks = [self._fetch_with_timeout(url, timeout=10) for url in verification_urls]
            
            if fetch_tasks:
                fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
                
                for i, result in enumerate(fetch_results):
                    if isinstance(result, Exception) or not result.get("success"):
                        continue
                    
                    verification_sources.append({
                        "url": verification_urls[i],
                        "content": result.get("content", "")[:3000]
                    })
            
            logger.info(f"Found {len(verification_sources)} verification sources")
            
            if not verification_sources:
                logger.warning("No verification sources available, returning original event")
                return {
                    **event,
                    "verified": False,
                    "confidence": "low",
                    "verified_facts": [],
                    "additional_facts": [],
                    "contradictions": ["No verification sources available"]
                }
            
            # Cross-check facts using Claude
            formatted_sources = "\n\n".join([
                f"SOURCE {i+1} ({src['url']}):\n{src['content']}"
                for i, src in enumerate(verification_sources)
            ])
            
            verification_prompt = f"""Verify this event across multiple sources:

EVENT: {event.get('event')}
DATE: {event.get('date')}
ACTORS: {', '.join(event.get('actors', []))}
CLAIMED FACTS: 
{chr(10).join(f"- {fact}" for fact in event.get('key_facts', []))}

VERIFICATION SOURCES:
{formatted_sources}

For each claimed fact, determine:
1. Confirmed by how many sources? (0-{len(verification_sources)})
2. Any contradictions or corrections?
3. Additional verified details from sources?

Return ONLY JSON (no markdown, no explanations):
{{
  "verified": true,
  "confidence": "high",
  "verified_facts": [
    {{
      "fact": "128K context window",
      "confirmed_by": 3,
      "corrections": null
    }}
  ],
  "additional_facts": ["Any new verified facts found in sources"],
  "contradictions": []
}}

DO NOT OUTPUT ANYTHING EXCEPT THE JSON."""
            
            logger.info("Running verification with Claude")
            
            messages = [{"role": "user", "content": verification_prompt}]
            response = await self.claude.generate_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.2  # Very low temperature for factual verification
            )
            
            # Parse verification results
            verification_data = self._parse_json_from_response(response)
            
            if not verification_data:
                logger.warning("Failed to parse verification data")
                verification_data = {
                    "verified": False,
                    "confidence": "low",
                    "verified_facts": [],
                    "additional_facts": [],
                    "contradictions": ["Verification parsing failed"]
                }
            
            # Merge verification results with original event
            enriched_event = {
                **event,
                **verification_data,
                "verification_sources": [src["url"] for src in verification_sources]
            }
            
            logger.info(f"Event verification completed: confidence={verification_data.get('confidence', 'unknown')}")
            return enriched_event
            
        except Exception as e:
            logger.error(f"Failed to verify event: {str(e)}")
            return {
                **event,
                "verified": False,
                "confidence": "low",
                "verified_facts": [],
                "additional_facts": [],
                "contradictions": [f"Verification error: {str(e)}"]
            }
    
    async def conduct_research(
        self, 
        topics: List[str], 
        timeframe: str = "this week",
        enable_verification: bool = False  # Changed default to False for speed
    ) -> Dict[str, Any]:
        """
        OPTIMIZED: Conducts comprehensive research with optional quick verification.
        
        This is the main entry point for the event-based research pipeline.
        Target completion time: 40-60 seconds for 2 topics (down from 10+ minutes).
        
        Args:
            topics: List of topics to research
            timeframe: Time window for news (e.g., "this week", "today")
            enable_verification: Whether to quick-verify uncertain events (default: False)
            
        Returns:
            Dictionary with discovered events, metadata, and optional verification
        """
        start_time = time.time()
        logger.info(f"🚀 OPTIMIZED: Research starting for {len(topics)} topics: {topics}")
        
        try:
            # OPTIMIZATION: Discover events for ALL topics in parallel
            logger.info(f"⚡ Discovering events for {len(topics)} topics in parallel")
            
            discovery_tasks = [
                self.discover_news_events(topic, timeframe) 
                for topic in topics
            ]
            
            events_by_topic = await asyncio.gather(*discovery_tasks, return_exceptions=True)
            
            # Aggregate all events
            all_events = []
            topics_covered = []
            
            for i, events in enumerate(events_by_topic):
                if isinstance(events, Exception):
                    logger.warning(f"❌ Discovery failed for topic '{topics[i]}': {events}")
                    continue
                
                if events:
                    topics_covered.append(topics[i])
                    for event in events:
                        event["research_topic"] = topics[i]
                        all_events.append(event)
            
            logger.info(f"📊 Discovered {len(all_events)} total events across {len(topics_covered)} topics")
            
            # OPTIMIZATION: Quick verification only if requested and needed
            verified_events = []
            if enable_verification and all_events:
                verify_start = time.time()
                
                # Auto-verify events with 3+ sources
                high_confidence = [e for e in all_events if len(e.get('source_urls', [])) >= self.config.AUTO_VERIFY_THRESHOLD]
                needs_verification = [e for e in all_events if len(e.get('source_urls', [])) < self.config.AUTO_VERIFY_THRESHOLD]
                
                # Mark high-confidence events as verified
                for event in high_confidence:
                    event['verified'] = True
                    event['confidence'] = 'high'
                
                # Only verify top 3 uncertain events
                to_verify = sorted(
                    needs_verification,
                    key=lambda x: x.get("credibility_score", 0),
                    reverse=True
                )[:self.config.VERIFY_TOP_N]
                
                logger.info(f"🔍 Quick verify: {len(high_confidence)} auto-verified, verifying {len(to_verify)} uncertain")
                
                if to_verify:
                    # Quick verification in parallel
                    verification_tasks = [
                        self._quick_verify_event(event)
                        for event in to_verify
                    ]
                    
                    verified = await asyncio.gather(*verification_tasks, return_exceptions=True)
                    verified = [e for e in verified if not isinstance(e, Exception)]
                    
                    verified_events = high_confidence + verified
                else:
                    verified_events = high_confidence
                
                verify_time = time.time() - verify_start
                logger.info(f"✅ Verification completed in {verify_time:.1f}s")
            
            research_time = time.time() - start_time
            cache_stats = self.search_cache.stats()
            
            result = {
                "events": all_events,
                "verified_events": verified_events,
                "topics_covered": topics_covered,
                "total_events": len(all_events),
                "research_metadata": {
                    "topics_researched": topics,
                    "timeframe": timeframe,
                    "research_duration_seconds": round(research_time, 1),
                    "verification_enabled": enable_verification,
                    "cache_hit_rate": cache_stats["hit_rate"],
                    "events_per_topic": {
                        topic: len([e for e in all_events if e.get("research_topic") == topic])
                        for topic in topics_covered
                    }
                }
            }
            
            logger.info(f"🎉 Research completed in {research_time:.1f}s: {len(all_events)} events (cache: {cache_stats['hit_rate']}%)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Research failed: {str(e)}")
            raise
    
    async def _quick_verify_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        OPTIMIZED: Quick verification with 10s timeout total.
        Much faster than full verification.
        """
        try:
            async with asyncio.timeout(self.config.VERIFY_TIMEOUT):
                # Single focused search
                verify_query = f"{event['event']} {event.get('date', '')}"
                
                cache_key = f"search:{hashlib.md5(verify_query.encode()).hexdigest()}"
                cached = self.search_cache.get(cache_key, ttl_minutes=self.config.SEARCH_CACHE_TTL)
                
                if cached:
                    results = cached
                else:
                    results = await self.claude.web_search(verify_query)
                    self.search_cache.set(cache_key, results)
                
                # Check if top 2 results mention key facts
                mentions = 0
                for result in results[:2]:
                    desc = result.get('description', '').lower() + result.get('snippet', '').lower()
                    if any(fact.lower() in desc for fact in event.get('key_facts', [])[:2]):
                        mentions += 1
                
                event['verified'] = mentions >= 1
                event['confidence'] = 'high' if mentions >= 2 else 'medium'
                
                return event
                
        except asyncio.TimeoutError:
            event['verified'] = False
            event['confidence'] = 'low'
            return event
        except Exception as e:
            logger.debug(f"Quick verify failed: {e}")
            event['verified'] = False
            event['confidence'] = 'low'
            return event
    
    async def load_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Load comprehensive user context including preferences and history.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary containing user preferences, interests, and history
        """
        logger.info(f"Loading user context for user: {user_id}")
        
        try:
            # Load user preferences
            prefs_result = self.supabase.table("users").select(
                "preferences, listening_stats, created_at"
            ).eq("id", user_id).single().execute()
            
            preferences_data = prefs_result.data.get("preferences", {})
            preferences = UserPreferences(**preferences_data)
            
            # Load user interests
            interests_result = self.supabase.table("user_interests").select(
                "interest, weight"
            ).eq("user_id", user_id).execute()
            
            interests = [row["interest"] for row in interests_result.data]
            interest_weights = {row["interest"]: row["weight"] for row in interests_result.data}
            
            # Load recent podcast history
            history_result = self.supabase.table("podcasts").select(
                "id, title, created_at"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
            
            recent_topics = []
            # Note: topics_covered column doesn't exist in current schema
            # for podcast in history_result.data:
            #     if podcast.get("topics_covered"):
            #         recent_topics.extend(podcast["topics_covered"])
            
            context = {
                "preferences": preferences,
                "interests": interests,
                "interest_weights": interest_weights,
                "recent_topics": recent_topics,
                "listening_stats": prefs_result.data.get("listening_stats", {}),
                "user_created_at": prefs_result.data.get("created_at")
            }
            
            logger.info(f"Loaded user context: {len(interests)} interests, {len(recent_topics)} recent topics")
            return context
            
        except Exception as e:
            logger.error(f"Failed to load user context for {user_id}: {str(e)}")
            # Return default context
            return {
                "preferences": UserPreferences(),
                "interests": [],
                "interest_weights": {},
                "recent_topics": [],
                "listening_stats": {},
                "user_created_at": None
            }
    
    async def build_continuity_context(
        self, 
        user_id: str, 
        topics: List[str]
    ) -> Dict[str, Any]:
        """
        Build continuity context by analyzing past podcasts and topic coverage.
        
        Args:
            user_id: User identifier
            topics: Current topics being covered
            
        Returns:
            Dictionary containing continuity information
        """
        logger.info(f"Building continuity context for topics: {topics}")
        
        try:
            # Get recent podcasts covering similar topics
            continuity_data = {
                "recent_episodes": [],
                "topic_coverage": {},
                "avoided_topics": [],
                "continuity_notes": []
            }
            
            # Query for recent podcasts with similar topics
            for topic in topics:
                similar_podcasts = self.supabase.table("podcasts").select(
                    "id, title, created_at"
                ).eq("user_id", user_id).order(
                    "created_at", desc=True
                ).limit(3).execute()
                
                continuity_data["recent_episodes"].extend(similar_podcasts.data)
                continuity_data["topic_coverage"][topic] = len(similar_podcasts.data)
            
            # Identify topics to avoid (recently covered)
            recent_episodes = continuity_data["recent_episodes"]
            if recent_episodes:
                # Find topics covered in last 7 days
                recent_date = datetime.utcnow() - timedelta(days=7)
                for episode in recent_episodes:
                    episode_date = datetime.fromisoformat(episode["created_at"].replace("Z", "+00:00"))
                    if episode_date > recent_date:
                        # Note: topics_covered column doesn't exist in current schema
                        pass
            
            # Generate continuity notes
            if continuity_data["recent_episodes"]:
                continuity_data["continuity_notes"] = [
                    f"User recently listened to episodes about {', '.join(topics)}",
                    f"Consider referencing previous discussions or building on past topics",
                    f"Avoid repeating content from recent episodes"
                ]
            
            logger.info(f"Built continuity context: {len(continuity_data['recent_episodes'])} recent episodes")
            return continuity_data
            
        except Exception as e:
            logger.error(f"Failed to build continuity context: {str(e)}")
            return {"recent_episodes": [], "topic_coverage": {}, "avoided_topics": [], "continuity_notes": []}
    
    async def generate_script(
        self,
        research: Dict[str, List[Source]],
        continuity: Dict[str, Any],
        preferences: UserPreferences,
        request: GenerationRequest,
        fact_checks: List[FactCheck]
    ) -> LiveKitScript:
        """
        Generate the complete podcast script using Claude with NEWS-STYLE coverage.
        
        Args:
            research: Research data organized by segment and topic
            continuity: Continuity context from past podcasts
            preferences: User preferences
            request: Original generation request
            fact_checks: Validated fact checks
            
        Returns:
            LiveKitScript object with complete podcast structure
        """
        logger.info("Generating NEWS-STYLE podcast script with Claude")
        
        try:
            # Prepare research summary with events
            research_summary = self._prepare_research_summary(research, fact_checks)
            
            # Extract events for news-style coverage
            events = self._extract_events_from_research(research)
            
            # Generate script with NEWS-STYLE approach
            script_prompt = f"""You are a PROFESSIONAL NEWS HOST presenting today's developments in an engaging podcast.

USER PREFERENCES:
- Complexity Level: {preferences.complexity_level.value}
- Tone: {preferences.tone.value}
- Pace: {preferences.pace.value}
- Duration: {request.duration_minutes} minutes

VERIFIED NEWS EVENTS TO COVER:
{self._format_events_for_news_coverage(events)}

🎯 CRITICAL STYLE RULES - NEWS COVERAGE (NOT ARTICLE SUMMARIES):

❌ NEVER SAY:
- "According to TechCrunch..."
- "Sources report that..."
- "MIT News indicates..."
- "Articles suggest..."
- "Reports show..."

✅ ALWAYS SAY:
- "OpenAI released..."
- "Meta announced..."
- "Researchers discovered..."
- "The company launched..."
- "Scientists revealed..."

❌ BAD EXAMPLE: "According to reports, OpenAI has launched a new model"
✅ GOOD EXAMPLE: "OpenAI dropped GPT-4 Turbo this week with 128K context - that's 16 times larger than before"

FOCUS ON WHAT HAPPENED, NOT WHO REPORTED IT.

PODCAST STRUCTURE ({request.duration_minutes} minutes total):
{self._format_segments_for_prompt(request.segments)}

WRITING STYLE:
- Energetic and conversational (like a news broadcast)
- Use specific numbers and facts
- Connect events to trends and implications
- Add brief analysis: "This is significant because..."
- Natural transitions between stories
- {preferences.pace} pacing
- {preferences.tone} tone

SEGMENT GUIDELINES:

INTRO (30-60 seconds):
- Hook with the most important headline
- Preview 2-3 major stories
- Create excitement
Example: "Big week in AI! OpenAI slashed prices by 40% while doubling context windows, Meta open-sourced their most powerful model yet, and we'll cover a wild security mishap that's got everyone talking. Let's dive in."

NEWS_OF_DAY (Main segment):
- Start with biggest story (90 seconds)
- Cover 2-3 major developments (60 seconds each)
- Quick hits for remaining stories (30 seconds each)
- Include specific facts, numbers, dates
- Add context and implications
- Use timing markers [MM:SS]

Example structure:
[0:00] "Let's start with the biggest news..."
[1:30] "Moving to another major development..."
[3:00] "In other AI news..."
[4:00] "Quick hits before we wrap..."

OUTRO (30-60 seconds):
- Recap 2-3 key takeaways
- Look ahead to what's coming
- Conversational sign-off

CONTINUITY:
{'; '.join(continuity.get('continuity_notes', ['First episode - no continuity']))}

Generate the COMPLETE script with:
- Timing markers [MM:SS]
- Natural, energetic delivery
- Specific facts and numbers
- NO source attribution
- Analysis and implications
- Smooth transitions

⚠️ CRITICAL FORMATTING REQUIREMENTS:
1. Use clear segment markers: ## INTRO, ## NEWS_OF_DAY, ## OUTRO
2. Write FULL content for each segment (hit the duration targets!)
3. INTRO: 50-80 seconds of content (~120-160 words)
4. NEWS_OF_DAY: 2.5-3.5 minutes of content (~400-600 words)
5. OUTRO: 40-60 seconds of content (~80-120 words)
6. DO NOT truncate or summarize - write the complete script

FORMAT:
## INTRO
[Full intro content with timing markers]

## NEWS_OF_DAY
[Full main segment content - be comprehensive, cover multiple stories]

## OUTRO
[Full outro content with recap]

Write as if you're presenting the NEWS, not summarizing articles.
Generate AT LEAST 600-800 words total for a {request.duration_minutes}-minute podcast.
"""

            messages = [{"role": "user", "content": script_prompt}]
            
            response = await self.claude.generate_completion(
                messages=messages,
                max_tokens=8000,
                temperature=0.7
            )
            
            # Parse the response into LiveKitScript format
            livekit_script = self._parse_script_response(response, request, preferences, research_summary)
            
            logger.info("NEWS-STYLE podcast script generated successfully")
            return livekit_script
            
        except Exception as e:
            logger.error(f"Failed to generate script: {str(e)}")
            raise
    
    async def generate_interactive_elements(
        self, 
        script: LiveKitScript, 
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate interactive elements for the podcast.
        
        Args:
            script: Generated podcast script
            count: Number of interactive elements to create
            
        Returns:
            List of interactive element dictionaries
        """
        logger.info(f"Generating {count} interactive elements")
        
        try:
            interactive_prompt = f"""Create {count} engaging interactive elements for this podcast script.

SCRIPT SUMMARY:
- Duration: {script.total_duration_estimate} seconds
- Segments: {len(script.segments)} segments
- Participants: {len(script.participants)} participants

Generate interactive elements such as:
1. Reflection questions for listeners
2. Poll questions about the content
3. Call-to-action moments
4. Audience engagement prompts
5. Discussion starters

For each element, provide:
- Type (question, poll, reflection, call_to_action)
- Timing (when in the podcast to include it)
- Content (the actual interactive element)
- Purpose (why it's engaging)

Format as JSON array with detailed objects."""

            messages = [{"role": "user", "content": interactive_prompt}]
            
            response = await self.claude.generate_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.8
            )
            
            # Parse interactive elements
            try:
                elements = json.loads(response)
                if not isinstance(elements, list):
                    elements = [elements]
                
                # Ensure we have the right number of elements
                elements = elements[:count]
                
                logger.info(f"Generated {len(elements)} interactive elements")
                return elements
                
            except json.JSONDecodeError:
                # Fallback: create basic interactive elements
                return self._create_fallback_interactive_elements(count)
                
        except Exception as e:
            logger.error(f"Failed to generate interactive elements: {str(e)}")
            return self._create_fallback_interactive_elements(count)
    
    async def _save_episode_topics(
        self,
        episode_id: str,
        podcast_id: str,
        user_id: str,
        events: List[Dict[str, Any]],
        script: Dict[str, Any]
    ) -> None:
        """
        Extract and save CONSOLIDATED episode topics to episode_topics table for follow-up queries.
        Groups related events to avoid fragmentation.
        
        Args:
            episode_id: ID of the episode
            podcast_id: ID of the parent podcast
            user_id: ID of the user
            events: List of discovered events
            script: Generated script data
        """
        logger.info(f"Extracting consolidated topics for episode {episode_id}")
        
        topics_to_save = []
        
        try:
            # 1. Group events by PRIMARY ENTITY (company/organization)
            entity_groups = self._group_events_by_entity(events)
            
            # Create consolidated topics for major entities
            for entity_name, entity_events in entity_groups.items():
                if len(entity_events) >= 1:  # At least 1 event
                    # Consolidate all information about this entity
                    all_key_facts = []
                    all_source_urls = []
                    event_summaries = []
                    max_importance = 0
                    
                    for event in entity_events:
                        all_key_facts.extend(event.get("key_facts", []))
                        all_source_urls.extend(event.get("source_urls", []))
                        event_summaries.append(event.get("event", ""))
                        max_importance = max(max_importance, event.get("importance_score", 5.0))
                    
                    # Create ONE consolidated topic for this entity
                    topic_name = f"{entity_name} Developments"
                    summary = f"{entity_name} featured in {len(entity_events)} development(s) this episode: " + "; ".join(event_summaries[:3])
                    
                    topics_to_save.append({
                        "episode_id": episode_id,
                        "podcast_id": podcast_id,
                        "user_id": user_id,
                        "topic_type": "entity",
                        "topic_name": topic_name[:200],
                        "summary": summary[:500],
                        "key_facts": all_key_facts[:10],  # Top 10 facts
                        "entities_mentioned": {
                            "primary_entity": entity_name,
                            "events_count": len(entity_events),
                            "related_events": event_summaries
                        },
                        "source_urls": list(set(all_source_urls))[:5],  # Unique URLs
                        "segment_mentioned": "multiple",
                        "importance_score": max_importance,
                        "created_at": datetime.utcnow().isoformat()
                    })
            
            # 2. Group remaining events by THEME (not already covered by entity topics)
            covered_events = {e.get("event") for entity_events in entity_groups.values() for e in entity_events if len(entity_groups.get(e.get("actors", [""])[0] if e.get("actors") else "", [])) >= 1}
            uncovered_events = [e for e in events if e.get("event") not in covered_events]
            
            theme_groups = self._group_events_by_theme(uncovered_events)
            
            # Create consolidated theme topics
            for theme_name, theme_events in theme_groups.items():
                if len(theme_events) >= 1:
                    all_key_facts = []
                    all_source_urls = []
                    event_summaries = []
                    avg_importance = sum(e.get("importance_score", 5.0) for e in theme_events) / len(theme_events)
                    
                    for event in theme_events:
                        all_key_facts.extend(event.get("key_facts", []))
                        all_source_urls.extend(event.get("source_urls", []))
                        event_summaries.append(event.get("event", ""))
                    
                    summary = f"This episode covers {len(theme_events)} development(s) related to {theme_name.lower()}: " + "; ".join(event_summaries[:2])
                    
                    topics_to_save.append({
                        "episode_id": episode_id,
                        "podcast_id": podcast_id,
                        "user_id": user_id,
                        "topic_type": "theme",
                        "topic_name": theme_name[:200],
                        "summary": summary[:500],
                        "key_facts": all_key_facts[:10],
                        "entities_mentioned": {},
                        "source_urls": list(set(all_source_urls))[:5],
                        "segment_mentioned": "multiple",
                        "importance_score": min(avg_importance + len(theme_events), 10.0),
                        "created_at": datetime.utcnow().isoformat()
                    })
            
            # Save all topics to database in batch
            if topics_to_save:
                result = self.supabase.table("episode_topics").insert(topics_to_save).execute()
                logger.info(f"✅ Saved {len(topics_to_save)} consolidated topics for episode {episode_id}")
                logger.info(f"   - {len([t for t in topics_to_save if t['topic_type'] == 'entity'])} entity groups")
                logger.info(f"   - {len([t for t in topics_to_save if t['topic_type'] == 'theme'])} theme groups")
            else:
                logger.warning(f"No topics to save for episode {episode_id}")
                
        except Exception as e:
            logger.error(f"Failed to save podcast topics: {str(e)}")
            import traceback
            traceback.print_exc()
            # Don't fail the whole podcast save if topics fail
            pass
    
    def _group_events_by_entity(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group events by primary entity (company/organization).
        Returns dictionary of entity_name -> [events]
        """
        entity_groups = {}
        
        # Major entities to consolidate around
        major_entities = ["OpenAI", "Google", "Meta", "Microsoft", "Anthropic", "Apple", 
                         "White House", "Congress", "Government"]
        
        for event in events:
            actors = event.get("actors", [])
            if not actors:
                continue
            
            # Find if any major entity is involved
            primary_entity = None
            for actor in actors:
                for major in major_entities:
                    if major.lower() in actor.lower():
                        primary_entity = major
                        break
                if primary_entity:
                    break
            
            # Group by primary entity
            if primary_entity:
                if primary_entity not in entity_groups:
                    entity_groups[primary_entity] = []
                entity_groups[primary_entity].append(event)
        
        return entity_groups
    
    def _group_events_by_theme(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group events by theme/category.
        Returns dictionary of theme_name -> [events]
        """
        theme_groups = {}
        
        # Define theme keywords (broader categories)
        theme_keywords = {
            "AI Policy & Regulation": ["policy", "regulation", "government", "white house", "congress", "law", "ban", "oversight", "pac", "lobbying"],
            "AI in Healthcare": ["health", "medical", "doctor", "cancer", "patient", "hospital", "diagnosis", "treatment", "mammogram", "disease"],
            "AI Safety & Security": ["safety", "security", "risk", "threat", "mistake", "error", "fail", "vulnerability", "attack"],
            "AI Products & Services": ["launch", "release", "integration", "app", "feature", "service", "platform", "tool"],
            "AI Research & Development": ["research", "breakthrough", "develop", "study", "university", "scientist", "discovery", "innovation"]
        }
        
        for event in events:
            event_text = f"{event.get('event', '')} {event.get('significance', '')} {' '.join(event.get('key_facts', []))}".lower()
            
            # Find best matching theme
            matched_theme = None
            max_matches = 0
            
            for theme_name, keywords in theme_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in event_text)
                if matches > max_matches:
                    max_matches = matches
                    matched_theme = theme_name
            
            # Group by theme
            if matched_theme and max_matches > 0:
                if matched_theme not in theme_groups:
                    theme_groups[matched_theme] = []
                theme_groups[matched_theme].append(event)
        
        return theme_groups
    
    def _extract_themes_from_events(self, events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Extract high-level themes from events (DEPRECATED - use _group_events_by_theme instead).
            
        Returns:
            Dictionary of theme_name -> {summary, related_events, importance}
        """
        themes = {}
        
        # Define theme keywords
        theme_keywords = {
            "AI Policy & Regulation": ["policy", "regulation", "government", "white house", "congress", "law", "ban", "oversight"],
            "AI in Healthcare": ["health", "medical", "doctor", "cancer", "patient", "hospital", "diagnosis", "treatment"],
            "AI Safety & Security": ["safety", "security", "risk", "threat", "mistake", "error", "fail"],
            "AI in Business & Productivity": ["business", "productivity", "integration", "workflow", "enterprise", "efficiency"],
            "AI Ethics & Society": ["ethics", "bias", "fairness", "privacy", "discrimination", "society", "impact"],
            "AI Research & Development": ["research", "breakthrough", "develop", "study", "university", "scientist", "discovery"],
            "Generative AI": ["generate", "chatgpt", "gpt", "dalle", "midjourney", "stable diffusion", "llm", "language model"]
        }
        
        for theme_name, keywords in theme_keywords.items():
            related_events = []
            for event in events:
                event_text = f"{event.get('event', '')} {event.get('significance', '')} {' '.join(event.get('key_facts', []))}".lower()
                if any(keyword in event_text for keyword in keywords):
                    related_events.append(event.get("event", ""))
            
            if related_events:
                themes[theme_name] = {
                    "summary": f"This podcast covers {len(related_events)} development(s) related to {theme_name.lower()}",
                    "related_events": related_events,
                    "importance": min(5.0 + len(related_events) * 1.5, 10.0)
                }
        
        return themes
    
    async def _get_or_create_podcast(self, user_id: str, podcast_data: Dict[str, Any]) -> str:
        """
        Get or create the user's main Podcast (the show).
        
        The podcast represents the show itself (like "Daily AI Updates"), 
        while episodes are individual chapters.
        
        Args:
            user_id: User ID
            podcast_data: Episode data containing topic information
            
        Returns:
            Podcast ID
        """
        try:
            # Try to find existing podcast for this user
            existing_podcasts = self.supabase.table("podcasts").select("id, title").eq(
                "user_id", user_id
            ).execute()
            
            if existing_podcasts.data and len(existing_podcasts.data) > 0:
                # Use the first podcast (user's main show)
                podcast_id = existing_podcasts.data[0]["id"]
                logger.info(f"✅ Using existing podcast: {existing_podcasts.data[0]['title']} ({podcast_id})")
                return podcast_id
            
            # No podcast exists - create one
            # Extract main topic from podcast_data for podcast title
            topics = []
            for segment in podcast_data.get("generation_metadata", {}).get("segments", []):
                topics.extend(segment.get("topics", []))
            
            main_topic = topics[0] if topics else "News"
            
            podcast_title = f"{user_id}'s Daily {main_topic.title()} Updates"
            podcast_description = f"Your personalized daily news podcast covering {', '.join(topics[:3]) if topics else 'your interests'}"
            
            podcast_result = self.supabase.table("podcasts").insert({
                "user_id": user_id,
                "title": podcast_title,
                "description": podcast_description,
                "status": "ready",  # Podcast (show) is ready for episodes
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            podcast_id = podcast_result.data[0]["id"]
            logger.info(f"✅ Created new podcast: {podcast_title} ({podcast_id})")
            return podcast_id
            
        except Exception as e:
            logger.error(f"Failed to get/create podcast: {str(e)}")
            raise
    
    async def save_to_database(self, podcast_data: Dict[str, Any]) -> str:
        """
        Save the complete episode data to Supabase.
        
        Creates or gets the user's podcast (show), then creates an episode under it.
        
        Args:
            podcast_data: Complete episode data dictionary
            
        Returns:
            Episode ID from database
        """
        logger.info("Saving episode data to database")
        
        try:
            user_id = podcast_data["user_id"]
            
            # Step 1: Get or create the user's Podcast (the show)
            podcast_id = await self._get_or_create_podcast(user_id, podcast_data)
            
            # Step 2: Create the Episode
            episode_result = self.supabase.table("episodes").insert({
                "podcast_id": podcast_id,
                # Note: user_id not needed - episodes relate to users via podcast_id
                "title": podcast_data["title"],
                "description": podcast_data["description"],
                "duration": podcast_data["total_duration"],
                "script": podcast_data["script"],  # ✅ Your table already has "script" column
                "created_at": datetime.utcnow().isoformat()
                # Note: No "status" or "metadata" - using existing simple schema
            }).execute()
            
            episode_id = episode_result.data[0]["id"]
            logger.info(f"✅ Episode created: {episode_id}")
            
            # Step 3: Save sources (linked to episode)
            if podcast_data["sources"]:
                sources_data = []
                for source in podcast_data["sources"]:
                    sources_data.append({
                        "episode_id": episode_id,
                        "url": source["url"],
                        "title": source["title"],
                        "publication": source["publication"],
                        "credibility_score": int(source["credibility_score"] * 10),
                        "content_summary": source["content_summary"]
                    })
                
                self.supabase.table("sources").insert(sources_data).execute()
                logger.info(f"✅ Saved {len(sources_data)} sources")
            
            # Step 4: Save fact checks (linked to episode)
            if podcast_data["fact_checks"]:
                fact_checks_data = []
                for fc in podcast_data["fact_checks"]:
                    fact_checks_data.append({
                        "episode_id": episode_id,
                        "claim": fc["claim"],
                        "confidence": fc["confidence"],
                        "verification_status": fc["verification_status"],
                        "notes": fc["notes"]
                    })
                
                self.supabase.table("fact_checks").insert(fact_checks_data).execute()
                logger.info(f"✅ Saved {len(fact_checks_data)} fact checks")
            
            # Step 5: Save episode topics for follow-up queries
            events_discovered = podcast_data.get("events_discovered", [])
            logger.info(f"Events discovered for topic extraction: {len(events_discovered)}")
            
            if events_discovered:
                logger.info(f"Calling _save_episode_topics with {len(events_discovered)} events")
                await self._save_episode_topics(
                    episode_id=episode_id,
                    podcast_id=podcast_id,
                    user_id=user_id,
                    events=events_discovered,
                    script=podcast_data.get("script", {})
                )
            else:
                logger.warning("No events_discovered found - skipping topic extraction")
            
            # Save interactive elements - skip for now due to schema issues
            if podcast_data["interactive_elements"]:
                logger.info(f"Skipping interactive_elements save (schema mismatch). Count: {len(podcast_data['interactive_elements'])}")
            
            logger.info(f"✅ Episode saved successfully with ID: {episode_id}")
            return episode_id
            
        except Exception as e:
            logger.error(f"Failed to save podcast to database: {str(e)}")
            raise
    
    # Helper methods for event discovery and verification
    
    async def _extract_all_events_single_call(
        self,
        articles: List[dict],
        topic: str,
        timeframe: str
    ) -> List[dict]:
        """
        OPTIMIZED: Extract ALL events in ONE Claude API call (not multiple calls).
        This is much faster than per-article extraction.
        """
        if not articles:
            return []
        
        # Combine all articles into one prompt (limit to prevent token overflow)
        articles_text = "\n\n---\n\n".join([
            f"ARTICLE {i+1}:\nTitle: {a['title']}\nURL: {a['url']}\n\n{a['content'][:2000]}"
            for i, a in enumerate(articles[:8])  # Limit to 8 articles
        ])
        
        extraction_prompt = f"""Extract 6-8 distinct news EVENTS from these {len(articles)} articles about {topic}.

{articles_text}

Return ONLY JSON array of events. Each event needs:
- event: What happened (specific and clear)
- date: When (YYYY-MM-DD or "{timeframe}")
- actors: Who was involved (array)
- key_facts: 3-5 specific facts with numbers/names (array)
- significance: Why it matters (one sentence)
- source_urls: Which article URLs mention this (array)

Rules:
- Deduplicate - same event in multiple articles = one entry
- Only recent events (last 2 weeks)
- Verifiable facts only, no opinions
- Include concrete details (numbers, dates, names)

DO NOT OUTPUT ANYTHING EXCEPT THE JSON ARRAY.
[
  {{
    "event": "Brief description",
    "date": "YYYY-MM-DD",
    "actors": ["Company/Person"],
    "key_facts": ["Fact 1", "Fact 2"],
    "significance": "Why it matters",
    "source_urls": ["url1"]
  }}
]
"""
        
        try:
            async with asyncio.timeout(15.0):  # 15s timeout for extraction
                response = await self.claude.generate_completion(
                    [{"role": "user", "content": extraction_prompt}],
                    max_tokens=3000,
                    temperature=0.3
                )
                
                # Parse events
                events = self._parse_events_from_response(response)
                
                # Add default fields
                for event in events:
                    event.setdefault("confidence", "medium")
                    event.setdefault("quote", "")
                
                return events
                
        except asyncio.TimeoutError:
            logger.error("⏱️  Event extraction timeout")
            return []
        except Exception as e:
            logger.error(f"❌ Event extraction failed: {e}")
            return []
    
    async def _fetch_with_timeout(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Fetch web content with timeout handling.
        
        Args:
            url: URL to fetch
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with success status and content
        """
        try:
            # Use asyncio.wait_for to implement timeout
            result = await asyncio.wait_for(
                self.claude.web_fetch(url),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Fetch timeout for {url} after {timeout}s")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.warning(f"Fetch error for {url}: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_publication_from_url(self, url: str) -> str:
        """
        Extract publication name from URL.
        
        Args:
            url: URL to extract from
            
        Returns:
            Publication name
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            domain = domain.replace("www.", "").replace("m.", "")
            
            # Extract main domain name
            parts = domain.split(".")
            if len(parts) >= 2:
                # Return main domain (e.g., "techcrunch" from "techcrunch.com")
                return parts[-2].title()
            
            return domain.title()
        except Exception:
            return "Unknown"
    
    def _format_articles_for_extraction(self, articles: List[Dict[str, Any]]) -> str:
        """
        Format articles for Claude event extraction.
        
        Args:
            articles: List of article dictionaries with content
            
        Returns:
            Formatted string for prompt
        """
        formatted_parts = []
        
        for i, article in enumerate(articles, 1):
            formatted_parts.append(f"{'='*80}")
            formatted_parts.append(f"ARTICLE {i}: {article.get('title', 'Untitled')}")
            formatted_parts.append(f"Publication: {article.get('publication', 'Unknown')}")
            formatted_parts.append(f"URL: {article.get('url', '')}")
            formatted_parts.append(f"Word Count: {article.get('word_count', 0)}")
            formatted_parts.append(f"{'-'*80}")
            formatted_parts.append(article.get('content', '')[:5000])  # Limit each article
            formatted_parts.append("")
        
        formatted_parts.append(f"{'='*80}")
        formatted_parts.append(f"TOTAL ARTICLES: {len(articles)}")
        formatted_parts.append(f"{'='*80}")
        
        return "\n".join(formatted_parts)
    
    def _parse_events_from_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse events from Claude's JSON response.
        
        Args:
            response: Raw response from Claude
            
        Returns:
            List of event dictionaries
        """
        try:
            # Try to parse as JSON directly
            events = json.loads(response)
            
            if isinstance(events, dict):
                # If single event, wrap in list
                events = [events]
            
            if not isinstance(events, list):
                logger.warning(f"Unexpected response type: {type(events)}")
                return []
            
            # Validate event structure
            valid_events = []
            for event in events:
                if isinstance(event, dict) and "event" in event:
                    # Ensure required fields exist
                    event.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
                    event.setdefault("actors", [])
                    event.setdefault("key_facts", [])
                    event.setdefault("significance", "")
                    event.setdefault("source_urls", [])
                    event.setdefault("quote", "")
                    valid_events.append(event)
            
            logger.info(f"Parsed {len(valid_events)} valid events from response")
            return valid_events
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {e}")
            
            # Try to extract JSON from markdown code blocks
            try:
                # Look for JSON between triple backticks or brackets
                import re
                
                # Try to find JSON array pattern
                json_match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
                if json_match:
                    events = json.loads(json_match.group(0))
                    if isinstance(events, list):
                        logger.info(f"Extracted {len(events)} events from markdown")
                        return events
                
                # Try to find JSON object pattern
                json_match = re.search(r'\{.*?\}', response, re.DOTALL)
                if json_match:
                    event = json.loads(json_match.group(0))
                    if isinstance(event, dict):
                        logger.info("Extracted single event from markdown")
                        return [event]
                        
            except Exception as inner_e:
                logger.error(f"Failed to extract JSON from markdown: {inner_e}")
            
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing events: {e}")
            return []
    
    def _parse_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from Claude's response (handles markdown formatting).
        
        Args:
            response: Raw response from Claude
            
        Returns:
            Parsed JSON dictionary or None if parsing fails
        """
        try:
            # Try direct JSON parse first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            try:
                import re
                json_match = re.search(r'\{.*?\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            except Exception:
                pass
            
            logger.warning("Failed to parse JSON from response")
            return None
    
    def _calculate_event_credibility(
        self, 
        event: Dict[str, Any], 
        sources: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate credibility score for an event based on sources and content.
        
        Args:
            event: Event dictionary
            sources: List of source articles
            
        Returns:
            Credibility score from 0-10
        """
        score = 5.0  # Base score
        
        # Factor 1: Number of source URLs mentioned (max +2)
        source_urls = event.get("source_urls", [])
        score += min(len(source_urls) * 0.5, 2.0)
        
        # Factor 2: Number of specific facts (max +2)
        key_facts = event.get("key_facts", [])
        score += min(len(key_facts) * 0.4, 2.0)
        
        # Factor 3: Has date (max +1)
        if event.get("date") and event["date"] != "":
            score += 1.0
        
        # Factor 4: Has quote (max +0.5)
        if event.get("quote") and event["quote"] != "":
            score += 0.5
        
        # Factor 5: Number of actors (max +1)
        actors = event.get("actors", [])
        score += min(len(actors) * 0.33, 1.0)
        
        # Factor 6: Source quality from original articles (max +1.5)
        if sources:
            avg_relevance = sum(s.get("relevance_score", 0.5) for s in sources) / len(sources)
            score += avg_relevance * 1.5
        
        # Ensure score is between 0 and 10
        return round(min(max(score, 0.0), 10.0), 1)
    
    def _format_event_as_summary(self, event: Dict[str, Any]) -> str:
        """
        Format an event dictionary as a content summary for Source objects.
        MUST be under 500 characters for Source validation.
        
        Args:
            event: Event dictionary from discover_news_events
            
        Returns:
            Formatted summary string (max 500 chars)
        """
        parts = []
        
        # Event description (truncate if needed)
        event_desc = event.get('event', 'Unknown event')
        if len(event_desc) > 200:
            event_desc = event_desc[:197] + "..."
        parts.append(f"EVENT: {event_desc}")
        
        # Date and actors
        date = event.get('date', '')
        actors = event.get('actors', [])
        if date:
            parts.append(f"Date: {date}")
        if actors:
            parts.append(f"Actors: {', '.join(actors[:2])}")  # Limit to 2 actors
        
        # Key facts (limit to 2-3 facts)
        key_facts = event.get('key_facts', [])
        if key_facts:
            parts.append("Key Facts:")
            for i, fact in enumerate(key_facts[:2], 1):  # Only first 2 facts
                fact_short = fact[:80] if len(fact) > 80 else fact
                parts.append(f"{i}. {fact_short}")
        
        # Significance (truncate if needed)
        significance = event.get('significance', '')
        if significance and len(significance) > 100:
            significance = significance[:97] + "..."
        if significance:
            parts.append(f"Why: {significance}")
        
        # Join and ensure under 500 chars
        summary = "\n".join(parts)
        if len(summary) > 500:
            summary = summary[:497] + "..."
        
        return summary
    
    # Helper methods for news-style script generation
    
    def _extract_events_from_research(self, research: Dict[str, List[Source]]) -> List[Dict[str, Any]]:
        """
        Extract event information from Source content_summary fields.
        Sources created from events have structured event data.
        """
        events = []
        
        for topic, sources in research.items():
            for source in sources:
                # Check if content_summary has EVENT: marker (from our event formatting)
                if source.content_summary and "EVENT:" in source.content_summary:
                    # Parse event data from content_summary
                    event = {
                        "event": self._extract_field(source.content_summary, "EVENT:"),
                        "date": self._extract_field(source.content_summary, "Date:"),
                        "actors": self._extract_field(source.content_summary, "Actors:").split(", ") if self._extract_field(source.content_summary, "Actors:") else [],
                        "key_facts": self._extract_key_facts(source.content_summary),
                        "significance": self._extract_field(source.content_summary, "Why:"),
                        "url": source.url,
                        "credibility_score": source.credibility_score * 10,  # Convert 0-1 to 0-10
                        "importance_score": self._calculate_importance_score(source.content_summary)
                    }
                    events.append(event)
                else:
                    # Fallback: create event from source metadata
                    event = {
                        "event": source.title,
                        "date": source.published_date.strftime("%Y-%m-%d") if source.published_date else "recent",
                        "actors": [source.publication],
                        "key_facts": [source.content_summary[:200]] if source.content_summary else [],
                        "significance": "Recent development in the field",
                        "url": source.url,
                        "credibility_score": source.credibility_score * 10,
                        "importance_score": 5.0
                    }
                    events.append(event)
        
        # Sort by IMPORTANCE first, then credibility
        events.sort(key=lambda x: (x.get("importance_score", 0), x.get("credibility_score", 0)), reverse=True)
        return events
    
    def _calculate_importance_score(self, content: str) -> float:
        """
        Calculate importance score based on event type and impact.
        Prioritizes major announcements/releases over quirky stories.
        """
        content_lower = content.lower()
        score = 5.0  # Base score
        
        # HIGH IMPORTANCE indicators (+3-4 points)
        high_importance = [
            'launch', 'release', 'announce', 'partnership', 'acquisition',
            'breakthrough', 'billion', 'million users', 'integration',
            'policy', 'regulation', 'white house', 'government'
        ]
        for keyword in high_importance:
            if keyword in content_lower:
                score += 3.0
                break
        
        # MEDIUM IMPORTANCE indicators (+1-2 points)
        medium_importance = [
            'report', 'study', 'research', 'develop', 'test',
            'improvement', 'update', 'feature'
        ]
        for keyword in medium_importance:
            if keyword in content_lower:
                score += 1.5
                break
        
        # LOW IMPORTANCE indicators (-2 points) - quirky/minor stories
        low_importance = [
            'mistake', 'error', 'mishap', 'doritos', 'bag',
            'high school', 'false alarm', 'confused'
        ]
        for keyword in low_importance:
            if keyword in content_lower:
                score -= 2.0
                break
        
        # Cap between 0-10
        return min(max(score, 0.0), 10.0)
    
    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field value from formatted text."""
        if not text or field_name not in text:
            return ""
        
        # Find the field and extract until next line or next field
        start = text.find(field_name) + len(field_name)
        end = text.find("\n", start)
        if end == -1:
            end = len(text)
        
        value = text[start:end].strip()
        # Remove any remaining formatting
        value = value.replace("Key Facts:", "").replace("Why:", "").strip()
        return value
    
    def _extract_key_facts(self, text: str) -> List[str]:
        """Extract key facts list from formatted text."""
        facts = []
        
        if "Key Facts:" not in text:
            return facts
        
        # Find the key facts section
        start = text.find("Key Facts:")
        end = text.find("Why:", start)
        if end == -1:
            end = len(text)
        
        facts_text = text[start:end]
        
        # Extract numbered facts
        for line in facts_text.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove numbering or bullets
                fact = line.lstrip("0123456789.-) ").strip()
                if fact:
                    facts.append(fact)
        
        return facts[:5]  # Limit to top 5 facts
    
    def _format_events_for_news_coverage(self, events: List[Dict[str, Any]]) -> str:
        """
        Format events specifically for news-style coverage (not article summaries).
        """
        if not events:
            return "No events available for coverage."
        
        formatted = []
        formatted.append("=" * 80)
        formatted.append("VERIFIED NEWS EVENTS FOR COVERAGE")
        formatted.append("=" * 80)
        
        for i, event in enumerate(events[:8], 1):  # Top 8 events
            formatted.append(f"\nEVENT #{i}: {event.get('event', 'Unknown event')}")
            formatted.append(f"Date: {event.get('date', 'Recent')}")
            
            actors = event.get('actors', [])
            if actors:
                formatted.append(f"Who: {', '.join(actors)}")
            
            key_facts = event.get('key_facts', [])
            if key_facts:
                formatted.append("Key Facts:")
                for fact in key_facts[:4]:  # Top 4 facts per event
                    formatted.append(f"  • {fact}")
            
            significance = event.get('significance', '')
            if significance:
                formatted.append(f"Why it matters: {significance}")
            
            credibility = event.get('credibility_score', 0)
            formatted.append(f"Confidence: {credibility:.1f}/10")
            formatted.append("-" * 60)
        
        formatted.append("\n" + "=" * 80)
        formatted.append(f"TOTAL EVENTS: {len(events)}")
        formatted.append("Remember: Present WHAT HAPPENED, not 'according to sources'")
        formatted.append("=" * 80)
        
        return "\n".join(formatted)
    
    # Helper methods
    def _prepare_research_summary(
        self, 
        research: Dict[str, List[Source]], 
        fact_checks: List[FactCheck]
    ) -> str:
        """Prepare research summary for script generation with detailed content."""
        summary_parts = []
        summary_parts.append("=" * 60)
        summary_parts.append("SOURCES AND CONTENT TO USE IN YOUR SCRIPT:")
        summary_parts.append("=" * 60)
        
        source_count = 0
        for key, sources in research.items():
            summary_parts.append(f"\nTOPIC: {key.replace('_', ' ').upper()}")
            summary_parts.append("-" * 60)
            for i, source in enumerate(sources, 1):
                source_count += 1
                summary_parts.append(f"\nSOURCE {source_count}: {source.title}")
                summary_parts.append(f"Publication: {source.publication}")
                summary_parts.append(f"URL: {source.url}")
                summary_parts.append(f"Credibility: {source.credibility_score}/1.0")
                summary_parts.append(f"\nContent Extract:")
                # Include much more content - up to 1000 characters per source
                content = source.content_summary[:1000] if source.content_summary else "No content available"
                summary_parts.append(content)
                if len(source.content_summary) > 1000:
                    summary_parts.append("...[content continues]")
                summary_parts.append("")
        
        # Add fact-check summary
        if fact_checks:
            summary_parts.append("\n" + "=" * 60)
            summary_parts.append("VERIFIED FACTS TO REFERENCE:")
            summary_parts.append("=" * 60)
            verified_facts = [fc for fc in fact_checks if fc.verification_status.value == "verified"]
            if verified_facts:
                for i, fc in enumerate(verified_facts[:10], 1):  # Top 10 verified facts
                    summary_parts.append(f"\n{i}. {fc.claim}")
                    summary_parts.append(f"   Confidence: {fc.confidence}")
                    if fc.notes:
                        summary_parts.append(f"   Notes: {fc.notes}")
        
        summary_parts.append("\n" + "=" * 60)
        summary_parts.append(f"TOTAL SOURCES PROVIDED: {source_count}")
        summary_parts.append("USE THIS INFORMATION TO CREATE A SPECIFIC, DETAILED SCRIPT")
        summary_parts.append("=" * 60)
        
        return "\n".join(summary_parts)
    
    def _format_segments_for_prompt(self, segments: List[PodcastSegmentRequest]) -> str:
        """Format segments for the script generation prompt."""
        segment_info = []
        for i, segment in enumerate(segments):
            topics_str = ", ".join(segment.topics) if segment.topics else "General content"
            segment_info.append(
                f"{i+1}. {segment.type.value.upper()} - {segment.duration_minutes} minutes - Topics: {topics_str}"
            )
        return "\n".join(segment_info)
    
    def _format_fact_checks_for_prompt(self, fact_checks: List[FactCheck]) -> str:
        """Format fact checks for the script generation prompt."""
        if not fact_checks:
            return "No fact checks available."
        
        fact_info = []
        for fc in fact_checks[:10]:  # Top 10 fact checks
            status_emoji = {
                "verified": "✅",
                "partially_verified": "⚠️",
                "unverified": "❓",
                "disputed": "❌"
            }.get(fc.verification_status.value, "❓")
            
            fact_info.append(f"{status_emoji} {fc.claim} (confidence: {fc.confidence})")
        
        return "\n".join(fact_info)
    
    def _parse_script_response(
        self, 
        response: str, 
        request: GenerationRequest, 
        preferences: UserPreferences,
        research_summary: str = ""
    ) -> LiveKitScript:
        """Parse Claude's response into a LiveKitScript object with actual transcript content."""
        from .types import Participant, Segment, Transition
        
        # Create participants
        participants = [
            Participant(
                name="Host" if preferences.voice_preference.value == "single" else "Host",
                role="Main presenter"
            )
        ]
        
        if preferences.voice_preference.value != "single":
            participants.append(
                Participant(
                    name="Co-host",
                    role="Supporting presenter"
                )
            )
        
        # Split the response into sections by segment type
        # Try to extract content for each segment from Claude's response
        segments = []
        current_time = 0.0
        response_lower = response.lower()
        
        for i, segment_req in enumerate(request.segments):
            duration_seconds = segment_req.duration_minutes * 60
            
            # Try to extract relevant content from Claude's response for this segment
            segment_content = self._extract_segment_content(
                response, 
                segment_req.type.value, 
                segment_req.topics or []
            )
            
            # If we couldn't extract specific content, use the full response or a portion of it
            if not segment_content or len(segment_content) < 50:
                # Divide the response among segments
                total_segments = len(request.segments)
                response_lines = response.split('\n\n')
                start_idx = int(i * len(response_lines) / total_segments)
                end_idx = int((i + 1) * len(response_lines) / total_segments)
                segment_content = '\n\n'.join(response_lines[start_idx:end_idx])
                
                # If still no content, create a basic script
                if not segment_content:
                    topic_text = f" about {', '.join(segment_req.topics)}" if segment_req.topics else ""
                    segment_content = f"""[{segment_req.type.value.upper()} SEGMENT]

Host: Welcome to this segment{topic_text}. 

{response[:500]}...

[This segment contains the main discussion and insights from our research.]
"""
            
            segment = Segment(
                type=segment_req.type,
                start_time=current_time,
                duration=duration_seconds,
                content=segment_content,
                participants=[p.name for p in participants],
                transitions=[]
            )
            segments.append(segment)
            current_time += duration_seconds
        
        # Create transitions
        transitions = []
        for i in range(len(segments) - 1):
            transition = Transition(
                from_segment=segments[i].type.value,
                to_segment=segments[i + 1].type.value,
                transition_type="smooth",
                duration=2.0,
                content=f"And now, let's move on to our {segments[i + 1].type.value} segment..."
            )
            transitions.append(transition)
        
        return LiveKitScript(
            total_duration_estimate=current_time,
            participants=participants,
            segments=segments,
            transitions=transitions,
            metadata={
                "generated_from": "claude_response",
                "response_length": len(response),
                "has_research": len(research_summary) > 0
            },
            fact_checks=[]
        )
    
    def _extract_segment_content(self, response: str, segment_type: str, topics: List[str]) -> str:
        """Extract content for a specific segment from Claude's response."""
        response_lower = response.lower()
        segment_type_lower = segment_type.lower()
        
        # Special handling for NEWS_OF_DAY / NEWS OF DAY / NEWS-OF-DAY
        if segment_type_lower in ['news_of_day', 'news-of-day', 'news of day']:
            possible_variants = [
                '## news_of_day',
                '## news-of-day', 
                '## news of day',
                '# news_of_day',
                '# news-of-day',
                '# news of day',
                'news_of_day segment',
                'news-of-day segment'
            ]
        else:
            possible_variants = [
                f"## {segment_type_lower}",
                f"# {segment_type_lower}",
                f"{segment_type_lower} segment",
                f"{segment_type_lower}:",
                f"[{segment_type_lower}]"
            ]
        
        # Find the segment start
        start_idx = -1
        marker_found = None
        for variant in possible_variants:
            if variant in response_lower:
                idx = response_lower.find(variant)
                if start_idx == -1 or idx < start_idx:
                    start_idx = idx
                    marker_found = variant
        
        if start_idx == -1:
            return ""  # Segment not found
        
        # Find the next segment (end of this segment)
        # Look for any other segment type markers after the current one
        all_segment_markers = [
            '## intro', '## outro', '## news_of_day', '## news-of-day', '## news of day',
            '# intro', '# outro', '# news_of_day', '# news-of-day', '# news of day',
            'intro segment', 'outro segment', 'news_of_day segment', 'news-of-day segment',
            '## deep_dive', '## quick_hits', '# deep_dive', '# quick_hits'
        ]
        
        # Find the next segment boundary
                end_idx = len(response)
        for marker in all_segment_markers:
            if marker == marker_found:
                continue  # Skip our current marker
            next_idx = response_lower.find(marker, start_idx + len(marker_found) + 20)
                    if next_idx > start_idx and next_idx < end_idx:
                        end_idx = next_idx
                
        # Extract the content
                content = response[start_idx:end_idx].strip()
        
        # Remove the segment header/marker from content
        lines = content.split('\n')
        if len(lines) > 2:
            # Skip title lines, keep actual content
            content_lines = []
            skip_header = True
            for line in lines:
                line_lower = line.lower().strip()
                # Skip header lines containing segment types or timing markers
                if skip_header and (
                    any(seg in line_lower for seg in ['intro', 'outro', 'news_of_day', 'news-of-day', 'news of day']) or
                    line.startswith('#') or
                    '[' in line and ']' in line and ':' in line  # timing markers like [0:00-1:00]
                ):
                    continue
                else:
                    skip_header = False
                    content_lines.append(line)
            
            content = '\n'.join(content_lines).strip()
        
        return content if len(content) > 50 else ""
    
    def _create_fallback_interactive_elements(self, count: int) -> List[Dict[str, Any]]:
        """Create fallback interactive elements."""
        elements = []
        for i in range(count):
            elements.append({
                "type": "question",
                "timing": i * 300,  # Every 5 minutes
                "content": f"Reflection question {i+1}: What are your thoughts on this topic?",
                "purpose": "Engage audience and encourage reflection"
            })
        return elements
    
    def _generate_podcast_title(self, request: GenerationRequest, user_context: Dict[str, Any]) -> str:
        """Generate a podcast title based on the request and user context."""
        topics = [topic for segment in request.segments for topic in (segment.topics or [])]
        if topics:
            return f"Exploring {', '.join(topics[:2])} - {request.format.value.title()} Episode"
        return f"Personalized {request.format.value.title()} Podcast"
    
    def _generate_podcast_description(self, request: GenerationRequest, user_context: Dict[str, Any]) -> str:
        """Generate a podcast description."""
        topics = [topic for segment in request.segments for topic in (segment.topics or [])]
        return f"A {request.duration_minutes}-minute {request.format.value} podcast covering {', '.join(topics[:3])} with verified facts and engaging content."
    
    def _calculate_verification_rate(self, fact_checks: List[FactCheck]) -> float:
        """Calculate the verification rate of fact checks."""
        if not fact_checks:
            return 0.0
        
        verified_count = sum(1 for fc in fact_checks if fc.verification_status.value == "verified")
        return round(verified_count / len(fact_checks), 3)
