# Travel Planner AI Agent

A sophisticated AI-powered travel planning application built with Object-Oriented Programming principles, featuring singleton design patterns, LangGraph StateGraph workflow orchestration, and professional Streamlit user interfaces.

## Architecture Overview

This application has been completely restructured from a Jupyter notebook into a modular, enterprise-grade OOP architecture with the following components:

### Core Components

- **models.py**: Pydantic data models and abstract base classes for type safety
- **config.py**: Configuration management with environment variable validation
- **services.py**: Service layer with singleton pattern implementation for resource efficiency
- **tools.py**: LangChain tool classes with circular import resolution
- **langgraph_agent.py**: LangGraph StateGraph implementation for workflow orchestration
- **app.py**: Modular Streamlit UI with LangGraph integration
- **streamlit_app_langgraph.py**: Complete standalone application with embedded LangGraph

## Features

### Core Functionality

- **AI-Powered Planning**: Uses Google Gemini 2.5 Pro for intelligent travel recommendations
- **LangGraph StateGraph**: Advanced workflow orchestration with state management
- **Weather Integration**: Real-time weather data from OpenWeatherMap API
- **Smart Budget Calculation**: Automatic budget estimation based on destination and travel preferences
- **Multi-Currency Support**: Real-time currency conversion with configurable rates

### Architecture Features

- **Singleton Design Pattern**: Ensures single instance per user session for consistent state management
- **Professional UI**: Clean Streamlit interface without visual distractions
- **Session Management**: Persistent user sessions with travel history and state restoration
- **Modular Design**: Clean separation of concerns following SOLID principles
- **Error Handling**: Comprehensive exception handling with graceful fallbacks
- **Type Safety**: Full Pydantic model validation for data integrity

## Project Structure

```
real_time_trip_planner/
├── src/                         # Source code directory
│   ├── __init__.py             # Package initialization
│   ├── models.py               # Pydantic models and abstract base classes
│   ├── config.py               # Configuration and environment management
│   ├── services.py             # Service layer with singleton patterns
│   ├── tools.py                # LangChain tool implementations
│   ├── langgraph_agent.py      # LangGraph StateGraph workflow implementation
│   ├── app.py                  # Modular Streamlit UI application
│   ├── streamlit_app_langgraph.py # Complete standalone application
│   ├── agent.py                # Legacy agent implementation
│   └── streamlit_travel_planner.py # Alternative UI implementation
├── run_app.py                  # Python launcher script
├── run_app.sh                  # Bash launcher script
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── .env                        # Environment variables (create this)
├── requirements.txt            # Python dependencies
├── __init__.py                 # Package initialization
└── README.md                   # Documentation
```

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project directory:

```env
# Required API Keys
GOOGLE_API_KEY=your_google_gemini_api_key
OPENWEATHERMAP_API_KEY=your_openweather_api_key
OWM_key=your_openweather_api_key

# Optional Configuration
LLM_MODEL=gemini-2.5-pro
DEFAULT_CURRENCY=USD
DEFAULT_TRAVEL_STYLE=mid-range
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

**Option 1: Using the Bash Script (Recommended)**

```bash
# Make the script executable (first time only)
chmod +x run_app.sh

# Run the application
./run_app.sh
```

**Option 2: Using the Python Script**

```bash
python run_app.py
```

**Option 3: Manual Method**

```bash
# Change to the src directory
cd src

# Run the modular application
streamlit run app.py

# OR run the standalone application
streamlit run streamlit_app_langgraph.py
```

## Architecture Details

### LangGraph StateGraph Implementation

The application uses LangGraph StateGraph for advanced workflow orchestration:

```python
class TravelPlannerState(TypedDict):
    """State for travel planning workflow"""
    messages: List
    travel_request: TravelRequest
    budget_info: dict
    current_step: str
