# tools.py - Tool Classes for Travel Planning
from typing import Dict, Any, List
import json
from langchain_core.tools import tool

from models import PlacesResponse, WeatherResponse, TripSummary


def create_travel_plan_tool():
    """Create the travel plan tool that matches the original implementation"""

    @tool
    def generate_complete_travel_plan(city: str, dates: str, num_days: int,
                                    origin_city: str, preferred_currency: str = "USD",
                                    user_preferences: str = "") -> str:
        """Create a comprehensive travel plan with auto-calculated budget"""

        # Import here to avoid circular import
        from agentic_ai.real_time_trip_planner.src.langgraph_agent import LangGraphTravelAgent
        from services import LLMService

        # Initialize services
        agent = LangGraphTravelAgent()

        # Calculate budget estimate using the same logic as original
        budget_info = agent.calculate_budget_estimate(city, num_days, origin_city, preferred_currency)
        budget = budget_info['total_budget']
        currency = budget_info['currency']

        # Create the same prompt as the original
        prompt = f"""Create a comprehensive travel plan for {city} from {dates} for {num_days} days.
        Starting from: {origin_city}
        Estimated budget: {budget:.0f} {currency} (calculated based on local costs)
        Budget breakdown: Accommodation: {budget_info['breakdown']['accommodation']:.0f} {currency}, Food: {budget_info['breakdown']['food']:.0f} {currency}, Activities: {budget_info['breakdown']['activities']:.0f} {currency}, Transport: {budget_info['breakdown']['transport']:.0f} {currency}
        Preferences: {user_preferences}

        Please provide a comprehensive travel plan in markdown table format as follows:

        ## TRAVEL PLAN FOR {city.upper()}

        ### Trip Overview
        | Field | Details |
        |-------|---------|
        | Destination | {city} |
        | Origin | {origin_city} |
        | Duration | {num_days} days |
        | Travel Dates | {dates} |
        | Total Budget | {budget:.0f} {currency} |
        | Daily Budget | {budget_info['daily_budget']:.0f} {currency} |

        ### Daily Itinerary Table
        | Day | Date | Morning (9-12) | Afternoon (12-17) | Evening (17-21) | Meals | Est. Cost |
        |-----|------|----------------|-------------------|-----------------|-------|-----------|
        | 1   | {dates.split(' to ')[0]} | Visit main attraction | City walking tour | Local dinner | Breakfast, Lunch, Dinner | {budget_info['daily_budget']:.0f} {currency} |
        | 2   | Day 2 | Museum visit | Shopping district | Cultural show | Breakfast, Lunch, Dinner | {budget_info['daily_budget']:.0f} {currency} |

        [Continue this pattern for all {num_days} days with specific activities]

        ### Budget Breakdown Table
        | Category | Daily Cost | Total Cost | Percentage | Notes |
        |----------|------------|------------|------------|-------|
        | Accommodation | {budget_info['breakdown']['accommodation']/num_days:.0f} {currency} | {budget_info['breakdown']['accommodation']:.0f} {currency} | 40% | Hotels/Hostels |
        | Food | {budget_info['breakdown']['food']/num_days:.0f} {currency} | {budget_info['breakdown']['food']:.0f} {currency} | 30% | Meals & Drinks |
        | Activities | {budget_info['breakdown']['activities']/num_days:.0f} {currency} | {budget_info['breakdown']['activities']:.0f} {currency} | 20% | Tours & Tickets |
        | Transport | {budget_info['breakdown']['transport']/num_days:.0f} {currency} | {budget_info['breakdown']['transport']:.0f} {currency} | 10% | Local Travel |

        ### Places & Attractions Table
        | Category | Location | Rating | Est. Time | Cost | Notes |
        |----------|----------|--------|-----------|------|-------|
        | Museum | National Museum | 5/5 stars | 2-3 hours | 15-25 {currency} | Must-visit cultural site |
        | Restaurant | Local Bistro | 4/5 stars | 1-2 hours | 30-50 {currency} | Traditional cuisine |
        | Attraction | City Center | 5/5 stars | 3-4 hours | Free | Historic district |

        Please provide specific real places, activities, and recommendations for {city}. Include actual restaurant names, museums, and attractions with realistic costs in {currency}.

        Also provide practical travel information including:
        - Weather forecast and packing suggestions
        - Local transportation options
        - Emergency contacts and important numbers
        - Cultural tips and local customs
        - Final travel checklist"""

        try:
            llm_service = LLMService()
            response = llm_service.process(prompt)

            # Return the response content directly as markdown tables
            travel_plan_content = response

            # Add budget info as a JSON appendix
            budget_json = {
                "auto_calculated_budget": budget_info
            }

            # Combine markdown content with budget info
            return f"{travel_plan_content}\n\n---\n**Budget Info (JSON):**\n```json\n{json.dumps(budget_json, indent=2)}\n```"

        except Exception as e:
            return f"""# Basic Travel Plan for {city}

## Trip Overview
- **Destination:** {city}
- **Origin:** {origin_city}
- **Budget:** {budget:.0f} {currency}

## Budget Breakdown
- **Accommodation:** {budget_info['breakdown']['accommodation']:.0f} {currency}
- **Food:** {budget_info['breakdown']['food']:.0f} {currency}
- **Activities:** {budget_info['breakdown']['activities']:.0f} {currency}
- **Transport:** {budget_info['breakdown']['transport']:.0f} {currency}

*Detailed planning is being prepared...*
Error: {str(e)}"""

    return generate_complete_travel_plan


# Create the main travel planning tool that matches original implementation
def get_travel_tools() -> List:
    """Get list of all travel planning tools"""
    travel_plan_tool = create_travel_plan_tool()
    return [travel_plan_tool]


def get_tool_by_name(name: str):
    """Get specific tool by name"""
    tools_dict = {
        "generate_complete_travel_plan": create_travel_plan_tool()
    }
    return tools_dict.get(name)
