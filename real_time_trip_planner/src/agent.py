# agent.py - Travel Planning Agent using LangGraph
from typing import TypedDict, List, Optional
import json

from models import TravelRequest, CompleteTravelPlan
from services import LLMService, SessionManager
from tools import get_travel_tools


class AgentState(TypedDict):
    """State for the travel planning agent"""
    travel_request: TravelRequest
    places_info: Optional[str]
    weather_info: Optional[str]
    budget_info: Optional[str]
    itinerary_info: Optional[str]
    trip_summary: Optional[str]
    final_plan: Optional[CompleteTravelPlan]
    error_message: Optional[str]
    current_step: str


class TravelPlanningAgent:
    """
    Travel Planning Agent using LangGraph workflow
    Implements singleton pattern for consistent agent behavior
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.llm_service = LLMService()
            self.session_manager = SessionManager()
            self.tools = get_travel_tools()
            self._initialized = True

    def should_continue(self, state: AgentState) -> str:
        """Determine the next step in the workflow"""
        current_step = state.get("current_step", "start")

        if current_step == "start":
            return "search_places"
        elif current_step == "search_places" and state.get("places_info"):
            return "get_weather"
        elif current_step == "get_weather" and state.get("weather_info"):
            return "calculate_budget"
        elif current_step == "calculate_budget" and state.get("budget_info"):
            return "create_itinerary"
        elif current_step == "create_itinerary" and state.get("itinerary_info"):
            return "create_summary"
        elif current_step == "create_summary" and state.get("trip_summary"):
            return "finalize_plan"
        elif current_step == "finalize_plan":
            return "end"
        else:
            return "error"

    def search_places_node(self, state: AgentState) -> AgentState:
        """Search for places and attractions"""
        try:
            travel_request = state["travel_request"]

            # Use places tool
            places_tool = next(tool for tool in self.tools if tool.name == "places_search")
            places_info = places_tool._run(
                destination=travel_request.destination,
                interests=travel_request.interests
            )

            state["places_info"] = places_info
            state["current_step"] = "search_places"
            return state

        except Exception as e:
            state["error_message"] = f"Error searching places: {str(e)}"
            state["current_step"] = "error"
            return state

    def get_weather_node(self, state: AgentState) -> AgentState:
        """Get weather information"""
        try:
            travel_request = state["travel_request"]

            # Use weather tool
            weather_tool = next(tool for tool in self.tools if tool.name == "weather_info")
            weather_info = weather_tool._run(
                location=travel_request.destination,
                start_date=travel_request.start_date,
                end_date=travel_request.end_date
            )

            state["weather_info"] = weather_info
            state["current_step"] = "get_weather"
            return state

        except Exception as e:
            state["error_message"] = f"Error getting weather: {str(e)}"
            state["current_step"] = "error"
            return state

    def calculate_budget_node(self, state: AgentState) -> AgentState:
        """Calculate budget information"""
        try:
            travel_request = state["travel_request"]

            # Use budget tool
            budget_tool = next(tool for tool in self.tools if tool.name == "budget_calculator")
            budget_info = budget_tool._run(
                destination=travel_request.destination,
                duration=travel_request.num_days,
                travel_style=travel_request.travel_style,
                currency=travel_request.currency
            )

            state["budget_info"] = budget_info
            state["current_step"] = "calculate_budget"
            return state

        except Exception as e:
            state["error_message"] = f"Error calculating budget: {str(e)}"
            state["current_step"] = "error"
            return state

    def create_itinerary_node(self, state: AgentState) -> AgentState:
        """Create detailed itinerary"""
        try:
            travel_request = state["travel_request"]

            # Use itinerary tool
            itinerary_tool = next(tool for tool in self.tools if tool.name == "itinerary_creator")
            itinerary_info = itinerary_tool._run(
                destination=travel_request.destination,
                duration=travel_request.num_days,
                interests=travel_request.interests,
                budget=state.get("budget_info", "moderate budget")
            )

            state["itinerary_info"] = itinerary_info
            state["current_step"] = "create_itinerary"
            return state

        except Exception as e:
            state["error_message"] = f"Error creating itinerary: {str(e)}"
            state["current_step"] = "error"
            return state

    def create_summary_node(self, state: AgentState) -> AgentState:
        """Create trip summary and checklist"""
        try:
            # Use summary tool
            summary_tool = next(tool for tool in self.tools if tool.name == "trip_summary")
            trip_summary = summary_tool._run(
                itinerary=state.get("itinerary_info", ""),
                weather=state.get("weather_info", ""),
                budget=state.get("budget_info", ""),
                places=state.get("places_info", "")
            )

            state["trip_summary"] = trip_summary
            state["current_step"] = "create_summary"
            return state

        except Exception as e:
            state["error_message"] = f"Error creating summary: {str(e)}"
            state["current_step"] = "error"
            return state

    def finalize_plan_node(self, state: AgentState) -> AgentState:
        """Finalize the complete travel plan"""
        try:
            travel_request = state["travel_request"]

            # Combine all information into final plan
            prompt = f"""
            Create a comprehensive travel plan based on the following information:

            Travel Request: {travel_request.json()}
            Places Information: {state.get("places_info", "")}
            Weather Information: {state.get("weather_info", "")}
            Budget Information: {state.get("budget_info", "")}
            Itinerary Information: {state.get("itinerary_info", "")}
            Trip Summary: {state.get("trip_summary", "")}

            Combine all this information into a single, comprehensive travel plan.
            Provide the response as structured text that can be parsed into a CompleteTravelPlan object.
            """

            final_response = self.llm_service.process(prompt)

            # Create a basic CompleteTravelPlan
            # In a full implementation, this would parse the LLM response more thoroughly
            from models import (
                PlacesResponse, WeatherResponse, FullItinerary,
                DayPlan, CompleteTravelPlan
            )

            # Parse places info
            try:
                places_dict = json.loads(state.get("places_info", "{}"))
                places_response = PlacesResponse(**places_dict)
            except:
                places_response = PlacesResponse(
                    attractions=[f"Attractions in {travel_request.destination}"],
                    restaurants=[f"Restaurants in {travel_request.destination}"],
                    activities=[f"Activities in {travel_request.destination}"],
                    transportation=[f"Transportation in {travel_request.destination}"],
                    summary=f"Information about {travel_request.destination}"
                )

            # Parse weather info
            try:
                weather_dict = json.loads(state.get("weather_info", "{}"))
                weather_response = WeatherResponse(**weather_dict)
            except:
                weather_response = WeatherResponse(
                    current_weather="Check local weather",
                    forecast=["Variable conditions expected"],
                    temperature_range="Check local forecasts",
                    recommendations=["Pack for variable weather"]
                )

            # Create basic itinerary
            daily_plans = []
            for day in range(1, travel_request.num_days + 1):
                daily_plan = DayPlan(
                    day=day,
                    title=f"Day {day} in {travel_request.destination}",
                    morning=f"Morning activities for day {day}",
                    afternoon=f"Afternoon activities for day {day}",
                    evening=f"Evening activities for day {day}",
                    estimated_cost=f"${travel_request.budget / travel_request.num_days:.0f}",
                    travel_tips=[f"Tip for day {day}"]
                )
                daily_plans.append(daily_plan)

            itinerary = FullItinerary(
                destination=travel_request.destination,
                total_days=travel_request.num_days,
                daily_plans=daily_plans,
                emergency_contacts=["Local emergency services"],
                local_tips=["Local customs and tips"],
                budget_breakdown={
                    "total": f"{travel_request.budget} {travel_request.currency}",
                    "daily": f"{travel_request.budget / travel_request.num_days:.0f} {travel_request.currency}"
                }
            )

            # Create final plan
            final_plan = CompleteTravelPlan(
                trip_overview=f"Complete travel plan for {travel_request.destination}",
                weather_forecast=weather_response,
                places_info=places_response,
                itinerary=itinerary,
                budget_summary={
                    "total": f"{travel_request.budget} {travel_request.currency}",
                    "daily": f"{travel_request.budget / travel_request.num_days:.0f} {travel_request.currency}",
                    "currency": travel_request.currency
                },
                practical_info=["Check passport validity", "Research visa requirements"],
                final_checklist=["Book accommodation", "Arrange transportation", "Pack essentials"]
            )

            state["final_plan"] = final_plan
            state["current_step"] = "finalize_plan"
            return state

        except Exception as e:
            state["error_message"] = f"Error finalizing plan: {str(e)}"
            state["current_step"] = "error"
            return state

    def error_node(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow"""
        error_msg = state.get("error_message", "Unknown error occurred")
        print(f"Agent Error: {error_msg}")
        return state

    def plan_trip(self, travel_request: TravelRequest, user_id: str = "default") -> CompleteTravelPlan:
        """
        Main method to plan a trip using the agent workflow
        """
        # Initialize state
        state = AgentState(
            travel_request=travel_request,
            places_info=None,
            weather_info=None,
            budget_info=None,
            itinerary_info=None,
            trip_summary=None,
            final_plan=None,
            error_message=None,
            current_step="start"
        )

        # Execute workflow steps
        steps = {
            "search_places": self.search_places_node,
            "get_weather": self.get_weather_node,
            "calculate_budget": self.calculate_budget_node,
            "create_itinerary": self.create_itinerary_node,
            "create_summary": self.create_summary_node,
            "finalize_plan": self.finalize_plan_node,
            "error": self.error_node
        }

        # Run workflow
        while state["current_step"] != "end":
            next_step = self.should_continue(state)

            if next_step == "end":
                break
            elif next_step in steps:
                state = steps[next_step](state)
            else:
                state["error_message"] = f"Unknown step: {next_step}"
                state = self.error_node(state)
                break

        # Create session if we have a final plan
        if state.get("final_plan"):
            session_id = self.session_manager.create_session(user_id, travel_request)
            self.session_manager.update_session(session_id, state["final_plan"])
            return state["final_plan"]
        else:
            # Return a basic error plan
            from models import (
                PlacesResponse, WeatherResponse, FullItinerary,
                CompleteTravelPlan
            )

            error_plan = CompleteTravelPlan(
                trip_overview=f"Error planning trip: {state.get('error_message', 'Unknown error')}",
                weather_forecast=WeatherResponse(
                    current_weather="Unable to fetch weather",
                    forecast=["Check local weather services"],
                    temperature_range="N/A",
                    recommendations=["Check weather before departure"]
                ),
                places_info=PlacesResponse(
                    attractions=["Unable to fetch attractions"],
                    restaurants=["Unable to fetch restaurants"],
                    activities=["Unable to fetch activities"],
                    transportation=["Check local transportation"],
                    summary="Error fetching destination information"
                ),
                itinerary=FullItinerary(
                    destination=travel_request.destination,
                    total_days=travel_request.num_days,
                    daily_plans=[],
                    emergency_contacts=["Contact local authorities"],
                    local_tips=["Research destination independently"],
                    budget_breakdown={"error": "Unable to calculate budget"}
                ),
                budget_summary={"error": "Budget calculation failed"},
                practical_info=["Plan manually due to system error"],
                final_checklist=["Verify all information independently"]
            )

            return error_plan


# Singleton instance for global access
travel_agent = TravelPlanningAgent()
