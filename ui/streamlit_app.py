"""
Dark Souls Knowledge Graph Explorer

A Streamlit application for querying and visualizing the Dark Souls Knowledge Graph 
stored in Neo4j Aura DB. Provides interactive graph exploration capabilities with 
Cypher query interface and network visualizations.

This is the main entry point that imports from modular components.
"""

import streamlit as st

# import modular components
from config import initialize_app
from database import get_neo4j_connection
from components import render_sidebar, render_query_interface


def main():
    """Main application entry point."""
    # initialize the application
    initialize_app()
    
    # render header
    st.markdown('<h1 class="main-header">⚔️ Dark Souls Knowledge Graph Explorer</h1>', unsafe_allow_html=True)
    
    # get database connection
    conn = get_neo4j_connection()
    
    # render sidebar
    if not render_sidebar(conn):
        st.stop()
    
    # render main interface
    render_query_interface(conn)


if __name__ == "__main__":
    main()
