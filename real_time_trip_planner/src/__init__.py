# __init__.py - Travel Planning Package
"""
AI Travel Planner - OOP Architecture

A sophisticated AI-powered travel planning application built with Object-Oriented
Programming principles, featuring singleton design patterns and Streamlit UI.

Main Components:
- models: Pydantic data models and abstract base classes
- config: Configuration management with environment variables
- services: Service layer with singleton pattern implementation
- tools: LangChain tool classes for specific functionalities
- agent: Travel planning agent with workflow orchestration
- app: Streamlit UI application

Usage:
    from travel_planner import TravelPlanningService, TravelRequest

    service = TravelPlanningService()
    request = TravelRequest(destination="Paris", ...)
    plan = service.process(request)
"""

__version__ = "1.0.0"
__author__ = "Travel Planning Team"
__description__ = "AI-Powered Travel Planning with OOP Architecture"

# Import main classes for easy access
from .models import (
    TravelRequest,
    CompleteTravelPlan,
    UserSession,
    PlacesResponse,
    WeatherResponse,
    FullItinerary,
    TripSummary
)

from .services import (
    TravelPlanningService,
    SessionManager,
    LLMService,
    SearchService,
    WeatherService,
    BudgetService,
    CurrencyService
)

from .agent import TravelPlanningAgent, travel_agent
from .config import config

# Main classes for external use
__all__ = [
    # Models
    "TravelRequest",
    "CompleteTravelPlan",
    "UserSession",
    "PlacesResponse",
    "WeatherResponse",
    "FullItinerary",
    "TripSummary",

    # Services
    "TravelPlanningService",
    "SessionManager",
    "LLMService",
    "SearchService",
    "WeatherService",
    "BudgetService",
    "CurrencyService",

    # Agent
    "TravelPlanningAgent",
    "travel_agent",

    # Config
    "config"
]

# Package metadata
PACKAGE_INFO = {
    "name": "travel_planner",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "architecture": "Object-Oriented with Singleton Patterns",
    "ui_framework": "Streamlit",
    "ai_backend": "Google Gemini + LangChain",
    "features": [
        "AI-powered travel planning",
        "Real-time weather integration",
        "Smart budget calculation",
        "Session management",
        "Interactive UI",
        "Modular OOP design"
    ]
}
