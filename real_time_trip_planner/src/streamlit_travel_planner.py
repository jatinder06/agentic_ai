
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
import requests

# Set up environment variables
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["OPENWEATHERMAP_API_KEY"] = os.getenv("OWM_key")

# Budget calculation function
def get_currency_conversion_rate(from_currency: str, to_currency: str) -> float:
    """Get currency conversion rate from USD to target currency"""
    if from_currency == to_currency:
        return 1.0

    # Basic exchange rates (you could use a real API for live rates)
    exchange_rates = {
        'EUR': 0.85,    # 1 USD = 0.85 EUR
        'GBP': 0.75,    # 1 USD = 0.75 GBP
        'INR': 83.0,    # 1 USD = 83 INR
        'CAD': 1.35,    # 1 USD = 1.35 CAD
        'AUD': 1.50,    # 1 USD = 1.50 AUD
        'JPY': 150.0,   # 1 USD = 150 JPY
        'CHF': 0.90,    # 1 USD = 0.90 CHF
        'CNY': 7.20,    # 1 USD = 7.20 CNY
        'USD': 1.0      # Base currency
    }

    return exchange_rates.get(to_currency, 1.0)

def calculate_budget_estimate(destination: str, num_days: int, origin_location: dict, preferred_currency: str = "USD") -> dict:
    """Calculate budget estimate based on destination and local costs"""
    try:
        # Base daily costs by region (USD)
        cost_data = {
            'Europe': {'budget': 80, 'mid': 150, 'luxury': 300},
            'Asia': {'budget': 40, 'mid': 80, 'luxury': 200},
            'North America': {'budget': 100, 'mid': 200, 'luxury': 400},
            'South America': {'budget': 50, 'mid': 100, 'luxury': 250},
            'Africa': {'budget': 60, 'mid': 120, 'luxury': 280},
            'Oceania': {'budget': 90, 'mid': 180, 'luxury': 350}
        }

        # Get destination cost info via search
        search_query = f"{destination} daily travel budget cost accommodation food"
        search_results = search.run(search_query)

        # Default to mid-range if can't determine region
        daily_cost = 120

        # Simple estimation based on common destinations
        if any(city in destination.lower() for city in ['paris', 'london', 'zurich', 'stockholm']):
            daily_cost = 180  # Expensive European cities
        elif any(city in destination.lower() for city in ['tokyo', 'singapore', 'hong kong']):
            daily_cost = 150  # Expensive Asian cities
        elif any(city in destination.lower() for city in ['new york', 'san francisco', 'los angeles']):
            daily_cost = 220  # Expensive US cities
        elif any(city in destination.lower() for city in ['bangkok', 'delhi', 'mumbai', 'jakarta']):
            daily_cost = 60   # Budget-friendly Asian cities
        elif any(city in destination.lower() for city in ['buenos aires', 'lima', 'bogota']):
            daily_cost = 80   # South American cities

        total_budget = daily_cost * num_days

        # Convert to preferred currency
        conversion_rate = get_currency_conversion_rate("USD", preferred_currency)
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
    except Exception as e:
        # Fallback budget calculation
        daily_cost = 100
        total_budget = daily_cost * num_days

        # Convert to preferred currency
        conversion_rate = get_currency_conversion_rate("USD", preferred_currency)
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

# Initialize LLM and tools
llm = ChatGoogleGenerativeAI(model='gemini-2.5-pro')
search = DuckDuckGoSearchRun()
weather_search = OpenWeatherMapAPIWrapper()

# [Include all your Pydantic models here - PlacesResponse, WeatherResponse, etc.]
class PlacesResponse(BaseModel):
    attractions: List[str] = Field(description="List of top tourist attractions")
    restaurants: List[str] = Field(description="List of recommended restaurants")
    activities: List[str] = Field(description="List of recommended activities")
    transportation: List[str] = Field(description="List of transportation options")
    summary: str = Field(description="Brief summary of the place")

class WeatherResponse(BaseModel):
    current_weather: str = Field(description="Current weather conditions")
    forecast: List[str] = Field(description="Weather forecast for travel dates")
    temperature_range: str = Field(description="Temperature range during travel")
    recommendations: List[str] = Field(description="Weather-based recommendations")

class DayPlan(BaseModel):
    day_number: int = Field(description="Day number of the trip")
    morning_activities: List[str] = Field(description="Morning activities")
    afternoon_activities: List[str] = Field(description="Afternoon activities")
    evening_activities: List[str] = Field(description="Evening activities")
    restaurants: Dict[str, str] = Field(description="Meal recommendations")
    transportation_tips: List[str] = Field(description="Transportation suggestions")
    weather_considerations: List[str] = Field(description="Weather-based tips")

