"""
Utility functions for data processing and formatting.

This module contains helper functions for processing Neo4j results,
extracting graph objects, and other common operations.
"""

import pandas as pd


def has_graph_objects(results):
    """Check if results contain Neo4j graph objects."""
    for record in results:
        for value in record.values():
            if hasattr(value, "__class__") and (
                "Node" in str(type(value)) or 
                "Relationship" in str(type(value)) or
                (isinstance(value, dict) and (
                    "labels" in value or 
                    "type" in value or 
                    value.get("path_type") == "neo4j_path"
                ))
            ):
                return True
    return False


def extract_nodes_and_relationships(results):
    """Extract nodes and relationships from query results for visualization."""
    nodes_by_name = {}  # use name as primary key for deduplication
    relationships_by_key = {}  # use composite key for relationship deduplication
    node_id_to_name = {}  # map node IDs to names for relationship processing
    
    for record in results:
        for key, value in record.items():
            # handle Neo4j Node objects
            if hasattr(value, "__class__") and "Node" in str(type(value)):
                _process_node_for_graph(value, nodes_by_name, node_id_to_name)
            
            # handle Neo4j Relationship objects
            elif hasattr(value, "__class__") and "Relationship" in str(type(value)):
                _process_relationship_for_graph(value, relationships_by_key, node_id_to_name)
            
            # handle dictionary representations (from JSON serialization)
            elif isinstance(value, dict):
                if value.get("path_type") == "neo4j_path":
                    _process_path_for_graph(value, nodes_by_name, relationships_by_key, node_id_to_name)
                elif "labels" in value:  # node dict
                    _process_node_dict_for_graph(value, nodes_by_name, node_id_to_name, key)
                elif "type" in value and ("start" in value and "end" in value):  # relationship dict
                    _process_relationship_dict_for_graph(value, relationships_by_key, node_id_to_name)
    
    # collect all nodes and relationships
    nodes = list(nodes_by_name.values())
    relationships = list(relationships_by_key.values())
    
    # add missing nodes referenced in relationships but not explicitly returned
    _add_missing_referenced_nodes(relationships, nodes_by_name, nodes)
    
    return nodes, relationships


def _process_node_for_graph(value, nodes_by_name, node_id_to_name):
    """Process a Neo4j node for graph visualization."""
    # extract node properties
    labels = list(value.labels) if hasattr(value, "labels") else []
    props = dict(value) if hasattr(value, "items") else {}
    
    # use name as primary identifier, fallback to element_id
    node_name = props.get("name", str(value.element_id if hasattr(value, "element_id") else "unknown"))
    node_id = value.element_id if hasattr(value, "element_id") else str(value.get("id", "unknown"))
    
    # map this ID to the name for later relationship processing
    node_id_to_name[node_id] = node_name
    
    # deduplicate by name (not by id) to avoid duplicates
    if node_name not in nodes_by_name:
        node_data = {
            "id": node_name,  # use name as consistent ID
            "name": node_name,
            "type": "/".join(labels) if labels else "Unknown",
            **{k: v for k, v in props.items() if k not in ["id", "name"]}
        }
        nodes_by_name[node_name] = node_data


def _process_relationship_for_graph(value, relationships_by_key, node_id_to_name):
    """Process a Neo4j relationship for graph visualization with deduplication."""
    # extract relationship properties
    rel_type = value.type if hasattr(value, "type") else "Unknown"
    start_id = value.start_node.element_id if hasattr(value, "start_node") else str(value.get("start", ""))
    end_id = value.end_node.element_id if hasattr(value, "end_node") else str(value.get("end", ""))
    props = dict(value) if hasattr(value, "items") else {}
    
    # map IDs to names for consistent relationship references
    start_name = node_id_to_name.get(start_id, start_id)
    end_name = node_id_to_name.get(end_id, end_id)
    
    # create unique key for deduplication (source, target, type)
    rel_key = (start_name, end_name, rel_type)
    
    # only add if not already present
    if rel_key not in relationships_by_key:
        relationships_by_key[rel_key] = {
            "source": start_name,
            "target": end_name,
            "type": rel_type,
            **{k: v for k, v in props.items() if k not in ["type", "start", "end"]}
        }