```

**StateGraph Nodes:**

- **Agent Node**: Main conversation and planning logic
- **Tool Node**: Execute travel planning tools
- **Budget Node**: Calculate and validate budgets
- **Workflow Orchestration**: Conditional routing between nodes

### Singleton Pattern Implementation

Enterprise-grade singleton implementation for:

- **LLMService**: Google Gemini integration with tool binding
- **SearchService**: DuckDuckGo search functionality
- **WeatherService**: OpenWeatherMap integration
- **BudgetService**: Budget calculation and currency conversion
- **SessionManager**: User session and state management
- **TravelPlanningService**: Main orchestration service

### Data Models Architecture

**Core Models:**

- **TravelRequest**: User input validation and type safety

  ```python
  class TravelRequest(BaseModel):
      destination: str
      start_date: str
      end_date: str
      budget: float
      currency: str
      preferences: List[str]
      num_days: int
  ```
- **CompleteTravelPlan**: Structured travel plan output
- **UserSession**: Session management with persistence
- **PlacesResponse**: Structured location data
- **WeatherResponse**: Weather forecast and recommendations

### Service Layer Architecture

**Service Classes with Singleton Pattern:**

- **LLMService**: AI language model interactions with tool binding
- **SearchService**: Web search capabilities with result formatting
- **WeatherService**: Weather data retrieval and analysis
- **BudgetService**: Budget calculation with currency conversion
- **SessionManager**: User session lifecycle management
- **TravelPlanningService**: Main orchestration and workflow

### Tool Implementation

**LangChain Tools with Error Handling:**

- **Travel Plan Tool**: Comprehensive travel plan generation
- **Budget Calculation Tool**: Smart budget estimation
- **Weather Tool**: Real-time weather data
- **Search Tool**: Location and attraction research

## Configuration Management

The application uses a centralized configuration class:

```python
class Config:
    """Configuration class for environment variables and settings"""

    @property
    def google_api_key(self) -> str
    @property
    def openweather_api_key(self) -> str
    @property
    def llm_model(self) -> str
    @property
    def exchange_rates(self) -> Dict[str, float]
