"""
Graph visualization utilities using PyVis for interactive network displays.

This module handles the creation and rendering of interactive network visualizations
from Neo4j graph data.
"""

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network


# node color scheme for graph visualization
NODE_COLORS = {
    "Character": "#4ECDC4",
    "Location": "#FF6B9D",
    "Group": "#C7EA46"
}


def create_network_visualization(nodes, relationships):
    """Create an interactive network visualization using PyVis."""
    try:
        # initialize PyVis network with better sizing
        net = Network(
            height="600px",
            width="100%",
            bgcolor="#ffffff",
            font_color=False,
            directed=True
        )
        
        # configure physics and interaction options for better centering
        net.set_options(_get_network_options())
        
        # prepare nodes and create node lookup
        node_lookup, all_nodes = _prepare_nodes_for_visualization(nodes, relationships)
        
        # add nodes to network
        nodes_added = _add_nodes_to_network(net, all_nodes)
        
        # add edges to network
        edges_added = _add_edges_to_network(net, relationships, node_lookup)
        
        if nodes_added == 0:
            return None, 0, 0
        
        # generate HTML visualization
        html_string = _generate_html(net)
        
        return html_string, nodes_added, edges_added
            
    except Exception as e:
        st.error(f"❌ Error creating PyVis network: {str(e)}")
        return None, 0, 0


def _get_network_options():
    """Get PyVis network configuration options."""
    return """
    {
        "physics": {
            "enabled": true,
            "stabilization": {
                "iterations": 200,
                "fit": true
            },
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 80,
                "springConstant": 0.04,
                "damping": 0.15,
                "avoidOverlap": 0.2
            }
        },
        "interaction": {
            "navigationButtons": true,
            "keyboard": true,
            "zoomView": true,
            "dragView": true,
            "hideEdgesOnDrag": false,
            "hideNodesOnDrag": false
        },
        "layout": {
            "improvedLayout": true,
            "clusterThreshold": 150
        },
        "configure": {
            "enabled": false
        }
    }
    """


def _prepare_nodes_for_visualization(nodes, relationships):
    """Prepare node data for visualization, including missing referenced nodes."""
    node_lookup = {}
    all_nodes = []
    
    # process existing nodes
    for i, node in enumerate(nodes):
        node_id = str(node.get("name", node.get("id", f"node_{i}")))
        node_lookup[node_id] = node
        all_nodes.append((node_id, node))
    
    # add missing nodes referenced in relationships
    for rel in relationships:
        source_id = str(rel.get("source", rel.get("start", "")))
        target_id = str(rel.get("target", rel.get("end", "")))
        
        for node_id in [source_id, target_id]:
            if node_id and node_id not in node_lookup:
                missing_node = {"id": node_id, "name": node_id, "type": "Referenced"}
                node_lookup[node_id] = missing_node
                all_nodes.append((node_id, missing_node))
    
    return node_lookup, all_nodes


def _get_node_color_and_type(node):
    """Determine node color and standardized type."""
    raw_type = node.get("type", "Unknown")
    node_type = raw_type.split("/")[0] if "/" in raw_type else raw_type
    
    # standardize common misspellings
    if node_type.lower() in ["character", "charcter"]:
        node_type = "Character"
    elif node_type.lower() in ["location", "locaton"]:
        node_type = "Location"
    elif node_type.lower() in ["group", "groupe"]:
        node_type = "Group"
    
    color = NODE_COLORS.get(node_type, "#95A5A6")  # default gray color for unknown types
    return color, node_type


def _add_nodes_to_network(net, all_nodes):
    """Add nodes to the PyVis network."""
    nodes_added = 0
    
    for node_id, node in all_nodes:
        name = str(node.get("name", node_id))
        color, node_type = _get_node_color_and_type(node)
        
        # create node title with description
        title = f"Name: {name}\nType: {node_type}"
        if node.get("description"):
            desc = str(node["description"])
            if len(desc) > 100:
                desc = desc[:100] + "..."
            title += f"\nDescription: {desc}"
        
        net.add_node(
            node_id,
            label=name,
            color=color,
            size=25,
            title=title,
            font={"color": "black", "size": 14}
        )
        nodes_added += 1
    
    return nodes_added


def _add_edges_to_network(net, relationships, node_lookup):
    """Add edges to the PyVis network."""
    edges_added = 0
    
    for rel in relationships:
        source_id = str(rel.get("source", rel.get("start", "")))
        target_id = str(rel.get("target", rel.get("end", "")))
        rel_type = rel.get("type", "RELATED_TO")
        
        if source_id in node_lookup and target_id in node_lookup:
            net.add_edge(
                source_id,
                target_id,
                label=rel_type,
                color="#888888",
                width=2,
                title=f"{source_id} --{rel_type}--> {target_id}"
            )
            edges_added += 1
    
    return edges_added


def _generate_html(net):
    """Generate HTML visualization for the PyVis network."""
    try:
        html_string = net.generate_html()
        return html_string
    except Exception as e:
        st.error(f"❌ Error generating PyVis HTML: {str(e)}")
        return None


def render_network_visualization(html_content, nodes_rendered, edges_rendered):
    """Render the network visualization in Streamlit."""
    if html_content:
        st.info(f"🎨 Rendering interactive network with {nodes_rendered} nodes and {edges_rendered} edges")
        # enable scrolling for better PyVis interactivity
        components.html(html_content, height=650, scrolling=True)
        return True
    else:
        st.error("❌ Failed to create network visualization")
        return False


def display_graph_legend():
    """Display a color legend for the graph visualization."""
    st.markdown("#### 🎨 Graph Legend")
    
    # create columns for the legend
    cols = st.columns(len(NODE_COLORS))
    
    for i, (node_type, color) in enumerate(NODE_COLORS.items()):
        with cols[i]:
            # create colored circle using HTML/CSS
            circle_html = f"""
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="
                    width: 20px; 
                    height: 20px; 
                    border-radius: 50%; 
                    background-color: {color};
                    border: 2px solid #333;
                    flex-shrink: 0;
                "></div>
                <span style="font-weight: 600; color: #333;">{node_type}</span>
            </div>
            """
            st.markdown(circle_html, unsafe_allow_html=True)
