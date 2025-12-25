# langgraph_agent.py - LangGraph StateGraph Implementation
from typing import TypedDict, List
from datetime import datetime, timedelta

# LangGraph imports
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage

# Local imports
from services import LLMService, BudgetService, SearchService, WeatherService
from tools import get_travel_tools
from models import TravelRequest, CompleteTravelPlan


class TravelPlannerState(TypedDict):
    """State for travel planning workflow"""
    messages: List
    travel_request: TravelRequest
    budget_info: dict
    current_step: str


class LangGraphTravelAgent:
    """
    Travel Planning Agent using LangGraph StateGraph
    Implements the same workflow as the original streamlit app
    """

    def __init__(self):
        self.llm_service = LLMService()
        self.budget_service = BudgetService()
        self.search_service = SearchService()
        self.weather_service = WeatherService()

        # Get tools and bind them to LLM
        self.tools = get_travel_tools()
        self.llm_with_tools = self.llm_service.bind_tools(self.tools)

        # Build the StateGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph"""
        builder = StateGraph(MessagesState)

        # Add nodes
        builder.add_node("llm_decision_step", self._llm_function)
        builder.add_node("tools", ToolNode(self.tools))

        # Add edges
        builder.add_edge(START, "llm_decision_step")
        builder.add_conditional_edges("llm_decision_step", tools_condition)
        builder.add_edge("tools", "llm_decision_step")

        return builder.compile()

    def _llm_function(self, state: MessagesState) -> MessagesState:
        """LLM function for travel planning - matches original structure"""
        user_question = state["messages"]
        response = self.llm_with_tools.invoke(user_question)
        return {"messages": [response]}

    def calculate_budget_estimate(self, destination: str, num_days: int,
                                origin_city: str, preferred_currency: str = "USD") -> dict:
        """Calculate budget estimate - matches original function"""
        try:
            # Base daily costs by region (USD) - from original code
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
            try:
                search_results = self.search_service.process(search_query)
            except Exception:
                search_results = "Unable to fetch search results"

            # Default to mid-range if can't determine region
            daily_cost = 120

            # Simple estimation based on common destinations - from original code
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

            # Convert to preferred currency using budget service
            conversion_rate = self.budget_service.currency_service.get_rate("USD", preferred_currency)
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
            # Fallback budget calculation - from original code
            daily_cost = 100
            total_budget = daily_cost * num_days

            # Convert to preferred currency
            try:
                conversion_rate = self.budget_service.currency_service.get_rate("USD", preferred_currency)
            except Exception:
                conversion_rate = 1.0

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

    def plan_trip(self, destination: str, start_date: str, end_date: str,
                  origin_city: str, preferred_currency: str = "USD",
                  preferences: str = "") -> dict:
        """
        Main trip planning method that matches the original Streamlit workflow
        """
        # Calculate number of days
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            num_days = (end_dt - start_dt).days
        except Exception:
            num_days = 7  # Default fallback

        dates_formatted = f"{start_date} to {end_date}"

        # Create the user query that matches the original format
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

        # Get budget estimate
        budget_info = self.calculate_budget_estimate(
            destination, num_days, origin_city, preferred_currency
        )

        try:
            # Invoke the graph with the user query
            message = [HumanMessage(content=user_query)]
            response = self.graph.invoke({"messages": message})
            final_message = response["messages"][-1]

            # Ensure we extract the content properly
            travel_plan_content = ""
            if hasattr(final_message, 'content'):
                travel_plan_content = final_message.content
            elif isinstance(final_message, str):
                travel_plan_content = final_message
            elif isinstance(final_message, list):
                # If it's a list, join the content or extract from list items
                travel_plan_content = "\n".join([
                    item.content if hasattr(item, 'content') else str(item)
                    for item in final_message
                ])
            else:
                travel_plan_content = str(final_message)

            # Return structured response
            return {
                "success": True,
                "travel_plan": travel_plan_content,
                "budget_info": budget_info,
                "destination": destination,
                "origin_city": origin_city,
                "dates": dates_formatted,
                "num_days": num_days,
                "currency": preferred_currency
            }

        except Exception as e:
            # Return error response with budget info
            return {
                "success": False,
                "error": str(e),
                "budget_info": budget_info,
                "destination": destination,
                "origin_city": origin_city,
                "dates": dates_formatted,
                "num_days": num_days,
                "currency": preferred_currency
            }

# Singleton instance
langgraph_travel_agent = LangGraphTravelAgent()