```

**Features:**

- Environment variable validation
- API key management
- Multi-currency exchange rates
- Budget estimation parameters
- Travel style configurations

## User Interface Features

### Streamlit UI Components

**Core Interface Elements:**

- Travel planning form with validation
- Budget summary with breakdown visualization
- Session management sidebar
- Export functionality for travel plans
- Professional layout without visual distractions

**Advanced Features:**

- Session state persistence
- User session history
- Travel plan export (JSON format)
- Responsive design
- Error handling with user feedback

## Workflow Architecture

1. **User Input**: Travel preferences via validated Streamlit form
2. **Request Processing**: TravelRequest model validation and sanitization
3. **LangGraph Orchestration**: StateGraph manages workflow execution
4. **Service Coordination**: Singleton services handle API interactions
5. **AI Integration**: LLM processes and structures intelligent responses
6. **Plan Generation**: CompleteTravelPlan model assembly
7. **Session Persistence**: SessionManager stores user data
8. **UI Rendering**: Streamlit displays interactive travel plan

## Development Guidelines

### Adding New Services

1. Create service class inheriting from `BaseService`
2. Implement singleton metaclass pattern
3. Add comprehensive error handling
4. Register in service registry

### Adding New Tools

1. Create tool function with `@tool` decorator
2. Define input schema with Pydantic models
3. Implement execution logic with error handling
4. Register in tool collection

### Extending Models

1. Add new Pydantic models to `models.py`
2. Update related services and validation
3. Modify UI components for new data structures
4. Maintain backward compatibility

## Error Handling and Validation

### Comprehensive Error Management

- **Input Validation**: Pydantic model validation
- **API Error Handling**: Graceful fallbacks for service failures
- **State Management**: Session recovery and consistency
- **User Feedback**: Clear error messages and guidance

### Security Features

- API keys stored in environment variables
- Input sanitization through Pydantic models
- Error messages without sensitive data exposure
- Secure session management

## Testing and Quality Assurance

### Code Quality Features

- Type hints throughout codebase
- Pydantic model validation
- Singleton pattern ensures consistency
- Modular architecture for testability
- Comprehensive error handling

### Future Testing Implementation

```bash
# When implemented
pytest tests/
python -m pytest --cov=real_time_trip_planner
```

## Deployment Architecture

### Local Development

```bash
streamlit run app.py
# or
streamlit run streamlit_app_langgraph.py
```

### Production Deployment Considerations

1. Environment variable management
2. Dependency installation and isolation
3. Process management (PM2, supervisor)
4. Reverse proxy configuration (nginx)
5. SSL/TLS certificate setup
6. Monitoring and logging setup

## API Documentation

### Core Service Methods

**TravelPlanningService.process()**

- **Input**: `TravelRequest`, `user_id`
- **Output**: `CompleteTravelPlan`
- **Purpose**: Main entry point for travel planning workflow

**LangGraphTravelAgent.plan_trip()**

- **Input**: Travel parameters and preferences
- **Output**: Structured travel plan with budget information
- **Purpose**: LangGraph StateGraph orchestration

**SessionManager Methods:**

- `create_session()`: Initialize new user session
- `get_session()`: Retrieve session by identifier
- `update_session()`: Update with travel plan data
- `delete_session()`: Clean session removal

## Performance Optimization

### Singleton Pattern Benefits

- Memory efficiency through single instances
- Consistent state management
- Reduced API initialization overhead
- Improved resource utilization

### LangGraph Advantages

- Efficient workflow orchestration
- State persistence across interactions
- Conditional execution paths
- Tool integration and management

## Contributing Guidelines

1. Fork the repository
2. Create feature branch with descriptive name
3. Follow OOP principles and existing patterns
4. Implement comprehensive error handling
5. Add type hints and documentation
6. Test singleton pattern functionality
7. Submit pull request with detailed description

## License

This project is licensed under the MIT License.

## Support and Troubleshooting

### Common Issues

1. **API Key Configuration**: Verify `.env` file setup
2. **Dependency Issues**: Check `requirements.txt` compatibility
3. **Service Initialization**: Review singleton pattern implementation
4. **LangGraph Errors**: Validate StateGraph configuration

### Debugging Resources

1. Configuration validation in `config.py`
2. Service health monitoring in singleton classes
3. Error logs in LangGraph StateGraph execution
4. Session state inspection tools

## Future Enhancement Roadmap

### Technical Improvements

- **Database Integration**: Persistent session storage
- **Caching Layer**: Redis for improved performance
- **API Rate Limiting**: Request throttling and queuing
- **Monitoring Dashboard**: Real-time system health metrics
- **Unit Testing Suite**: Comprehensive test coverage
- **CI/CD Pipeline**: Automated testing and deployment

### Feature Enhancements

- **Multi-language Support**: Internationalization framework
- **Advanced AI Models**: Integration with multiple LLM providers
- **Real-time Updates**: Live data feeds and notifications
- **Collaboration Features**: Shared travel planning
- **Mobile Optimization**: Responsive design improvements
- **Booking Integration**: Direct reservation capabilities

---

**Built with Python, Streamlit, LangChain, LangGraph, and Google Gemini AI**

**Architecture**: Object-Oriented Programming with Singleton Patterns and StateGraph Orchestration

- `FullItinerary`: Detailed day-by-day itinerary

### Service Layer Architecture

**Service Classes with Singleton Pattern:**

- **LLMService**: AI language model interactions with tool binding
- **SearchService**: Web search capabilities with result formatting
- **WeatherService**: Weather data retrieval and analysis
- **BudgetService**: Budget calculation with currency conversion
- **SessionManager**: User session lifecycle management
- **TravelPlanningService**: Main orchestration and workflow

### Tool Implementation

**LangChain Tools with Error Handling:**

- **Travel Plan Tool**: Comprehensive travel plan generation
- **Budget Calculation Tool**: Smart budget estimation
- **Weather Tool**: Real-time weather data
- **Search Tool**: Location and attraction research

## Configuration Management

The application uses a centralized configuration class:

```python
class Config:
    """Configuration class for environment variables and settings"""

    @property
    def google_api_key(self) -> str
    @property
    def openweather_api_key(self) -> str
    @property
    def llm_model(self) -> str
    @property
    def exchange_rates(self) -> Dict[str, float]
