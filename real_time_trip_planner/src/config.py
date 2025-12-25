# config.py - Configuration and Environment Setup
import os
from dotenv import load_dotenv
from typing import Dict, Any


class Config:
    """Configuration class for environment variables and settings"""

    def __init__(self):
        load_dotenv()
        self._validate_env_vars()

    def _validate_env_vars(self):
        """Validate required environment variables"""
        required_vars = ["GOOGLE_API_KEY", "OPENWEATHERMAP_API_KEY"]
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

    @property
    def google_api_key(self) -> str:
        return os.getenv("GOOGLE_API_KEY")

    @property
    def openweather_api_key(self) -> str:
        return os.getenv("OPENWEATHERMAP_API_KEY")

    @property
    def llm_model(self) -> str:
        return os.getenv("LLM_MODEL", "gemini-2.5-pro")

    @property
    def default_currency(self) -> str:
        return os.getenv("DEFAULT_CURRENCY", "USD")

    @property
    def exchange_rates(self) -> Dict[str, float]:
        """Static exchange rates (in production, use live API)"""
        return {
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

    @property
    def budget_breakdown(self) -> Dict[str, float]:
        """Default budget breakdown percentages"""
        return {
            'accommodation': 0.4,
            'food': 0.3,
            'activities': 0.2,
            'transport': 0.1
        }

    @property
    def city_cost_estimates(self) -> Dict[str, int]:
        """Daily cost estimates for popular cities (USD)"""
        return {
            # Expensive European cities
            'paris': 180, 'london': 200, 'zurich': 250, 'stockholm': 190,
            # Expensive Asian cities
            'tokyo': 150, 'singapore': 140, 'hong kong': 160,
            # Expensive US cities
            'new york': 220, 'san francisco': 230, 'los angeles': 180,
            # Budget-friendly Asian cities
            'bangkok': 60, 'delhi': 40, 'mumbai': 45, 'jakarta': 50,
            # South American cities
            'buenos aires': 80, 'lima': 70, 'bogota': 65,
            # Default
            'default': 120
        }


# Singleton instance
config = Config()
