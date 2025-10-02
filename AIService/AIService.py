# services/ai_service.py - INTEGRATED WITH IMAGE SERVICE
import httpx
from groq import Groq
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Import ImageService for automatic image enhancement
from AIService.image_service import ImageService

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Groq client uses GROQ_API_KEY from environment automatically
        self.groq_client = Groq()
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
        # Initialize ImageService for automatic image enhancement
        self.image_service = ImageService()
        logger.info("AIService initialized with ImageService integration")
    
    # ========== DESTINATION RECOMMENDATIONS ==========
    async def get_destination_recommendations(
        self, 
        user_data: Dict, 
        budget: Optional[float] = None, 
        trip_type: str = "leisure",
        include_images: bool = True  # New parameter to control image fetching
    ) -> List[Dict]:
        """
        Get personalized destination recommendations with images
        
        Flow:
        1. Check cache
        2. Generate AI recommendations
        3. Automatically fetch images (batch processed)
        4. Cache complete results
        5. Return recommendations with images
        """
        
        context = self._build_user_context(user_data)
        budget_category = self._determine_budget_category(budget)
        lifestyle_category = user_data.get('preferences', {}).get('lifestyle', 'balanced')
        
        # Check cache first (includes images if previously fetched)
        cache_key = f"dest_rec_{hash(context)}_{budget_category}_{trip_type}_img{include_images}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info("Returning cached destination recommendations with images")
            return cached_result
        
        # Create AI prompt
        prompt = self._create_destination_prompt(context, budget_category, trip_type, budget)
        
        try:
            # STEP 1: Get AI recommendations
            logger.info("Generating AI destination recommendations...")
            response = await self._call_groq_api(
                prompt=prompt,
                model="llama-3.3-70b-versatile",
                max_tokens=1200,
                temperature=0.7
            )
            
            # Parse JSON response
            result = json.loads(response)
            recommendations = result.get("recommendations", [])
            
            # Validate and format recommendations
            formatted_recommendations = []
            for rec in recommendations:
                formatted_rec = self._format_destination_recommendation(
                    rec, trip_type, budget_category, lifestyle_category
                )
                if self._validate_destination_recommendation(formatted_rec):
                    formatted_recommendations.append(formatted_rec)
            
            logger.info(f"Generated {len(formatted_recommendations)} AI recommendations")
            
            # STEP 2: Automatically enhance with images (batch processed!)
            if include_images and formatted_recommendations:
                logger.info("Fetching images for all destinations (batch processing)...")
                formatted_recommendations = await self.image_service.enhance_destinations_with_images(
                    formatted_recommendations,
                    images_per_destination=4  # Get 4 images per destination
                )
                logger.info("All destinations enhanced with images")
            
            # Cache the complete results (with images)
            self._save_to_cache(cache_key, formatted_recommendations)
            
            return formatted_recommendations
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response: {response[:200]}...")
            return await self._fallback_destination_recommendations(
                budget_category, trip_type, lifestyle_category, include_images
            )
            
        except Exception as e:
            logger.error(f"AI Service error in get_destination_recommendations: {e}")
            return await self._fallback_destination_recommendations(
                budget_category, trip_type, lifestyle_category, include_images
            )
    
    # ========== CURRENT TRIP RECOMMENDATIONS ==========
    async def get_current_trip_recommendations(
        self, 
        destination: str, 
        trip_type: str = "leisure", 
        duration: int = 3,
        include_images: bool = True  # New parameter to control image fetching
    ) -> List[Dict]:
        """
        Get specific activity recommendations for current trip with images
        
        Flow:
        1. Check cache
        2. Generate AI activity recommendations
        3. Automatically fetch images (batch processed)
        4. Cache complete results
        5. Return activities with images
        """
        
        # Check cache (includes images if previously fetched)
        cache_key = f"trip_rec_{destination}_{trip_type}_{duration}_img{include_images}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info("Returning cached trip recommendations with images")
            return cached_result
        
        prompt = self._create_current_trip_prompt(destination, trip_type, duration)
        
        try:
            # STEP 1: Get AI recommendations
            logger.info("Generating AI trip activity recommendations...")
            response = await self._call_groq_api(
                prompt=prompt,
                model="llama-3.3-70b-versatile",
                max_tokens=1500,
                temperature=0.6
            )
            
            result = json.loads(response)
            recommendations = result.get("recommendations", [])
            
            # Format for frontend
            formatted_recommendations = []
            for rec in recommendations:
                formatted_rec = self._format_current_trip_recommendation(rec, destination)
                if self._validate_current_trip_recommendation(formatted_rec):
                    formatted_recommendations.append(formatted_rec)
            
            logger.info(f"Generated {len(formatted_recommendations)} AI trip recommendations")
            
            # STEP 2: Automatically enhance with images (batch processed!)
            if include_images and formatted_recommendations:
                logger.info("Fetching images for all activities (batch processing)...")
                formatted_recommendations = await self.image_service.enhance_trip_activities_with_images(
                    formatted_recommendations,
                    images_per_activity=2  # Get 2 images per activity
                )
                logger.info("All activities enhanced with images")
            
            # Cache results (with images)
            self._save_to_cache(cache_key, formatted_recommendations)
            
            return formatted_recommendations
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._fallback_current_trip_recommendations(destination, include_images)
            
        except Exception as e:
            logger.error(f"AI Service error in get_current_trip_recommendations: {e}")
            return self._fallback_current_trip_recommendations(destination, include_images)
    
    # ========== TRAVEL TIPS ==========
    async def get_travel_tips(self, destination: str, season: str = "current") -> Dict:
        """Get comprehensive travel tips for destination (no images needed)"""
        
        cache_key = f"tips_{destination}_{season}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info("Returning cached travel tips")
            return cached_result
        
        prompt = self._create_travel_tips_prompt(destination, season)
        
        try:
            response = await self._call_groq_api(
                prompt=prompt,
                model="llama-3.3-70b-versatile",
                max_tokens=1000,
                temperature=0.3
            )
            
            tips = json.loads(response)
            
            # Cache for longer since tips don't change often
            self._save_to_cache(cache_key, tips, ttl=7200)
            logger.info(f"Generated travel tips for {destination}")
            
            return tips
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._fallback_travel_tips(destination)
            
        except Exception as e:
            logger.error(f"AI Service error in get_travel_tips: {e}")
            return self._fallback_travel_tips(destination)
    
    # ========== GROQ API CALL ==========
    async def _call_groq_api(
        self, 
        prompt: str, 
        model: str, 
        max_tokens: int, 
        temperature: float
    ) -> str:
        """Make API call to Groq (runs in thread pool to avoid blocking)"""
        
        def _sync_call():
            try:
                completion = self.groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    top_p=1,
                    stream=False
                )
                return completion.choices[0].message.content
                
            except Exception as e:
                logger.error(f"Groq API error: {e}")
                raise
        
        # Run sync Groq call in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_call)
    
    # ========== PROMPT CREATION (unchanged) ==========
    def _create_destination_prompt(
        self, 
        context: str, 
        budget_category: str, 
        trip_type: str, 
        budget: Optional[float]
    ) -> str:
        """Create optimized prompt for destination recommendations"""
        
        budget_text = f"${budget}/day" if budget else f"{budget_category} range"
        
        return f"""Based on this traveler's profile:
{context}

Trip Type: {trip_type}
Budget: {budget_text}

Recommend 5 diverse destinations that match their profile. Return ONLY valid JSON (no markdown, no extra text):

{{
    "recommendations": [
        {{
            "name": "Paris",
            "location": "France",
            "title": "Paris, France",
            "description": "Compelling 2-3 sentence description explaining why this destination perfectly matches their travel profile and what unique experiences await them",
            "settlement_type": "city",
            "destination_type": "destination",
            "estimated_cost": 150,
            "tags": ["Cultural", "Romantic", "Historic"],
            "rating": 4.5,
            "budget_score": 70
        }}
    ]
}}

Requirements:
- name: City/destination name only
- location: Country or region
- title: "City, Country" format
- description: 150-300 characters, personalized
- settlement_type: city/town/village/resort/island
- destination_type: Always "destination"
- estimated_cost: Daily USD budget
- tags: 2-4 relevant tags
- rating: 3.5-5.0
- budget_score: 1-100 (1=cheap, 100=expensive)

Return ONLY the JSON, no additional text."""
    
    def _create_current_trip_prompt(self, destination: str, trip_type: str, duration: int) -> str:
        """Create prompt for current trip recommendations"""
        
        return f"""For a {duration}-day {trip_type} trip to {destination}, recommend specific activities and experiences.

Return ONLY valid JSON (no markdown, no extra text):

{{
    "recommendations": [
        {{
            "title": "Specific attraction or activity name",
            "category": "Dining",
            "bestTime": "9AM - 11AM",
            "estimatedCost": "$15 - $25",
            "location": {{"name": "Specific address or area name"}},
            "description": "Detailed 2-3 sentence description",
            "culturalTips": ["Specific tip", "Another tip", "Practical advice"],
            "aiInsight": "AI Recommended for You"
        }}
    ]
}}

Requirements:
- 6-8 diverse recommendations
- category: Dining/Sightseeing/Activities/Shopping/Culture/Nature/Entertainment
- bestTime: Specific time recommendations
- estimatedCost: Realistic price range
- location.name: Specific area or landmark
- description: 150-400 characters
- culturalTips: 3-4 specific, actionable tips

Return ONLY the JSON, no additional text."""
    
    def _create_travel_tips_prompt(self, destination: str, season: str) -> str:
        """Create prompt for travel tips"""
        
        return f"""Provide practical travel tips for {destination} in {season}.

Return ONLY valid JSON (no markdown, no extra text):

{{
    "culture": {{
        "customs": ["Important custom", "Another custom"],
        "etiquette": ["Etiquette rule", "Another rule"],
        "dress_code": "Dress code guidance"
    }},
    "language": {{
        "basic_phrases": {{
            "hello": "translation",
            "thank you": "translation",
            "excuse me": "translation",
            "how much": "translation",
            "where is": "translation"
        }},
        "language_tips": "Communication advice"
    }},
    "practical": {{
        "currency": "Currency info",
        "tipping": "Tipping culture",
        "transportation": "Transportation options",
        "safety": ["Safety tip 1", "Safety tip 2"]
    }}
}}

Return ONLY the JSON, no additional text."""
    
    # ========== FORMATTING & VALIDATION (unchanged) ==========
    def _format_destination_recommendation(
        self, 
        rec: Dict, 
        trip_type: str, 
        budget_category: str, 
        lifestyle_category: str
    ) -> Dict:
        """Format and enhance recommendation with database fields"""
        
        return {
            "name": rec.get("name", "").strip(),
            "location": rec.get("location", "").strip(),
            "title": rec.get("title", "").strip(),
            "description": rec.get("description", "").strip()[:1000],
            "settlement_type": rec.get("settlement_type", "city").lower(),
            "destination_type": rec.get("destination_type", "destination").lower(),
            "estimated_cost": int(rec.get("estimated_cost", 0)),
            "tags": rec.get("tags", [])[:5],
            "rating": float(rec.get("rating", 4.0)),
            "budget_score": int(rec.get("budget_score", 50)),
            "category": trip_type,
            "budget_category": budget_category,
            "lifestyle_category": lifestyle_category,
            "popularity": 0,
            # Image fields will be populated by ImageService
            "image": None,
            "image2": None,
            "image3": None,
            "image4": None
        }
    
    def _format_current_trip_recommendation(self, rec: Dict, destination: str) -> Dict:
        """Format current trip recommendation for frontend"""
        
        return {
            "title": rec.get("title", "").strip(),
            "category": rec.get("category", "Activities"),
            "bestTime": rec.get("bestTime", "Anytime"),
            "estimatedCost": rec.get("estimatedCost", "Varies"),
            "location": rec.get("location", {"name": f"Near {destination}"}),
            "description": rec.get("description", "").strip(),
            "culturalTips": rec.get("culturalTips", []),
            "aiInsight": rec.get("aiInsight", "AI Recommended for You"),
            "inItinerary": False,
            "destination": destination,
            # Image fields will be populated by ImageService
            "images": [],
            "coverImage": None
        }
    
    def _validate_destination_recommendation(self, rec: Dict) -> bool:
        """Validate recommendation has required fields"""
        required_fields = ["name", "location", "title", "description"]
        return all(rec.get(field) for field in required_fields)
    
    def _validate_current_trip_recommendation(self, rec: Dict) -> bool:
        """Validate current trip recommendation"""
        required_fields = ["title", "category", "description"]
        return all(rec.get(field) for field in required_fields)
    
    # ========== UTILITY METHODS (unchanged) ==========
    def _determine_budget_category(self, budget: Optional[float]) -> str:
        """Convert numeric budget to category"""
        if not budget:
            return "moderate"
        elif budget < 50:
            return "budget"
        elif budget < 100:
            return "moderate"
        elif budget < 200:
            return "premium"
        else:
            return "luxury"
    
    def _build_user_context(self, user_data: Dict) -> str:
        """Build comprehensive user context from data"""
        
        past_trips = user_data.get('past_trips', [])
        preferences = user_data.get('preferences', {})
        
        context_parts = []
        
        if past_trips:
            recent_destinations = [trip.get('destination', '') for trip in past_trips[-5:]]
            context_parts.append(f"Recent destinations: {', '.join(filter(None, recent_destinations))}")
            
            trip_types = [trip.get('type', '') for trip in past_trips[-3:]]
            if trip_types:
                context_parts.append(f"Preferred trip types: {', '.join(filter(None, trip_types))}")
        else:
            context_parts.append("New traveler with no past trips")
        
        if preferences:
            if preferences.get('activities'):
                context_parts.append(f"Preferred activities: {preferences['activities']}")
            if preferences.get('travel_style'):
                context_parts.append(f"Travel style: {preferences['travel_style']}")
            if preferences.get('group_type'):
                context_parts.append(f"Usually travels: {preferences['group_type']}")
            if preferences.get('interests'):
                context_parts.append(f"Interests: {preferences['interests']}")
        
        return "\n".join(context_parts)
    
    # ========== CACHING (unchanged) ==========
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def _save_to_cache(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Save item to cache with timestamp"""
        cache_ttl = ttl or self.cache_ttl
        self.cache[key] = (data, datetime.now().timestamp())
        
        # Simple cache cleanup
        if len(self.cache) > 100:
            current_time = datetime.now().timestamp()
            expired_keys = [
                k for k, (_, timestamp) in self.cache.items()
                if current_time - timestamp > cache_ttl
            ]
            for k in expired_keys:
                del self.cache[k]
    
    # ========== FALLBACK METHODS (enhanced with images) ==========
    async def _fallback_destination_recommendations(
        self, 
        budget_category: str, 
        trip_type: str, 
        lifestyle_category: str,
        include_images: bool = True
    ) -> List[Dict]:
        """Fallback recommendations when AI fails (with images if enabled)"""
        
        logger.info("Using fallback destination recommendations")
        
        fallback_recs = [
            {
                "name": "Lisbon", "location": "Portugal", "title": "Lisbon, Portugal",
                "description": "Perfect blend of history, culture, and affordability. Stunning architecture, delicious food, and friendly locals make this ideal for budget-conscious travelers.",
                "settlement_type": "city", "destination_type": "destination",
                "estimated_cost": 60, "tags": ["Budget-Friendly", "Cultural", "Historic"],
                "rating": 4.3, "budget_score": 45,
                "category": trip_type, "budget_category": budget_category,
                "lifestyle_category": lifestyle_category, "popularity": 0,
                "image": None, "image2": None, "image3": None, "image4": None
            },
            {
                "name": "Prague", "location": "Czech Republic", "title": "Prague, Czech Republic",
                "description": "Fairy-tale architecture meets vibrant nightlife in this affordable European gem. Medieval streets and rich history.",
                "settlement_type": "city", "destination_type": "destination",
                "estimated_cost": 55, "tags": ["Historic", "Affordable", "Architecture"],
                "rating": 4.4, "budget_score": 40,
                "category": trip_type, "budget_category": budget_category,
                "lifestyle_category": lifestyle_category, "popularity": 0,
                "image": None, "image2": None, "image3": None, "image4": None
            }
        ]
        
        # Add images to fallback recommendations too
        if include_images:
            fallback_recs = await self.image_service.enhance_destinations_with_images(fallback_recs, 4)
        
        return fallback_recs
    
    async def _fallback_current_trip_recommendations(self, destination: str, include_images: bool = True) -> List[Dict]:
        """Fallback for current trip recommendations (with images if enabled)"""
        
        logger.info("Using fallback trip recommendations")
        
        fallback_activities = [
            {
                "title": "Local Market Experience",
                "category": "Culture",
                "bestTime": "9AM - 12PM",
                "estimatedCost": "$10 - $20",
                "location": {"name": f"Central Market, {destination}"},
                "description": "Explore the vibrant local market. Perfect for trying local foods and experiencing authentic daily life.",
                "culturalTips": [
                    "Bring cash for small vendors",
                    "Try local specialties",
                    "Practice basic greetings"
                ],
                "aiInsight": "AI Recommended for You",
                "inItinerary": False,
                "destination": destination,
                "images": [],
                "coverImage": None
            }
        ]
        
        # Add images to fallback activities too
        if include_images:
            fallback_activities = await self.image_service.enhance_trip_activities_with_images(fallback_activities, 2)
        
        return fallback_activities
    
    def _fallback_travel_tips(self, destination: str) -> Dict:
        """Fallback travel tips"""
        
        logger.info("Using fallback travel tips")
        
        return {
            "culture": {
                "customs": ["Research local customs before visiting", "Be respectful at cultural sites"],
                "etiquette": ["Learn basic greetings", "Be patient with language barriers"],
                "dress_code": "Dress modestly and appropriately"
            },
            "language": {
                "basic_phrases": {
                    "hello": "hello",
                    "thank you": "thank you",
                    "excuse me": "excuse me"
                },
                "language_tips": "English is often understood in tourist areas"
            },
            "practical": {
                "currency": "Research current exchange rates",
                "tipping": "Research local tipping customs",
                "transportation": "Use official transportation",
                "safety": ["Keep valuables secure", "Stay in well-lit areas"]
            }
        }
       
      

      
ai_service =  AIService()        