def _process_path_for_graph(value, nodes_by_name, relationships_by_key, node_id_to_name):
    """Process a Neo4j path for graph visualization."""
    # path object - extract all nodes and relationships
    path_nodes = value.get("nodes", [])
    path_relationships = value.get("relationships", [])
    
    # add all nodes from the path
    for node in path_nodes:
        # use name as primary identifier for deduplication
        node_name = node.get("name", str(node.get("id", f"path_node_{len(nodes_by_name)}")))
        node_id = str(node.get("id", node_name))
        
        # map this ID to the name
        node_id_to_name[node_id] = node_name
        
        if node_name not in nodes_by_name:
            node_data = {
                "id": node_name,  # use name as consistent ID
                "name": node_name,
                "type": "/".join(node.get("labels", ["Unknown"])),
                **{k: v for k, v in node.items() if k not in ["labels", "id", "name"]}
            }
            nodes_by_name[node_name] = node_data
    
    # add all relationships from the path with deduplication
    for rel in path_relationships:
        # map IDs to names for consistent references
        start_id = str(rel.get("start", ""))
        end_id = str(rel.get("end", ""))
        start_name = node_id_to_name.get(start_id, start_id)
        end_name = node_id_to_name.get(end_id, end_id)
        rel_type = rel.get("type", "Unknown")
        
        # create unique key for deduplication (source, target, type)
        rel_key = (start_name, end_name, rel_type)
        
        # only add if not already present
        if rel_key not in relationships_by_key:
            relationships_by_key[rel_key] = {
                "source": start_name,
                "target": end_name,
                "type": rel_type,
                **{k: v for k, v in rel.items() if k not in ["type", "start", "end"]}
            }


def _process_node_dict_for_graph(value, nodes_by_name, node_id_to_name, key):
    """Process a node dictionary for graph visualization."""
    # use name as primary identifier for deduplication
    node_name = value.get("name", str(value.get("id", key)))
    node_id = str(value.get("id", node_name))
    
    # map this ID to the name
    node_id_to_name[node_id] = node_name
    
    if node_name not in nodes_by_name:
        node_data = {
            "id": node_name,  # use name as consistent ID
            "name": node_name,
            "type": "/".join(value.get("labels", ["Unknown"])),
            **{k: v for k, v in value.items() if k not in ["labels", "id", "name"]}
        }
        nodes_by_name[node_name] = node_data


def _process_relationship_dict_for_graph(value, relationships_by_key, node_id_to_name):
    """Process a relationship dictionary for graph visualization with deduplication."""
    # map IDs to names for consistent references
    start_id = str(value.get("start", ""))
    end_id = str(value.get("end", ""))
    start_name = node_id_to_name.get(start_id, start_id)
    end_name = node_id_to_name.get(end_id, end_id)
    rel_type = value.get("type", "Unknown")
    
    # create unique key for deduplication (source, target, type)
    rel_key = (start_name, end_name, rel_type)
    
    # only add if not already present
    if rel_key not in relationships_by_key:
        relationships_by_key[rel_key] = {
            "source": start_name,
            "target": end_name,
            "type": rel_type,
            **{k: v for k, v in value.items() if k not in ["type", "start", "end"]}
        }


def _add_missing_referenced_nodes(relationships, nodes_by_name, nodes):
    """Add placeholder nodes for entities referenced in relationships but not explicitly returned."""
    if relationships:
        referenced_names = set()
        for rel in relationships:
            referenced_names.add(rel.get("source"))
            referenced_names.add(rel.get("target"))
        
        for node_name in referenced_names:
            if node_name and node_name not in nodes_by_name:
                # create placeholder node for referenced entity
                node_data = {
                    "id": node_name,
                    "name": node_name,
                    "type": "Referenced"
                }
                nodes.append(node_data)
                nodes_by_name[node_name] = node_data


