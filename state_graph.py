import logging
import json
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, List
from utils import generate_response
from prompts import PLAN_PROMPT, SECTION_GENERATE_PROMPT, CRITIQUE_PROMPT, REVISE_PROMPT
from websocket_handler import node_wrapper
from azure.cosmos import CosmosClient
import os

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize in-memory SQLite for LangGraph
memory = SqliteSaver.from_conn_string(":memory:")

# Set up Cosmos DB client
cosmosdb_endpoint = os.getenv('COSMOSDB_ENDPOINT')
cosmosdb_primary_key = os.getenv('COSMOSDB_PRIMARY_KEY')
cosmos_client = CosmosClient(cosmosdb_endpoint, credential=cosmosdb_primary_key)

# Get the database and container clients
database_name = 'dlyog'
container_name = 'dlyogcont1'
database = cosmos_client.get_database_client(database_name)
container = database.get_container_client(container_name)

import json
import re

def validate_and_clean_json(json_string):
    """
    Validates a JSON string and attempts to clean it if invalid.
    If valid, returns the JSON string; otherwise, returns the original JSON string.
    """
    def clean_json_string(json_string):
        """
        Cleans a JSON string by removing trailing commas that make the JSON invalid.
        """
        # Remove trailing commas before the closing brace
        cleaned_json = re.sub(r',\s*([\]}])', r'\1', json_string)
        return cleaned_json
    
    try:
        # Try to parse the JSON string
        json.loads(json_string)
        return json_string
    except json.JSONDecodeError:
        # If parsing fails, try to clean the JSON string and parse again
        cleaned_json_string = clean_json_string(json_string)
        try:
            json.loads(cleaned_json_string)
            return cleaned_json_string
        except json.JSONDecodeError:
            return json_string
        
class AgentState(TypedDict):
    task: str
    title: str
    category: str
    summary: str
    sections: List[dict]
    current_section_index: int
    revision_number: int
    max_revisions: int

def log_state_output(state, response, node_name):
    logger.info(f"State output from {node_name}: {response}")

def plan_node(state: AgentState):
    logger.info(f"Planning for task: {state['task']}")
    response = generate_response(PLAN_PROMPT, state['task'])
    logger.info(f"Plan generated: {response}")
    log_state_output(state, response, "plan_node")
    response = validate_and_clean_json(response)
    plan = json.loads(response)
    return {
        "task": state['task'],
        "title": plan['title'],
        "category": plan['category'],
        "summary": plan['summary'],
        "sections": plan['sections'],
        "current_section_index": 0,
        "revision_number": 0,
        "max_revisions": state['max_revisions']
    }

def section_generation_node(state: AgentState):
    current_index = state['current_section_index']
    section = state['sections'][current_index]
    logger.info(f"Generating content for section: {section['section_name']}")
    response = generate_response(
        SECTION_GENERATE_PROMPT.format(
            title=state['title'],
            section_name=section['section_name'],
            content=section['content']
        ), 
        state['task']
    )
    log_state_output(state, response, "section_generation_node")
    new_sections = state['sections'].copy()
    new_sections[current_index]['content'] = response
    logger.info(f"Content generated for section: {section['section_name']}")
    return {
        "task": state['task'],
        "title": state['title'],
        "category": state['category'],
        "summary": state['summary'],
        "sections": new_sections,
        "current_section_index": state['current_section_index'],
        "revision_number": state['revision_number'],
        "max_revisions": state['max_revisions']
    }

def critique_node(state: AgentState):
    current_index = state['current_section_index']
    section = state['sections'][current_index]
    logger.info(f"Critiquing content for section: {section['section_name']}")
    critique = generate_response(
        CRITIQUE_PROMPT.format(
            title=state['title'],
            section_name=section['section_name'],
            content=section['content']
        ), 
        state['task']
    )
    log_state_output(state, critique, "critique_node")
    new_sections = state['sections'].copy()
    new_sections[current_index]['critique'] = critique
    logger.info(f"Critique generated for section: {section['section_name']}")
    return {
        "task": state['task'],
        "title": state['title'],
        "category": state['category'],
        "summary": state['summary'],
       
        "sections": new_sections,
        "current_section_index": state['current_section_index'],
        "revision_number": state['revision_number'],
        "max_revisions": state['max_revisions']
    }