class FullItinerary(BaseModel):
    destination: str = Field(description="Destination city")
    total_days: int = Field(description="Total number of days")
    daily_plans: List[DayPlan] = Field(description="Day-by-day detailed plans")
    emergency_contacts: List[str] = Field(description="Emergency contacts")
    local_tips: List[str] = Field(description="Local tips and cultural insights")
    budget_breakdown: Dict[str, str] = Field(description="Budget breakdown")

class CompleteTravelPlan(BaseModel):
    trip_overview: str = Field(description="Trip overview and highlights")
    weather_forecast: WeatherResponse = Field(description="Weather information")
    places_info: PlacesResponse = Field(description="Places and attractions")
    itinerary: FullItinerary = Field(description="Complete itinerary")
    budget_summary: Dict[str, str] = Field(description="Budget breakdown")
    practical_info: List[str] = Field(description="Practical travel information")
    final_checklist: List[str] = Field(description="Final travel checklist")

# Initialize parsers
complete_plan_parser = PydanticOutputParser(pydantic_object=CompleteTravelPlan)

# [Include your generate_complete_travel_plan tool here]
@tool
def generate_complete_travel_plan(city: str, dates: str, num_days: int, origin_city: str, preferred_currency: str = "USD", user_preferences: str = "") -> str:
    """Create a comprehensive travel plan with auto-calculated budget"""

    # Get user location for context
    origin_location = {'city': origin_city}

    # Calculate budget estimate
    budget_info = calculate_budget_estimate(city, num_days, origin_location, preferred_currency)
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

        # Return the response content directly as markdown tables
        travel_plan_content = response.content

        # Add budget info as a JSON appendix
        budget_json = {
            "auto_calculated_budget": budget_info
        }

        # Combine markdown content with budget info
        return f"{travel_plan_content}\n\n---\n**Budget Info (JSON):**\n```json\n{json.dumps(budget_json, indent=2)}\n```"

    except Exception:
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

