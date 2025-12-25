# streamlit_app_langgraph.py - Complete Streamlit App with LangGraph StateGraph
import streamlit as st
import json
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import required libraries for travel planning
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from typing import List, Optional, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

# Set up environment variables
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["OPENWEATHERMAP_API_KEY"] = os.getenv("OWM_key")

# Singleton pattern for services
class SingletonMeta(type):
    """Metaclass for implementing Singleton pattern"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class LLMService(metaclass=SingletonMeta):
    """Singleton LLM service"""
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.llm = ChatGoogleGenerativeAI(model='gemini-2.5-pro')
            self._initialized = True

class SearchService(metaclass=SingletonMeta):
    """Singleton search service"""
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.search = DuckDuckGoSearchRun()
            self._initialized = True

# Initialize singleton services
llm_service = LLMService()
search_service = SearchService()
llm = llm_service.llm
search = search_service.search

try:
    weather_search = OpenWeatherMapAPIWrapper()
except Exception:
    weather_search = None

# Budget calculation function with singleton pattern
class BudgetCalculator(metaclass=SingletonMeta):
    """Singleton budget calculator"""

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.exchange_rates = {
                'EUR': 0.85, 'GBP': 0.75, 'INR': 83.0, 'CAD': 1.35,
                'AUD': 1.50, 'JPY': 150.0, 'CHF': 0.90, 'CNY': 7.20, 'USD': 1.0
            }
            self._initialized = True

    def get_currency_conversion_rate(self, from_currency: str, to_currency: str) -> float:
        """Get currency conversion rate from USD to target currency"""
        if from_currency == to_currency:
            return 1.0
        return self.exchange_rates.get(to_currency, 1.0)

    def calculate_budget_estimate(self, destination: str, num_days: int,
                                origin_city: str, preferred_currency: str = "USD") -> dict:
        """Calculate budget estimate based on destination and local costs"""
        try:
            # Search for budget information
            search_query = f"{destination} daily travel budget cost accommodation food"
            try:
                search_results = search.run(search_query)
            except Exception:
                search_results = "No search results available"

            # Default to mid-range cost
            daily_cost = 120

            # City-specific cost estimation
            expensive_european = ['paris', 'london', 'zurich', 'stockholm']
            expensive_asian = ['tokyo', 'singapore', 'hong kong']
            expensive_us = ['new york', 'san francisco', 'los angeles']
            budget_asian = ['bangkok', 'delhi', 'mumbai', 'jakarta']
            south_american = ['buenos aires', 'lima', 'bogota']

            destination_lower = destination.lower()

            if any(city in destination_lower for city in expensive_european):
                daily_cost = 180
            elif any(city in destination_lower for city in expensive_asian):
                daily_cost = 150
            elif any(city in destination_lower for city in expensive_us):
                daily_cost = 220
            elif any(city in destination_lower for city in budget_asian):
                daily_cost = 60
            elif any(city in destination_lower for city in south_american):
                daily_cost = 80

            total_budget = daily_cost * num_days
            conversion_rate = self.get_currency_conversion_rate("USD", preferred_currency)
            total_budget_converted = total_budget * conversion_rate
            daily_cost_converted = daily_cost * conversion_rate

            return {
                'total_budget': total_budget_converted,
                'daily_budget': daily_cost_converted,
                'currency': preferred_currency,
                'breakdown': {
                    'accommodation': total_budget_converted * 0.4,
                    'food': total_budget_converted * 0.3,
                    'activities': total_budget_converted * 0.2,
                    'transport': total_budget_converted * 0.1
                }
            }
        except Exception:
            # Fallback calculation
            daily_cost = 100
            total_budget = daily_cost * num_days
            conversion_rate = self.get_currency_conversion_rate("USD", preferred_currency)
            total_budget_converted = total_budget * conversion_rate
            daily_cost_converted = daily_cost * conversion_rate

            return {
                'total_budget': total_budget_converted,
                'daily_budget': daily_cost_converted,
                'currency': preferred_currency,
                'breakdown': {
                    'accommodation': total_budget_converted * 0.4,
                    'food': total_budget_converted * 0.3,
                    'activities': total_budget_converted * 0.2,
                    'transport': total_budget_converted * 0.1
                }
            }

# Initialize budget calculator
budget_calc = BudgetCalculator()

# Pydantic models
class TravelRequest(BaseModel):
    destination: str = Field(description="Travel destination")
    start_date: str = Field(description="Start date")
    end_date: str = Field(description="End date")
    num_days: int = Field(description="Number of days")
    currency: str = Field(description="Preferred currency")
    interests: str = Field(description="User interests")
    origin_city: str = Field(description="Origin city", default="Unknown")

class UserSession(BaseModel):
    session_id: str = Field(description="Session ID")
    user_id: str = Field(description="User ID")
    travel_request: TravelRequest = Field(description="Travel request")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")

# Session manager with singleton pattern
class SessionManager(metaclass=SingletonMeta):
    """Singleton session manager"""

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.sessions: Dict[str, UserSession] = {}
            self._initialized = True

    def create_session(self, user_id: str, travel_request: TravelRequest) -> str:
        """Create a new user session"""
        import uuid
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

# Travel planning tool with LangGraph
@tool
def generate_complete_travel_plan(city: str, dates: str, num_days: int,
                                origin_city: str, preferred_currency: str = "USD",
                                user_preferences: str = "") -> str:
    """Create a comprehensive travel plan with auto-calculated budget"""

    # Calculate budget estimate
    budget_info = budget_calc.calculate_budget_estimate(city, num_days, origin_city, preferred_currency)
    budget = budget_info['total_budget']
    currency = budget_info['currency']

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
        response = llm.invoke(prompt)
        travel_plan_content = response.content

        # Add budget info as JSON appendix
        budget_json = {"auto_calculated_budget": budget_info}
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

# LangGraph StateGraph setup
class TravelPlannerGraph(metaclass=SingletonMeta):
    """Singleton LangGraph travel planner"""

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.tools = [generate_complete_travel_plan]
            self.llm_with_tools = llm.bind_tools(self.tools)
            self.graph = self._build_graph()
            self._initialized = True

    def _build_graph(self):
        """Build the StateGraph"""
        def llm_function(state: MessagesState) -> MessagesState:
            """LLM function for travel planning"""
            user_question = state["messages"]
            response = self.llm_with_tools.invoke(user_question)
            return {"messages": [response]}

        # Build the graph
        builder = StateGraph(MessagesState)
        builder.add_node("llm_decision_step", llm_function)
        builder.add_node("tools", ToolNode(self.tools))
        builder.add_edge(START, "llm_decision_step")
        builder.add_conditional_edges("llm_decision_step", tools_condition)
        builder.add_edge("tools", "llm_decision_step")
        return builder.compile()

    def plan_trip(self, destination: str, start_date: str, end_date: str,
                  origin_city: str, preferred_currency: str = "USD",
                  preferences: str = "") -> dict:
        """Plan trip using StateGraph"""
        try:
            # Calculate days
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            num_days = (end_dt - start_dt).days

            dates_formatted = f"{start_date} to {end_date}"

            user_query = f"""Plan a trip to {destination} from {dates_formatted}
            for {num_days} days starting from {origin_city}.
            Preferred currency: {preferred_currency}
            Preferences: {preferences or 'general travel'}.

            Please use the generate_complete_travel_plan tool with these parameters:
            - city: {destination}
            - dates: {dates_formatted}
            - num_days: {num_days}
            - origin_city: {origin_city}
            - preferred_currency: {preferred_currency}
            - user_preferences: {preferences or 'general travel'}"""

            message = [HumanMessage(content=user_query)]
            response = self.graph.invoke({"messages": message})
            final_message = response["messages"][-1]

            # Get budget info
            budget_info = budget_calc.calculate_budget_estimate(
                destination, num_days, origin_city, preferred_currency
            )

            return {
                "success": True,
                "travel_plan": final_message.content if hasattr(final_message, 'content') else str(final_message),
                "budget_info": budget_info,
                "destination": destination,
                "origin_city": origin_city,
                "dates": dates_formatted,
                "num_days": num_days,
                "currency": preferred_currency
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "budget_info": None
            }

# Initialize the travel planner graph
travel_planner = TravelPlannerGraph()
session_manager = SessionManager()

# Streamlit App
def main():
    st.set_page_config(
        page_title="AI Travel Agent & Expense Planner (OOP + LangGraph)",
        page_icon="",
        layout="wide"
    )

    st.title("AI Travel Agent & Expense Planner")
    st.markdown("**Plan your perfect trip with OOP design, Singleton patterns, and LangGraph StateGraph**")

    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if 'travel_plan' not in st.session_state:
        st.session_state.travel_plan = None
    if 'budget_info' not in st.session_state:
        st.session_state.budget_info = None

    # Sidebar inputs
    with st.sidebar:
        st.header("Trip Details")
        st.markdown(f"**User ID:** {st.session_state.user_id}")

        origin_city = st.text_input("Origin City", placeholder="e.g., New York, London")
        destination = st.text_input("Destination City", placeholder="e.g., Paris, Tokyo")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() + timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now() + timedelta(days=37))

        num_days = (end_date - start_date).days if start_date and end_date else 0
        st.info(f"Trip Duration: {num_days} days")

        preferred_currency = st.selectbox(
            "Preferred Currency",
            ["USD", "EUR", "GBP", "INR", "CAD", "AUD", "JPY", "CHF", "CNY"],
            index=0
        )

        # Show estimated budget
        if destination and num_days > 0 and origin_city:
            with st.spinner("Calculating budget estimate..."):
                budget_estimate = budget_calc.calculate_budget_estimate(
                    destination, num_days, origin_city, preferred_currency
                )

            st.markdown("### Estimated Budget")
            st.metric("Total Budget", f"{budget_estimate['total_budget']:.0f} {budget_estimate['currency']}")
            st.metric("Daily Budget", f"{budget_estimate['daily_budget']:.0f} {budget_estimate['currency']}")

            with st.expander("Budget Breakdown"):
                st.write(f"Accommodation: {budget_estimate['breakdown']['accommodation']:.0f} {budget_estimate['currency']}")
                st.write(f"Food: {budget_estimate['breakdown']['food']:.0f} {budget_estimate['currency']}")
                st.write(f"Activities: {budget_estimate['breakdown']['activities']:.0f} {budget_estimate['currency']}")
                st.write(f"Transport: {budget_estimate['breakdown']['transport']:.0f} {budget_estimate['currency']}")

        preferences = st.text_area("Travel Preferences", placeholder="culture, food, museums")
        generate_plan = st.button("Generate Travel Plan", type="primary")

    # Main content
    if generate_plan and destination and num_days > 0 and origin_city:
        with st.spinner("Planning your trip using LangGraph StateGraph..."):
            try:
                # Create travel request
                travel_request = TravelRequest(
                    destination=destination,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    num_days=num_days,
                    currency=preferred_currency,
                    interests=preferences or "general travel",
                    origin_city=origin_city
                )

                # Create session
                session_id = session_manager.create_session(st.session_state.user_id, travel_request)

                # Plan trip using LangGraph
                result = travel_planner.plan_trip(
                    destination=destination,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    origin_city=origin_city,
                    preferred_currency=preferred_currency,
                    preferences=preferences or "general travel"
                )

                if result["success"]:
                    st.session_state.travel_plan = result["travel_plan"]
                    st.session_state.budget_info = result["budget_info"]
                    st.success("Your travel plan is ready!")
                else:
                    st.error(f"Error: {result['error']}")

            except Exception as e:
                st.error(f"Error generating travel plan: {str(e)}")

    elif generate_plan:
        if not origin_city:
            st.error("Please enter your origin city!")
        elif not destination:
            st.error("Please enter destination!")
        else:
            st.error("Please enter valid dates!")

    # Display travel plan
    if st.session_state.travel_plan:
        st.header("Your Personalized Travel Plan")

        # Display the markdown travel plan
        st.markdown(st.session_state.travel_plan)

        # Budget summary
        if st.session_state.budget_info:
            budget_info = st.session_state.budget_info

            st.header("Budget Summary")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total Budget", f"{budget_info['total_budget']:.0f} {budget_info['currency']}")
                st.metric("Daily Budget", f"{budget_info['daily_budget']:.0f} {budget_info['currency']}")

            with col2:
                st.subheader("Breakdown")
                st.write(f"Accommodation: {budget_info['breakdown']['accommodation']:.0f} {budget_info['currency']}")
                st.write(f"Food: {budget_info['breakdown']['food']:.0f} {budget_info['currency']}")
                st.write(f"Activities: {budget_info['breakdown']['activities']:.0f} {budget_info['currency']}")
                st.write(f"Transport: {budget_info['breakdown']['transport']:.0f} {budget_info['currency']}")

        # Actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Export Plan"):
                export_data = {
                    "travel_plan": st.session_state.travel_plan,
                    "budget_info": st.session_state.budget_info,
                    "user_id": st.session_state.user_id,
                    "generated_at": datetime.now().isoformat()
                }
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"travel_plan_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

        with col2:
            if st.button("Plan Another Trip"):
                st.session_state.travel_plan = None
                st.session_state.budget_info = None
                st.rerun()

        with col3:
            if st.button("Share Plan"):
                st.info("Sharing functionality would be implemented here")

if __name__ == "__main__":
    main()
