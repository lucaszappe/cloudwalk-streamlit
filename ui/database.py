"""
Neo4j database connection and query execution utilities.

This module handles the connection to Neo4j Aura DB and provides methods for
executing Cypher queries and formatting results.
"""

import os
import streamlit as st
from neo4j import GraphDatabase


class Neo4jConnection:
    """Handle Neo4j database connections and query execution."""
    
    def __init__(self, uri, username, password):
        """Initialize Neo4j connection parameters."""
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None

    def connect(self):
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            st.error(f"❌ Failed to connect to Neo4j: {str(e)}")
            return False

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()

    def run_query(self, query, parameters=None):
        """Execute a Cypher query and return formatted results."""
        if not self.driver:
            raise Exception("Database connection not established")
        
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            records = []
            
            for record in result:
                record_dict = {}
                
                for key, value in record.items():
                    if hasattr(value, "labels"):  # Neo4j Node
                        record_dict[key] = self._format_node(value)
                    elif hasattr(value, "type"):  # Neo4j Relationship
                        record_dict[key] = self._format_relationship(value)
                    elif hasattr(value, "nodes") and hasattr(value, "relationships"):  # Neo4j Path
                        record_dict[key] = self._format_path(value)
                    else:  # primitive value
                        record_dict[key] = value
                
                records.append(record_dict)
            
            return records

    def _format_node(self, node):
        """Format a Neo4j Node object for serialization."""
        return {
            "id": node.element_id,
            "labels": list(node.labels),
            "name": node.get("name", str(node.element_id)),
            **dict(node)
        }

    def _format_relationship(self, relationship):
        """Format a Neo4j Relationship object for serialization."""
        return {
            "type": relationship.type,
            "start": relationship.start_node.element_id,
            "end": relationship.end_node.element_id,
            **dict(relationship)
        }

    def _format_path(self, path):
        """Format a Neo4j Path object for serialization."""
        path_nodes = [self._format_node(node) for node in path.nodes]
        path_relationships = [self._format_relationship(rel) for rel in path.relationships]
        
        return {
            "path_type": "neo4j_path",
            "nodes": path_nodes,
            "relationships": path_relationships,
            "length": len(path.relationships),
            "path_summary": f"Path with {len(path_nodes)} nodes and {len(path_relationships)} relationships"
        }


@st.cache_resource
def get_neo4j_connection():
    """Get cached Neo4j connection instance."""
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, username, password]):
        st.error("❌ Neo4j credentials not found in environment variables")
        st.info("Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in your .env file")
        return None
    
    conn = Neo4jConnection(uri, username, password)
    if conn.connect():
        return conn
    return None


def execute_query(conn, query):
    """Execute a user-initiated query with error handling."""
    try:
        with st.spinner("🔄 Executing query..."):
            results = conn.run_query(query)
            st.session_state.current_results = results
            if query not in st.session_state.query_history:
                st.session_state.query_history.append(query)
        return results, None
    except Exception as e:
        error_msg = f"❌ Query failed: {str(e)}"
        return None, error_msg


def handle_auto_execute(conn, query, show_network_message=False):
    """Handle auto-execution from sidebar buttons."""
    try:
        with st.spinner("🔄 Loading query..."):
            results = conn.run_query(query)
            st.session_state.current_results = results
            if query not in st.session_state.query_history:
                st.session_state.query_history.append(query)
        return results, show_network_message
    except Exception as e:
        error_msg = f"❌ Query failed: {str(e)}"
        return None, error_msg