def revision_node(state: AgentState):
    current_index = state['current_section_index']
    section = state['sections'][current_index]
    #logger.info(f"Revising content for section: {section['section_name']}")
    revised_content = generate_response(
        REVISE_PROMPT.format(
            title=state['title'],
            section_name=section['section_name'],
            initial_content=section['content'],
            critique=section['critique']
        ), 
        state['task']
    )
    log_state_output(state, revised_content, "revision_node")
    new_sections = state['sections'].copy()
    new_sections[current_index]['content'] = revised_content
    #logger.info(f"Content revised for section: {section['section_name']}")
    return {
        "task": state['task'],
        "title": state['title'],
        "category": state['category'],
        "summary": state['summary'],
       
        "sections": new_sections,
        "current_section_index": state['current_section_index'],
        "revision_number": state['revision_number'],
        "max_revisions": state['max_revisions']
    }

import uuid

def aggregate_node(state: AgentState):
    #logger.info("Aggregating final paper content.")
    final_paper = {
        "id": str(uuid.uuid4()),  # Add a unique ID to each document
        "paper": state['title'],  # Ensure partition key field is included
        "status": "Draft",
        "title": state['title'],
        "category": state['category'],
        "summary": state['summary'],
       
        "sections": [
            {"section_name": section['section_name'], "content": section['content']}
            for section in state['sections']
        ]
    }

    #logger.info(f"Final paper aggregated: {final_paper}")
    return final_paper

def validate_document_structure(document):
    required_fields = ["paper", "title", "sections"]
    for field in required_fields:
        if field not in document:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(document["sections"], list):
        raise ValueError("Field 'sections' must be a list")

    for section in document["sections"]:
        if "section_name" not in section or "content" not in section:
            raise ValueError("Each section must have 'section_name' and 'content' fields")

    return True
def save_to_cosmos_node(state):
    final_paper = aggregate_node(state)  # Ensure the paper is properly aggregated
    validate_document_structure(final_paper)  # Validate document structure

    try:
        #logger.info(f"Attempting to save final paper to Cosmos DB: {final_paper}")
        container.upsert_item(final_paper, partition_key=final_paper['paper'])
        #logger.info(f"Final paper saved to Cosmos DB: {final_paper}")
    except Exception as e:
        logger.error(f"Error saving final paper to Cosmos DB: {e}")
        raise e
    return final_paper

def should_continue(state: AgentState):
    state["revision_number"] += 1
    #logger.info(f"Revision number: {state['revision_number']}")
    if state["revision_number"] >= state["max_revisions"]:
        return "next_section"
    return "critique"

def next_section(state: AgentState):
    current_index = state["current_section_index"] + 1
    
    return {
        "task": state['task'],
        "title": state['title'],
       
        "sections": state['sections'],
        "current_section_index": current_index,
        "revision_number": 0,  # Reset revision number for the next section
        "max_revisions": state['max_revisions']
    }

def ready_for_aggregate(state: AgentState):
    if state["current_section_index"] >= len(state["sections"]):
        return "aggregate"
    
    return "generate_section"

builder = StateGraph(AgentState)

builder.add_node("planner", lambda state: node_wrapper(plan_node, "planner", state))
builder.add_node("generate_section", lambda state: node_wrapper(section_generation_node, "generate_section", state))
builder.add_node("critique", lambda state: node_wrapper(critique_node, "critique", state))
builder.add_node("revise", lambda state: node_wrapper(revision_node, "revise", state))
builder.add_node("next_section", lambda state: node_wrapper(next_section, "next_section", state))
builder.add_node("aggregate", lambda state: node_wrapper(aggregate_node, "aggregate", state))
builder.add_node("save_to_cosmos", lambda state: node_wrapper(save_to_cosmos_node, "save_to_cosmos", state))

builder.set_entry_point("planner")

builder.add_edge("planner", "generate_section")
builder.add_edge("generate_section", "critique")
builder.add_edge("critique", "revise")
builder.add_conditional_edges(
    "revise", 
    should_continue, 
    {"next_section": "next_section", "critique": "critique"}
)
builder.add_conditional_edges(
    "next_section", 
    ready_for_aggregate,
    {"aggregate": "aggregate", "generate_section": "generate_section"}
)
builder.add_edge("aggregate", "save_to_cosmos")
builder.add_edge("save_to_cosmos", END)

graph = builder.compile(checkpointer=memory)