def create_dataframe_from_results(results, has_neo4j_objects=False):
    """Create a pandas DataFrame from query results."""
    if has_neo4j_objects:
        # for queries with neo4j objects, create a proper table
        table_data = []
        for record in results:
            row = {}
            for key, value in record.items():
                if hasattr(value, "__class__") and "Node" in str(type(value)):
                    # neo4j node - extract key properties
                    labels = list(value.labels) if hasattr(value, "labels") else value.get("labels", [])
                    props = dict(value) if hasattr(value, "items") else value
                    
                    row[f"{key}_name"] = props.get("name", "N/A")
                    row[f"{key}_type"] = "/".join(labels)
                    row[f"{key}_id"] = value.element_id if hasattr(value, "element_id") else value.get("id", "N/A")
                    
                    # add description if available
                    if props.get("description"):
                        desc = str(props["description"])
                        if len(desc) > 100:
                            desc = desc[:100] + "..."
                        row[f"{key}_description"] = desc
                        
                elif hasattr(value, "__class__") and "Relationship" in str(type(value)):
                    # neo4j relationship - extract key properties
                    rel_type = value.type if hasattr(value, "type") else value.get("type", "Unknown")
                    props = dict(value) if hasattr(value, "items") else value
                    
                    row[f"{key}_relationship"] = rel_type
                    row[f"{key}_id"] = value.element_id if hasattr(value, "element_id") else value.get("id", "N/A")
                    
                    # add any custom properties
                    custom_props = {k: v for k, v in props.items() if k not in ["type", "start", "end"] and v is not None}
                    if custom_props:
                        prop_list = [f"{k}: {v}" for k, v in list(custom_props.items())[:3]]  # limit to 3 props
                        row[f"{key}_properties"] = ", ".join(prop_list)
                        
                elif isinstance(value, dict):
                    # dictionary object - handle nodes, relationships, and paths
                    if value.get("path_type") == "neo4j_path":
                        # path object
                        row[f"{key}_path_summary"] = value.get("path_summary", "Path")
                        row[f"{key}_path_length"] = value.get("length", 0)
                        row[f"{key}_nodes_count"] = len(value.get("nodes", []))
                        row[f"{key}_relationships_count"] = len(value.get("relationships", []))
                        
                        # add first and last node names if available
                        nodes = value.get("nodes", [])
                        if nodes:
                            row[f"{key}_start_node"] = nodes[0].get("name", "Unknown")
                            if len(nodes) > 1:
                                row[f"{key}_end_node"] = nodes[-1].get("name", "Unknown")
                    elif "labels" in value:  # node dict
                        row[f"{key}_name"] = value.get("name", "N/A")
                        row[f"{key}_type"] = "/".join(value.get("labels", []))
                        if value.get("description"):
                            desc = str(value["description"])
                            if len(desc) > 100:
                                desc = desc[:100] + "..."
                            row[f"{key}_description"] = desc
                    elif "type" in value:  # relationship dict
                        row[f"{key}_relationship"] = value.get("type", "Unknown")
                    else:
                        # other dict - convert to string
                        value_str = str(value)
                        row[key] = value_str[:100] + "..." if len(value_str) > 100 else value_str
                else:
                    # primitive value
                    row[key] = value if value is not None else ""
            
            table_data.append(row)
        
        if table_data:
            df = pd.DataFrame(table_data)
            # clean up column names
            df.columns = [col.replace("_", " ").title() for col in df.columns]
            return df
        else:
            return None
    else:
        # for regular tabular data, create dataframe
        df_data = []
        for record in results:
            clean_record = {}
            for key, value in record.items():
                if isinstance(value, (list, dict)):
                    clean_record[key] = str(value)
                else:
                    clean_record[key] = value if value is not None else ""
            df_data.append(clean_record)
        
        return pd.DataFrame(df_data)
