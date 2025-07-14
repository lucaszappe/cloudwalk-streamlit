"""
UI components for the Dark Souls Knowledge Graph Explorer.

This module contains reusable UI components for rendering different views
and handling user interactions.
"""

import streamlit as st
import pandas as pd
from queries import get_quick_action_queries
from database import handle_auto_execute
from visualization import create_network_visualization, render_network_visualization, display_graph_legend
from utils import has_graph_objects, extract_nodes_and_relationships, create_dataframe_from_results


def render_sidebar(conn):
    """Render the application sidebar with quick actions."""
    if conn:
        st.sidebar.success("✅ Connected to Neo4j Aura DB")
    else:
        st.sidebar.error("❌ Not connected to database")
        return False
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📍 Quick Actions")
    
    # get quick action queries
    quick_actions = get_quick_action_queries()
    
    # render buttons for each quick action
    for action_key, action_data in quick_actions.items():
        if st.sidebar.button(action_data["button_text"], use_container_width=True):
            st.session_state.query_text = action_data["query"]
            st.session_state.auto_execute = True
            st.session_state.show_network_message = action_data["show_network_message"]
            st.rerun()
    
    return True


def render_query_interface(conn):
    """Render the main query interface."""
    st.markdown("### 💻 Cypher Query Interface")
    
    # query input text area
    query = st.text_area(
        "Enter your query:",
        value=st.session_state.query_text,
        height=150,
        help="Write a Cypher query to explore the Dark Souls knowledge graph",
        key="query_input"
    )
    
    # update session state if query changed
    if query != st.session_state.query_text:
        st.session_state.query_text = query
    
    # query execution buttons
    col1, col2, col3 = st.columns([2, 1, 6])
    with col1:
        execute_query = st.button("🚀 Execute Query", type="primary")
    with col2:
        clear_button = st.button("🧹 Clear", key="clear_btn")
    
    # handle clear button
    if clear_button:
        st.session_state.query_text = ""
        st.rerun()
    
    # handle query execution
    if execute_query and query and query.strip():
        _execute_query_handler(conn, query)
    elif hasattr(st.session_state, "auto_execute") and st.session_state.auto_execute and query and query.strip():
        _handle_auto_execute_handler(conn, query)
    elif st.session_state.current_results is not None:
        st.info("📊 Showing previous query results. Execute a new query to update.")
        render_query_results(st.session_state.current_results)


def _execute_query_handler(conn, query):
    """Handle user-initiated query execution."""
    from database import execute_query
    
    results, error = execute_query(conn, query)
    if error:
        st.error(error)
        st.info("💡 **Tip:** Check your Cypher syntax and ensure the query is valid")
    else:
        st.success(f"✅ Query executed successfully! Found {len(results or [])} results.")
        render_query_results(results)


def _handle_auto_execute_handler(conn, query):
    """Handle auto-execution from sidebar buttons."""
    st.session_state.auto_execute = False
    show_network_message = getattr(st.session_state, "show_network_message", False)
    st.session_state.show_network_message = False
    
    results, error = handle_auto_execute(conn, query, show_network_message)
    if isinstance(error, str):  # error case
        st.error(error)
    else:
        if show_network_message:
            st.success(f"✅ Sample network loaded! Found {len(results or [])} relationships.")
            render_query_results(results, auto_select_network=True)
        else:
            st.success(f"✅ Query executed successfully! Found {len(results or [])} results.")
            render_query_results(results)


def render_query_results(results, auto_select_network=False):
    """Render query results with appropriate visualizations."""
    if not results:
        st.warning("⚠️ No results returned from query")
        return
    
    st.markdown("### 📊 Query Results")
    
    # determine if we have Neo4j objects for visualization
    has_neo4j_objects = has_graph_objects(results)
    
    # show helpful message for network visualization
    if auto_select_network and has_neo4j_objects:
        st.info("🌐 **Network visualization ready!** The 'Graph' tab below shows the interactive graph.")
    
    # create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Table", "🌐 Graph", "🔍 Raw Data"])
    
    with tab1:
        _render_table_view(results, has_neo4j_objects)
    
    with tab2:
        _render_graph_view(results)
    
    with tab3:
        _render_raw_data_view(results)


def _render_table_view(results, has_neo4j_objects):
    """Render the table view of query results."""
    if has_neo4j_objects:
        st.info("📋 Converting Neo4j objects to table format:")
        
        df = create_dataframe_from_results(results, has_neo4j_objects=True)
        
        if df is not None:
            st.dataframe(df, use_container_width=True, height=400)
            st.info(f"📊 Showing {len(df)} records with {len(df.columns)} columns")
        else:
            st.warning("⚠️ No data could be extracted for table view")
    else:
        # for regular tabular data, create dataframe
        try:
            df = create_dataframe_from_results(results, has_neo4j_objects=False)
            st.dataframe(df, use_container_width=True)
            st.info(f"📊 Showing {len(df)} records with {len(df.columns)} columns")
            
        except Exception as e:
            st.error(f"❌ Error creating table: {str(e)}")
            # fallback to simple display
            st.write("**Query Results:**")
            for i, record in enumerate(results[:10]):
                st.write(f"**Record {i+1}:** {record}")


def _render_graph_view(results):
    """Render the graph visualization view."""
    # extract nodes and relationships for network visualization
    nodes, relationships = extract_nodes_and_relationships(results)
    
    if nodes or relationships:
        _display_graph_statistics(nodes, relationships)
        
        # render the network
        html_content, nodes_rendered, edges_rendered = create_network_visualization(nodes, relationships)
        render_network_visualization(html_content, nodes_rendered, edges_rendered)
        
        # display the graph legend
        display_graph_legend()
        
    else:
        st.warning("🌐 **No graph data to visualize**")
        st.info("""
        💡 **To see a graph visualization, try queries that return Neo4j objects:**
        
        **✅ Good for visualization:**
        ```cypher
        MATCH (c:Character)-[r]-(other)
        RETURN c, r, other
        LIMIT 20
        ```
        
        **❌ Not for visualization:**
        ```cypher
        MATCH (c:Character)-[r]-(other)
        RETURN c.name AS Character, type(r) AS Relationship
        ```
        
        The first query returns actual graph objects (nodes & relationships), while the second returns just text values.
        """)


def _display_graph_statistics(nodes, relationships):
    """Display statistics about the graph data."""
    st.success(f"✅ Found {len(nodes)} nodes and {len(relationships)} relationships")
    
    # show network stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nodes", len(nodes))
    with col2:
        st.metric("Relationships", len(relationships))
    with col3:
        if nodes:
            node_types = {}
            for node in nodes:
                node_type = node.get("type", "Unknown")
                node_types[node_type] = node_types.get(node_type, 0) + 1
            st.metric("Node Types", len(node_types))
    
    # show node type distribution
    if nodes:
        node_types = {}
        for node in nodes:
            node_type = node.get("type", "Unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        st.write("🏷️ **Node Types:**")
        type_cols = st.columns(min(len(node_types), 4))
        for i, (node_type, count) in enumerate(node_types.items()):
            with type_cols[i % len(type_cols)]:
                st.write(f"**{node_type}:** {count}")


def _render_raw_data_view(results):
    """Render the raw data tab."""
    st.markdown("### 🔍 Raw Query Results")
    st.info("This shows the raw JSON data returned from Neo4j for analysis and inspection purposes.")
    st.json(results)