*Detailed planning is being prepared...*"""

# Set up tools and graph
tools = [generate_complete_travel_plan]
llm_with_tools = llm.bind_tools(tools)

def function_1(state: MessagesState) -> MessagesState:
    """LLM function for travel planning"""
    user_question = state["messages"]
    response = llm_with_tools.invoke(user_question)
    return {"messages": [response]}

# Build the graph
builder = StateGraph(MessagesState)
builder.add_node("llm_decision_step", function_1)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "llm_decision_step")
builder.add_conditional_edges("llm_decision_step", tools_condition)
builder.add_edge("tools", "llm_decision_step")

travel_plan_graph = builder.compile()

# Streamlit App
def main():
    st.set_page_config(
        page_title="AI Travel Planner",
        page_icon="",
        layout="wide"
    )

    st.title("AI Travel Agent & Expense Planner")
    st.markdown("**Plan your perfect trip with real-time data and AI recommendations**")

    # Sidebar inputs
    with st.sidebar:
        st.header("Trip Details")

        # Manual origin city input
        origin_city = st.text_input("Origin City", placeholder="e.g., New York, London")

        destination = st.text_input("Destination City", placeholder="e.g., Paris, Tokyo")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() + timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now() + timedelta(days=37))

        num_days = (end_date - start_date).days if start_date and end_date else 0
        st.info(f"Trip Duration: {num_days} days")

        # Currency selection
        preferred_currency = st.selectbox(
            "Preferred Currency",
            ["USD", "EUR", "GBP", "INR", "CAD", "AUD", "JPY", "CHF", "CNY"],
            index=0,
            help="Select your preferred currency for budget display"
        )

        # Show estimated budget
        if destination and num_days > 0 and origin_city:
            with st.spinner("Calculating budget estimate..."):
                # Create a simple location dict for the origin
                origin_location = {'city': origin_city}
                budget_estimate = calculate_budget_estimate(destination, num_days, origin_location, preferred_currency)

            st.markdown("### Estimated Budget")
            st.metric("Total Budget", f"{budget_estimate['total_budget']:.0f} {budget_estimate['currency']}")
            st.metric("Daily Budget", f"{budget_estimate['daily_budget']:.0f} {budget_estimate['currency']}")

            with st.expander("Budget Breakdown"):
                st.write(f"Accommodation: {budget_estimate['breakdown']['accommodation']:.0f} {budget_estimate['currency']}")
                st.write(f"Food: {budget_estimate['breakdown']['food']:.0f} {budget_estimate['currency']}")
                st.write(f"Activities: {budget_estimate['breakdown']['activities']:.0f} {budget_estimate['currency']}")
                st.write(f"Transport: {budget_estimate['breakdown']['transport']:.0f} {budget_estimate['currency']}")

        preferences = st.text_area("Travel Preferences", placeholder="culture, food, museums")

        generate_plan = st.button("Generate Travel Plan", type="primary")    # Main content
    if generate_plan and destination and num_days > 0 and origin_city:
        dates_formatted = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

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

        with st.spinner("Planning your trip..."):
            try:
                message = [HumanMessage(content=user_query)]
                response = travel_plan_graph.invoke({"messages": message})
                final_message = response["messages"][-1]

                st.success("Your travel plan is ready!")

                # Get budget estimate for display
                origin_location = {'city': origin_city}
                budget_info = calculate_budget_estimate(destination, num_days, origin_location, preferred_currency)

                # Display tabs
                tab1, tab2, tab3 = st.tabs(["Travel Plan", "Budget", "Summary"])

                with tab1:
                    st.header("Complete Travel Plan")
                    if hasattr(final_message, 'content') and final_message.content:
                        try:
                            # Try to parse as JSON first (for backward compatibility)
                            json_content = json.loads(final_message.content)

                            # Display structured tables
                            st.subheader("Trip Overview")
                            overview_data = {
                                'Field': ['Destination', 'Origin', 'Duration', 'Travel Dates', 'Total Budget'],
                                'Details': [
                                    destination,
                                    origin_city,
                                    f"{num_days} days",
                                    dates_formatted,
                                    f"{budget_info['total_budget']:.0f} {budget_info['currency']}"
                                ]
                            }
                            st.table(pd.DataFrame(overview_data))

                            st.subheader("Budget Breakdown")
                            budget_table_data = {
                                'Category': ['Accommodation', 'Food', 'Activities', 'Transport'],
                                'Daily Cost': [
                                    f"{budget_info['breakdown']['accommodation']/num_days:.0f} {budget_info['currency']}",
                                    f"{budget_info['breakdown']['food']/num_days:.0f} {budget_info['currency']}",
                                    f"{budget_info['breakdown']['activities']/num_days:.0f} {budget_info['currency']}",
                                    f"{budget_info['breakdown']['transport']/num_days:.0f} {budget_info['currency']}"
                                ],
                                'Total Cost': [
                                    f"{budget_info['breakdown']['accommodation']:.0f} {budget_info['currency']}",
                                    f"{budget_info['breakdown']['food']:.0f} {budget_info['currency']}",
                                    f"{budget_info['breakdown']['activities']:.0f} {budget_info['currency']}",
                                    f"{budget_info['breakdown']['transport']:.0f} {budget_info['currency']}"
                                ],
                                'Percentage': ['40%', '30%', '20%', '10%']
                            }
                            st.table(pd.DataFrame(budget_table_data))

                            # Show full JSON response in expander
                            with st.expander("Full Travel Plan Details"):
                                st.json(json_content)

                        except Exception:
                            # Display as markdown if not JSON
                            st.markdown(final_message.content)

                with tab2:
                    st.header("Budget Breakdown")
                    daily_budget = budget_info['daily_budget']
                    st.metric("Daily Budget", f"{daily_budget:.0f} {budget_info['currency']}")

                    budget_data = {
                        'Accommodation (40%)': budget_info['breakdown']['accommodation'],
                        'Food (30%)': budget_info['breakdown']['food'],
                        'Activities (20%)': budget_info['breakdown']['activities'],
                        'Transport (10%)': budget_info['breakdown']['transport']
                    }

                    for category, amount in budget_data.items():
                        st.write(f"{category}: {amount:.0f} {budget_info['currency']}")

                with tab3:
                    st.header("Trip Summary")
                    st.write(f"**Origin:** {origin_city}")
                    st.write(f"**Destination:** {destination}")
                    st.write(f"**Dates:** {dates_formatted}")
                    st.write(f"**Duration:** {num_days} days")
                    st.write(f"**Currency:** {budget_info['currency']}")
                    st.write(f"**Estimated Budget:** {budget_info['total_budget']:.0f} {budget_info['currency']}")

            except Exception as e:
                st.error(f"Error generating travel plan: {str(e)}")

    elif generate_plan:
        if not origin_city:
            st.error("Please enter your origin city!")
        elif not destination:
            st.error("Please enter destination!")
        else:
            st.error("Please enter valid dates!")

if __name__ == "__main__":
    main()
