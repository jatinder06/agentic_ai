# models.py - Pydantic Models for Travel Planning
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from abc import ABC, abstractmethod


class PlacesResponse(BaseModel):
    """Structured response for places and attractions"""
    attractions: List[str] = Field(description="List of top tourist attractions")
    restaurants: List[str] = Field(description="List of recommended restaurants")
    activities: List[str] = Field(description="List of recommended activities")
    transportation: List[str] = Field(description="List of transportation options")
    summary: str = Field(description="Brief summary of the place")


class WeatherResponse(BaseModel):
    """Structured response for weather information"""
    current_weather: str = Field(description="Current weather conditions")
    forecast: List[str] = Field(description="Weather forecast for travel dates")
    temperature_range: str = Field(description="Temperature range during travel")
    recommendations: List[str] = Field(description="Weather-based recommendations")


class DayPlan(BaseModel):
    """Structured response for a single day plan"""
    day_number: int = Field(description="Day number of the trip")
    morning_activities: List[str] = Field(description="Morning activities (9 AM - 12 PM)")
    afternoon_activities: List[str] = Field(description="Afternoon activities (12 PM - 6 PM)")
    evening_activities: List[str] = Field(description="Evening activities (6 PM - 10 PM)")
    restaurants: Dict[str, str] = Field(description="Meal recommendations {meal_type: restaurant}")
    transportation_tips: List[str] = Field(description="Transportation suggestions")
    weather_considerations: List[str] = Field(description="Weather-based tips")


class FullItinerary(BaseModel):
    """Structured response for complete itinerary"""
    destination: str = Field(description="Destination city")
    total_days: int = Field(description="Total number of days")
    daily_plans: List[DayPlan] = Field(description="Day-by-day detailed plans")
    emergency_contacts: List[str] = Field(description="Emergency contacts and information")
    local_tips: List[str] = Field(description="Local tips and cultural insights")
    budget_breakdown: Dict[str, str] = Field(description="Daily budget breakdown")


class TripSummary(BaseModel):
    """Structured response for trip summary"""
    destination: str = Field(description="Destination city")
    travel_dates: str = Field(description="Travel dates")
    total_cost: str = Field(description="Total estimated cost")
    key_highlights: List[str] = Field(description="Trip highlights")
    budget_breakdown: Dict[str, str] = Field(description="Cost breakdown by category")
    important_notes: List[str] = Field(description="Important travel notes")
    emergency_info: List[str] = Field(description="Emergency information")


class CompleteTravelPlan(BaseModel):
    """Structured response for complete travel plan"""
    trip_overview: str = Field(description="Trip overview and highlights")
    weather_forecast: WeatherResponse = Field(description="Weather information")
    places_info: PlacesResponse = Field(description="Places and attractions")
    itinerary: FullItinerary = Field(description="Complete itinerary")
    budget_summary: Dict[str, str] = Field(description="Budget breakdown")
    practical_info: List[str] = Field(description="Practical travel information")
    final_checklist: List[str] = Field(description="Final travel checklist")


class TravelRequest(BaseModel):
    """Travel request from user"""
    destination: str = Field(description="Travel destination")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    budget: float = Field(description="Total budget amount")
    currency: str = Field(description="Currency code (USD, EUR, etc.)")
    preferences: List[str] = Field(default=[], description="User preferences")
    num_days: int = Field(description="Number of travel days")


class UserSession(BaseModel):
    """User session data"""
    session_id: str = Field(description="Unique session identifier")
    user_id: str = Field(description="User identifier")
    travel_request: TravelRequest = Field(description="Current travel request")
    travel_plan: CompleteTravelPlan = Field(default=None, description="Generated travel plan")
    created_at: str = Field(description="Session creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


# Abstract base classes for services
class BaseService(ABC):
    """Abstract base class for all services"""

    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """Process data - to be implemented by subclasses"""
        pass


class BaseTool(ABC):
    """Abstract base class for all tools"""

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the tool"""
        pass
