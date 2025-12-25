# services.py - Service Classes for Travel Planning
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod, ABCMeta

from models import (
    BaseService, UserSession, TravelRequest,
    CompleteTravelPlan, PlacesResponse, WeatherResponse,
    FullItinerary, TripSummary
)
from config import config


class SingletonMeta(type):
    """Metaclass for implementing Singleton pattern"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonABCMeta(SingletonMeta, ABCMeta):
    """Metaclass that combines Singleton and ABCMeta for service classes."""
    pass


class LLMService(BaseService, metaclass=SingletonABCMeta):
    """Singleton service for LLM interactions with tool binding"""

    def __init__(self):
        if not hasattr(self, '_initialized'):
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                import os
                os.environ["GOOGLE_API_KEY"] = config.google_api_key
                self.llm = ChatGoogleGenerativeAI(model=config.llm_model)
                self.llm_with_tools = None  # Will be set when tools are bound
                self._initialized = True
            except ImportError as e:
                raise ImportError(f"Failed to import LangChain dependencies: {e}") from e

    def bind_tools(self, tools):
        """Bind tools to the LLM for function calling"""
        self.llm_with_tools = self.llm.bind_tools(tools)
        return self.llm_with_tools

    def process(self, prompt: str) -> str:
        """Process a prompt using the LLM"""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            raise RuntimeError(f"LLM processing failed: {e}") from e

    def invoke_with_tools(self, messages):
        """Invoke LLM with tools bound"""
        if self.llm_with_tools is None:
            raise ValueError("Tools not bound to LLM. Call bind_tools() first.")
        return self.llm_with_tools.invoke(messages)


class SearchService(BaseService, metaclass=SingletonABCMeta):
    """Singleton service for web search"""

    def __init__(self):
        if not hasattr(self, '_initialized'):
            try:
                from langchain_community.tools import DuckDuckGoSearchRun
                self.search = DuckDuckGoSearchRun()
                self._initialized = True
            except ImportError as e:
                raise ImportError(f"Failed to import search dependencies: {e}")

    def process(self, query: str) -> str:
        """Perform web search"""
        try:
            return self.search.invoke(query)
        except Exception as e:
            return f"Search failed: {e}"


class WeatherService(BaseService, metaclass=SingletonABCMeta):
    """Singleton service for weather information"""

    def __init__(self):
        if not hasattr(self, '_initialized'):
            try:
                from langchain_community.utilities import OpenWeatherMapAPIWrapper
                import os
                os.environ["OPENWEATHERMAP_API_KEY"] = config.openweather_api_key
                self.weather = OpenWeatherMapAPIWrapper()
                self._initialized = True
            except ImportError as e:
                raise ImportError(f"Failed to import weather dependencies: {e}")

    def process(self, location: str) -> str:
        """Get weather information for location"""
        try:
            return self.weather.run(location)
        except Exception as e:
            return f"Weather data unavailable: {e}"


class CurrencyService(BaseService, metaclass=SingletonABCMeta):
    """Singleton service for currency conversion"""

    def __init__(self):
        self.exchange_rates = config.exchange_rates

    def process(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert currency"""
        if from_currency == to_currency:
            return amount

        # Convert to USD first, then to target currency
        if from_currency != 'USD':
            amount = amount / self.exchange_rates.get(from_currency, 1.0)

        return amount * self.exchange_rates.get(to_currency, 1.0)

    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between currencies"""
        if from_currency == to_currency:
            return 1.0
        return self.exchange_rates.get(to_currency, 1.0) / self.exchange_rates.get(from_currency, 1.0)


class BudgetService(BaseService, metaclass=SingletonABCMeta):
    """Singleton service for budget calculations"""

    def __init__(self):
        self.city_costs = config.city_cost_estimates
        self.budget_breakdown = config.budget_breakdown
        self.currency_service = CurrencyService()

    def process(self, destination: str, num_days: int, preferred_currency: str = "USD") -> Dict[str, Any]:
        """Calculate budget estimate for destination"""
        # Get daily cost estimate
        city_key = destination.lower()
        daily_cost_usd = self.city_costs.get(city_key, self.city_costs['default'])

        # Calculate total budget in USD
        total_budget_usd = daily_cost_usd * num_days

        # Convert to preferred currency
        total_budget = self.currency_service.process(total_budget_usd, 'USD', preferred_currency)
        daily_budget = total_budget / num_days

        # Calculate breakdown
        breakdown = {}
        for category, percentage in self.budget_breakdown.items():
            breakdown[category] = total_budget * percentage

        return {
            'total_budget': total_budget,
            'daily_budget': daily_budget,
            'currency': preferred_currency,
            'breakdown': breakdown,
            'cost_per_day_usd': daily_cost_usd
        }


class SessionManager(metaclass=SingletonMeta):
    """Singleton class for managing user sessions"""

    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}

    def create_session(self, user_id: str, travel_request: TravelRequest) -> str:
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            travel_request=travel_request,
            created_at=timestamp,
            updated_at=timestamp
        )

        self.sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def update_session(self, session_id: str, travel_plan: CompleteTravelPlan) -> bool:
        """Update session with travel plan"""
        if session_id in self.sessions:
            self.sessions[session_id].travel_plan = travel_plan
            self.sessions[session_id].updated_at = datetime.now().isoformat()
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def get_user_sessions(self, user_id: str) -> Dict[str, UserSession]:
        """Get all sessions for a user"""
        return {sid: session for sid, session in self.sessions.items()
                if session.user_id == user_id}


class TravelPlanningService(BaseService, metaclass=SingletonABCMeta):
    """Main service for orchestrating travel planning"""

    def __init__(self):
        self.llm_service = LLMService()
        self.search_service = SearchService()
        self.weather_service = WeatherService()
        self.budget_service = BudgetService()
        self.session_manager = SessionManager()

    def process(self, travel_request: TravelRequest, user_id: str = "default") -> CompleteTravelPlan:
        """Process complete travel planning request"""
        try:
            # Create session
            session_id = self.session_manager.create_session(user_id, travel_request)

            # Generate travel plan
            travel_plan = self._generate_complete_plan(travel_request)

            # Update session
            self.session_manager.update_session(session_id, travel_plan)

            return travel_plan

        except Exception as e:
            raise Exception(f"Travel planning failed: {e}")

    def _generate_complete_plan(self, request: TravelRequest) -> CompleteTravelPlan:
        """Generate complete travel plan"""
        # This would contain the logic from the tools
        # For now, return a basic structure
        dates_str = f"{request.start_date} to {request.end_date}"

        # Get budget info
        budget_info = self.budget_service.process(
            request.destination,
            request.num_days,
            request.currency
        )

        # Create basic travel plan (in production, this would use the tools)
        plan = CompleteTravelPlan(
            trip_overview=f"Travel plan for {request.destination}",
            weather_forecast=WeatherResponse(
                current_weather="Partly cloudy",
                forecast=["Sunny", "Cloudy", "Rainy"],
                temperature_range="20-25°C",
                recommendations=["Pack light jacket", "Bring umbrella"]
            ),
            places_info=PlacesResponse(
                attractions=[f"Top attractions in {request.destination}"],
                restaurants=[f"Best restaurants in {request.destination}"],
                activities=[f"Popular activities in {request.destination}"],
                transportation=[f"Transportation options in {request.destination}"],
                summary=f"Overview of {request.destination}"
            ),
            itinerary=FullItinerary(
                destination=request.destination,
                total_days=request.num_days,
                daily_plans=[],
                emergency_contacts=["Emergency services: 911"],
                local_tips=["Tip: Learn basic local phrases"],
                budget_breakdown={
                    "accommodation": f"{budget_info['breakdown']['accommodation']:.0f} {request.currency}",
                    "food": f"{budget_info['breakdown']['food']:.0f} {request.currency}",
                    "activities": f"{budget_info['breakdown']['activities']:.0f} {request.currency}",
                    "transport": f"{budget_info['breakdown']['transport']:.0f} {request.currency}"
                }
            ),
            budget_summary={
                "total": f"{budget_info['total_budget']:.0f} {request.currency}",
                "daily": f"{budget_info['daily_budget']:.0f} {request.currency}",
                "currency": request.currency
            },
            practical_info=["Bring passport", "Check visa requirements"],
            final_checklist=["Book accommodation", "Pack essentials"]
        )

        return plan