```

**Features:**

- Environment variable validation
- API key management
- Multi-currency exchange rates
- Budget estimation parameters
- Travel style configurations

## User Interface Features

### Streamlit UI Components

**Core Interface Elements:**

- Travel planning form with validation
- Budget summary with breakdown visualization
- Session management sidebar
- Export functionality for travel plans
- Professional layout without visual distractions

**Advanced Features:**

- Session state persistence
- User session history
- Travel plan export (JSON format)
- Responsive design
- Error handling with user feedback

## Workflow Architecture

1. **User Input**: Travel preferences via validated Streamlit form
2. **Request Processing**: TravelRequest model validation and sanitization
3. **LangGraph Orchestration**: StateGraph manages workflow execution
4. **Service Coordination**: Singleton services handle API interactions
5. **AI Integration**: LLM processes and structures intelligent responses
6. **Plan Generation**: CompleteTravelPlan model assembly
7. **Session Persistence**: SessionManager stores user data
8. **UI Rendering**: Streamlit displays interactive travel plan

## Development Guidelines

### Adding New Services

1. Create service class inheriting from `BaseService`
2. Implement singleton metaclass pattern
3. Add comprehensive error handling
4. Register in service registry

### Adding New Tools

1. Create tool function with `@tool` decorator
2. Define input schema with Pydantic models
3. Implement execution logic with error handling
4. Register in tool collection

### Extending Models

1. Add new Pydantic models to `models.py`
2. Update related services and validation
3. Modify UI components for new data structures
4. Maintain backward compatibility

## Error Handling and Validation

### Comprehensive Error Management

- **Input Validation**: Pydantic model validation
- **API Error Handling**: Graceful fallbacks for service failures
- **State Management**: Session recovery and consistency
- **User Feedback**: Clear error messages and guidance

### Security Features

- API keys stored in environment variables
- Input sanitization through Pydantic models
- Error messages without sensitive data exposure
- Secure session management

## Testing and Quality Assurance

### Code Quality Features

- Type hints throughout codebase
- Pydantic model validation
- Singleton pattern ensures consistency
- Modular architecture for testability
- Comprehensive error handling

### Future Testing Implementation

```bash
# When implemented
pytest tests/
python -m pytest --cov=real_time_trip_planner
```

## Deployment Architecture

### Local Development

```bash
streamlit run app.py
# or
streamlit run streamlit_app_langgraph.py
```

### Production Deployment Considerations

1. Environment variable management
2. Dependency installation and isolation
3. Process management (PM2, supervisor)
4. Reverse proxy configuration (nginx)
5. SSL/TLS certificate setup
6. Monitoring and logging setup

## API Documentation

### Core Service Methods

**TravelPlanningService.process()**

- **Input**: `TravelRequest`, `user_id`
- **Output**: `CompleteTravelPlan`
- **Purpose**: Main entry point for travel planning workflow

**LangGraphTravelAgent.plan_trip()**

- **Input**: Travel parameters and preferences
- **Output**: Structured travel plan with budget information
- **Purpose**: LangGraph StateGraph orchestration

**SessionManager Methods:**

- `create_session()`: Initialize new user session
- `get_session()`: Retrieve session by identifier
- `update_session()`: Update with travel plan data
- `delete_session()`: Clean session removal

## Performance Optimization

### Singleton Pattern Benefits

- Memory efficiency through single instances
- Consistent state management
- Reduced API initialization overhead
- Improved resource utilization

### LangGraph Advantages

- Efficient workflow orchestration
- State persistence across interactions
- Conditional execution paths
- Tool integration and management

## Contributing Guidelines

1. Fork the repository
2. Create feature branch with descriptive name
3. Follow OOP principles and existing patterns
4. Implement comprehensive error handling
5. Add type hints and documentation
6. Test singleton pattern functionality
7. Submit pull request with detailed description

## License

This project is licensed under the MIT License.

## Support and Troubleshooting

### Common Issues

1. **API Key Configuration**: Verify `.env` file setup
2. **Dependency Issues**: Check `requirements.txt` compatibility
3. **Service Initialization**: Review singleton pattern implementation
4. **LangGraph Errors**: Validate StateGraph configuration

### Debugging Resources

1. Configuration validation in `config.py`
2. Service health monitoring in singleton classes
3. Error logs in LangGraph StateGraph execution
4. Session state inspection tools

## Future Enhancement Roadmap

### Technical Improvements

- **Database Integration**: Persistent session storage
- **Caching Layer**: Redis for improved performance
- **API Rate Limiting**: Request throttling and queuing
- **Monitoring Dashboard**: Real-time system health metrics
- **Unit Testing Suite**: Comprehensive test coverage
- **CI/CD Pipeline**: Automated testing and deployment

### Feature Enhancements

- **Multi-language Support**: Internationalization framework
- **Advanced AI Models**: Integration with multiple LLM providers
- **Real-time Updates**: Live data feeds and notifications
- **Collaboration Features**: Shared travel planning
- **Mobile Optimization**: Responsive design improvements
- **Booking Integration**: Direct reservation capabilities

---

**Built with Python, Streamlit, LangChain, LangGraph, and Google Gemini AI**

**Architecture**: Object-Oriented Programming with Singleton Patterns and StateGraph Orchestration
