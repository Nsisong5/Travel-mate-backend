# services/ai_service.py - COMPLETE IMPLEMENTATION
import httpx
from groq import Groq
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from core.config import settings

class AIService:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.hf_headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour cache
    
    # ========== DESTINATION RECOMMENDATIONS ==========
    async def get_destination_recommendations(self, user_data: Dict, budget: Optional[float] = None, trip_type: str = "leisure") -> List[Dict]:
        """
        Get personalized destination recommendations formatted for AIRecommendation table
        
        Args:
            user_data: Dictionary containing user's past trips and preferences
            budget: Daily budget in USD (optional)
            trip_type: Type of trip (leisure, adventure, business, cultural, romantic)
            
        Returns:
            List of recommendations ready for database insertion
        """
        
        # Build user context and determine budget category
        context = self._build_user_context(user_data)
        budget_category = self._determine_budget_category(budget)
        lifestyle_category = user_data.get('preferences', {}).get('lifestyle', 'balanced')
        
        # Check cache first
        cache_key = f"dest_rec_{hash(context)}_{budget_category}_{trip_type}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Create AI prompt
        prompt = self._create_destination_prompt(context, budget_category, trip_type, budget)
        
        try:
            # Get recommendations from Groq
            response = await self._call_groq_api(prompt, "llama3-8b-8192", 1200, 0.7)
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
            
            # Cache the results
            self._save_to_cache(cache_key, formatted_recommendations)
            
            return formatted_recommendations
            
        except Exception as e:
            print(f"AI Service error in get_destination_recommendations: {e}")
            return await self._fallback_destination_recommendations(budget_category, trip_type, lifestyle_category)
    
    def _create_destination_prompt(self, context: str, budget_category: str, trip_type: str, budget: Optional[float]) -> str:
        """Create optimized prompt for destination recommendations"""
        
        budget_text = f"${budget}/day" if budget else f"{budget_category} range"
        
        return f"""
Based on this traveler's profile:
{context}

Trip Type: {trip_type}
Budget: {budget_text}

Recommend 5 diverse destinations that match their profile. Return ONLY valid JSON in this EXACT format:

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

REQUIREMENTS:
- name: City/destination name only (e.g., "Tokyo", "Santorini")  
- location: Country or region (e.g., "Japan", "Greece")
- title: Format as "City, Country" (e.g., "Tokyo, Japan")
- description: 150-300 characters, highly personalized based on their past trips
- settlement_type: Choose from "city", "town", "village", "resort", "island"
- destination_type: Always "destination"
- estimated_cost: Realistic daily budget in USD (accommodation + meals + activities)
- tags: 2-4 relevant descriptive tags (Cultural, Adventure, Budget-Friendly, Luxury, Historic, Nature, Romantic, etc.)
- rating: Realistic rating 3.5-5.0 based on tourist satisfaction
- budget_score: 1-100 scale (1=very cheap, 100=very expensive)

Focus on destinations that genuinely match their travel history and preferences.
Ensure variety in locations, budgets, and experiences.
"""

    def _format_destination_recommendation(self, rec: Dict, trip_type: str, budget_category: str, lifestyle_category: str) -> Dict:
        """Format and enhance recommendation with additional database fields"""
        
        return {
            # Core AI fields
            "name": rec.get("name", "").strip(),
            "location": rec.get("location", "").strip(),
            "title": rec.get("title", "").strip(),
            "description": rec.get("description", "").strip()[:1000],  # Ensure max length
            "settlement_type": rec.get("settlement_type", "city").lower(),
            "destination_type": rec.get("destination_type", "destination").lower(),
            "estimated_cost": int(rec.get("estimated_cost", 0)),
            "tags": rec.get("tags", [])[:5],  # Max 5 tags
            "rating": float(rec.get("rating", 4.0)),
            "budget_score": int(rec.get("budget_score", 50)),
            
            # Additional database fields
            "category": trip_type,
            "budget_category": budget_category,
            "lifestyle_category": lifestyle_category,
            "popularity": 0,  # Will be tracked by backend
            
            # Image fields (will be populated by ImageService)
            "image": None,
            "image2": None,
            "image3": None,
            "image4": None
        }
    
    def _validate_destination_recommendation(self, rec: Dict) -> bool:
        """Validate recommendation has required fields"""
        required_fields = ["name", "location", "title", "description"]
        return all(rec.get(field) for field in required_fields)
    
    # ========== CURRENT TRIP RECOMMENDATIONS ==========
    async def get_current_trip_recommendations(self, destination: str, trip_type: str = "leisure", duration: int = 3) -> List[Dict]:
        """
        Get specific activity/sight recommendations for current trip
        
        Args:
            destination: Current destination (e.g., "Paris, France")
            trip_type: Type of trip
            duration: Number of days
            
        Returns:
            List of recommendations in frontend format (not for database)
        """
        
        # Check cache
        cache_key = f"trip_rec_{destination}_{trip_type}_{duration}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        prompt = self._create_current_trip_prompt(destination, trip_type, duration)
        
        try:
            response = await self._call_groq_api(prompt, "llama3-8b-8192", 1500, 0.6)
            result = json.loads(response)
            recommendations = result.get("recommendations", [])
            
            # Format for frontend
            formatted_recommendations = []
            for rec in recommendations:
                formatted_rec = self._format_current_trip_recommendation(rec, destination)
                if self._validate_current_trip_recommendation(formatted_rec):
                    formatted_recommendations.append(formatted_rec)
            
            # Cache results
            self._save_to_cache(cache_key, formatted_recommendations)
            
            return formatted_recommendations
            
        except Exception as e:
            print(f"AI Service error in get_current_trip_recommendations: {e}")
            return self._fallback_current_trip_recommendations(destination)
    
    def _create_current_trip_prompt(self, destination: str, trip_type: str, duration: int) -> str:
        """Create prompt for current trip recommendations"""
        
        return f"""
For a {duration}-day {trip_type} trip to {destination}, recommend specific activities, sights, and experiences.

Focus on authentic, local experiences that travelers actually enjoy. Return ONLY valid JSON:

{{
    "recommendations": [
        {{
            "title": "Specific attraction or activity name",
            "category": "Dining",
            "bestTime": "9AM - 11AM",
            "estimatedCost": "$15 - $25",
            "location": {{
                "name": "Specific address or area name"
            }},
            "description": "Detailed 2-3 sentence description explaining what makes this special and why it's recommended for this trip",
            "culturalTips": [
                "Specific, actionable cultural tip",
                "Another helpful local insight",
                "Practical advice for visitors"
            ],
            "aiInsight": "AI Recommended for You"
        }}
    ]
}}

REQUIREMENTS:
- Provide 6-8 diverse recommendations
- category: Choose from "Dining", "Sightseeing", "Activities", "Shopping", "Culture", "Nature", "Entertainment"
- bestTime: Specific time recommendations (e.g., "6PM - 10PM", "Early morning", "Sunset")
- estimatedCost: Realistic price range in local context
- location.name: Specific area, street, or landmark name
- description: 150-400 characters explaining the experience and why it's special
- culturalTips: 3-4 specific, actionable tips for that location/activity
- Include mix of well-known and hidden gem locations
- Consider local customs, timing, and practical aspects

Make recommendations feel personal and locally authentic.
"""

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
            
            # Frontend-specific fields
            "inItinerary": False,
            "destination": destination,
            "images": [],  # Will be populated by ImageService
            "coverImage": None  # Will be set by ImageService
        }
    
    def _validate_current_trip_recommendation(self, rec: Dict) -> bool:
        """Validate current trip recommendation"""
        required_fields = ["title", "category", "description"]
        return all(rec.get(field) for field in required_fields)
    
    # ========== TRAVEL TIPS ==========
    async def get_travel_tips(self, destination: str, season: str = "current") -> Dict:
        """
        Get comprehensive travel tips for destination
        
        Args:
            destination: Destination name
            season: Season or "current"
            
        Returns:
            Dictionary with culture, language, and practical tips
        """
        
        cache_key = f"tips_{destination}_{season}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        prompt = self._create_travel_tips_prompt(destination, season)
        
        try:
            response = await self._call_groq_api(prompt, "llama3-8b-8192", 1000, 0.3)
            tips = json.loads(response)
            
            # Cache for longer since tips don't change often
            self._save_to_cache(cache_key, tips, ttl=7200)  # 2 hours
            
            return tips
            
        except Exception as e:
            print(f"AI Service error in get_travel_tips: {e}")
            return self._fallback_travel_tips(destination)
    
    def _create_travel_tips_prompt(self, destination: str, season: str) -> str:
        """Create prompt for travel tips"""
        
        return f"""
Provide practical, current travel tips for {destination} in {season}. 

Return ONLY valid JSON in this format:

{{
    "culture": {{
        "customs": ["Important local custom or tradition", "Another key cultural practice"],
        "etiquette": ["Social etiquette rule", "Behavioral guideline"],
        "dress_code": "Specific dress code guidance for the destination"
    }},
    "language": {{
        "basic_phrases": {{
            "hello": "local translation",
            "thank you": "local translation", 
            "excuse me": "local translation",
            "how much": "local translation",
            "where is": "local translation",
            "yes": "local translation",
            "no": "local translation"
        }},
        "language_tips": "Practical advice about communication and language barriers"
    }},
    "practical": {{
        "currency": "Currency name, exchange rate info, and payment method advice",
        "tipping": "Specific tipping culture and expected amounts",
        "transportation": "Best transportation options and practical advice",
        "safety": ["Specific safety tip", "Another safety consideration", "Local safety advice"]
    }}
}}

Make all advice specific to {destination} and current/practical.
Include real cultural insights, not generic advice.
"""

    # ========== UTILITY METHODS ==========
    async def _call_groq_api(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Make API call to Groq with error handling"""
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Groq API error: {e}")
            # Try Hugging Face as fallback
            return await self._call_huggingface_api(prompt)
    
    async def _call_huggingface_api(self, prompt: str) -> str:
        """Fallback to Hugging Face API"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
                    headers=self.hf_headers,
                    json={"inputs": prompt[:500]},  # Shorter for HF
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result[0].get("generated_text", "")
        except Exception as e:
            print(f"HuggingFace API error: {e}")
        
        return ""
    
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
        
        # Build context string
        context_parts = []
        
        if past_trips:
            recent_destinations = [trip.get('destination', '') for trip in past_trips[-5:]]
            context_parts.append(f"Recent destinations: {', '.join(filter(None, recent_destinations))}")
            
            # Analyze trip patterns
            trip_types = [trip.get('type', '') for trip in past_trips[-3:]]
            if trip_types:
                context_parts.append(f"Preferred trip types: {', '.join(filter(None, trip_types))}")
        else:
            context_parts.append("New traveler with no past trips")
        
        # Add preferences
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
    
    # ========== CACHING METHODS ==========
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
        
        # Simple cache cleanup - remove expired items
        if len(self.cache) > 100:  # Max cache size
            current_time = datetime.now().timestamp()
            expired_keys = [
                k for k, (_, timestamp) in self.cache.items() 
                if current_time - timestamp > cache_ttl
            ]
            for k in expired_keys:
                del self.cache[k]
    
    # ========== FALLBACK METHODS ==========
    async def _fallback_destination_recommendations(self, budget_category: str, trip_type: str, lifestyle_category: str) -> List[Dict]:
        """Fallback recommendations when AI fails"""
        
        fallback_destinations = [
            {
                "name": "Lisbon", "location": "Portugal", "title": "Lisbon, Portugal",
                "description": "Perfect blend of history, culture, and affordability. Stunning architecture, delicious food, and friendly locals make this ideal for budget-conscious travelers seeking authentic European experiences.",
                "settlement_type": "city", "destination_type": "destination",
                "estimated_cost": 60, "tags": ["Budget-Friendly", "Cultural", "Historic"],
                "rating": 4.3, "budget_score": 45
            },
            {
                "name": "Prague", "location": "Czech Republic", "title": "Prague, Czech Republic", 
                "description": "Fairy-tale architecture meets vibrant nightlife in this affordable European gem. Medieval streets, world-class beer, and rich history create unforgettable experiences.",
                "settlement_type": "city", "destination_type": "destination",
                "estimated_cost": 55, "tags": ["Historic", "Affordable", "Architecture"],
                "rating": 4.4, "budget_score": 40
            },
            {
                "name": "Bangkok", "location": "Thailand", "title": "Bangkok, Thailand",
                "description": "Street food paradise with incredible temples and bustling markets. Modern city energy mixed with ancient traditions, perfect for adventurous travelers on any budget.",
                "settlement_type": "city", "destination_type": "destination", 
                "estimated_cost": 35, "tags": ["Adventure", "Food", "Cultural"],
                "rating": 4.2, "budget_score": 25
            }
        ]
        
        # Add required database fields
        for dest in fallback_destinations:
            dest.update({
                "category": trip_type,
                "budget_category": budget_category,
                "lifestyle_category": lifestyle_category,
                "popularity": 0,
                "image": None, "image2": None, "image3": None, "image4": None
            })
        
        return fallback_destinations
    
    def _fallback_current_trip_recommendations(self, destination: str) -> List[Dict]:
        """Fallback for current trip recommendations"""
        return [
            {
                "title": "Local Market Experience",
                "category": "Culture",
                "bestTime": "9AM - 12PM", 
                "estimatedCost": "$10 - $20",
                "location": {"name": f"Central Market Area, {destination}"},
                "description": "Immerse yourself in local life at the bustling central market. Taste authentic flavors, interact with vendors, and discover unique local products.",
                "culturalTips": [
                    "Bring cash as many vendors don't accept cards",
                    "Try local breakfast specialties early in the morning",
                    "Learn basic greetings in the local language",
                    "Bargaining is often expected and appreciated"
                ],
                "aiInsight": "AI Recommended for You",
                "inItinerary": False,
                "destination": destination,
                "images": [],
                "coverImage": None
            },
            {
                "title": "Historic City Center Walking Tour",
                "category": "Sightseeing",
                "bestTime": "10AM - 2PM",
                "estimatedCost": "$15 - $30", 
                "location": {"name": f"Historic District, {destination}"},
                "description": "Discover the city's rich history through its architecture and landmarks. Self-guided or join a local guide for deeper insights.",
                "culturalTips": [
                    "Wear comfortable walking shoes",
                    "Bring water and sun protection",
                    "Respect photography rules at religious sites",
                    "Consider visiting during less crowded morning hours"
                ],
                "aiInsight": "AI Recommended for You",
                "inItinerary": False,
                "destination": destination,
                "images": [],
                "coverImage": None
            }
        ]
    
    def _fallback_travel_tips(self, destination: str) -> Dict:
        """Fallback travel tips"""
        return {
            "culture": {
                "customs": [
                    "Research local customs and traditions before visiting",
                    "Be respectful when visiting religious or cultural sites"
                ],
                "etiquette": [
                    "Learn basic greetings and polite expressions",
                    "Be patient and respectful with language barriers"
                ],
                "dress_code": "Dress modestly and appropriately for the local culture and climate"
            },
            "language": {
                "basic_phrases": {
                    "hello": "hello",
                    "thank you": "thank you",
                    "excuse me": "excuse me",
                    "how much": "how much",
                    "where is": "where is",
                    "yes": "yes", 
                    "no": "no"
                },
                "language_tips": "English is often understood in tourist areas. Consider downloading a translation app for easier communication."
            },
            "practical": {
                "currency": f"Research current exchange rates for {destination}. Many places accept credit cards, but carry some local cash.",
                "tipping": "Research local tipping customs as they vary significantly by country and culture.",
                "transportation": "Use official transportation services and research the best local options (public transit, rideshare, etc.).",
                "safety": [
                    "Keep important documents and valuables secure", 
                    "Stay in well-lit, populated areas especially at night",
                    "Trust your instincts and avoid situations that feel unsafe",
                    "Have emergency contact information readily available"
                ]
            }
        }


ai_service = AIService()