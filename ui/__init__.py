"""
Dark Souls Knowledge Graph Explorer UI Package

This package contains the modular components for the Streamlit-based
Dark Souls Knowledge Graph Explorer application.

Modules:
- config: Application configuration and setup
- database: Neo4j connection and query handling
- visualization: Graph visualization utilities
- components: UI components and rendering
- queries: Sample queries and query utilities
- utils: Utility functions for data processing
- main: Main application entry point
"""

from .main import main

__version__ = "1.0.0"
__all__ = ["main"]
