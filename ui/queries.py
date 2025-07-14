"""
Quick action Cypher queries for the Dark Souls Knowledge Graph Explorer.

This module contains predefined queries used by the sidebar quick action buttons
to provide common graph exploration functionality.
"""





def get_quick_action_queries():
    """Return quick action queries for the sidebar."""
    return {
        "sample_network": {
            "query": (
                "MATCH (n)\n"
                "WITH n, COUNT { (n)--() } AS connections\n"
                "WHERE connections > 0\n"
                "ORDER BY connections DESC\n"
                "LIMIT 50\n"
                "MATCH (n)-[r]-(connected)\n"
                "RETURN n, r, connected"
            ),
            "show_network_message": True,
            "button_text": "Sample Network View"
        },
        "four_knights": {
            "query": (
                "MATCH (knight)-[:MEMBER_OF|LEADER_OF]->({name: \"Four Knights\"})\n"
                "MATCH p = (knight)-[r]-(connected)\n"
                "RETURN p"
            ),
            "show_network_message": True,
            "button_text": "Four Knights Members"
        },
        "manus_location": {
            "query": (
                "MATCH (manus {name: \"Manus\"})-[:ALSO_KNOWN_AS*]-(alias)-[:LOCATED_IN*]->(location)\n"
                "RETURN DISTINCT location.name AS LocationName\n"
            ),
            "show_network_message": False,
            "button_text": "Where is Manus?"
        },
        "sealers_enemies": {
            "query": (
                "MATCH (sealers)-[:ENEMY_OF]->(enemy)\n"
                "WHERE toLower(sealers.name) CONTAINS \"sealers\"\n"
                "RETURN enemy"
            ),
            "show_network_message": False,
            "button_text": "Sealers' Enemies"
        },
        "gwyn_aliases": {
            "query": (
                "MATCH ({name: \"Gwyn\"})-[:ALSO_KNOWN_AS]->(alias)\n"
                "RETURN alias"
            ),
            "show_network_message": False,
            "button_text": "Gwyn's Aliases"
        }
    }
