import os
from dotenv import load_dotenv
import certifi

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from typing import TypedDict, Annotated
# used for state of the graph
import operator
# used so that output comes as list not replacing the first input
import uuid
# used for unique id generation

import psycopg
# used for connecting to postgres database
from psycopg.rows import dict_row

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from tools.flight_tool import search_flights
from tools.tavily_tool import tavily_search

def get_postgres_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    
    if "sslmode" not in database_url:
        database_url += "?sslmode=require"

    return database_url

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(api_key=GROQ_API_KEY, model="openai/gpt-oss-120b", temperature=0.7)
#  Initialize the ChatGroq model with the API key and model name

# graph state management

class TravelState(TypedDict):
    messages : Annotated[list[AnyMessage],add_messages] # used for storing messages in the state graph
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    final_plan: str
    llm_call: int


# flight agent

def flight_agent(state: TravelState) -> TravelState:
    """
    Flight agent that searches for flights based on the user's query.

    Args:
        state (TravelState): The current state of the travel planning process.
"""
    # Extract the user's query from the state
    user_query = state.get("user_query", "")
    
    # Search for flights using the flight_tool
    flight_results = search_flights(user_query)
    
    
    return {
        "flight_results": flight_results,
        "messages": [AIMessage(content=f"Flight search results fetched:\n{flight_results}")],
        # "llm_call": state.get("llm_call", 0) + 1
    }

def hotel_agent(state: TravelState) -> TravelState:
    """
    Hotel agent that searches for hotels based on the user's query.

    Args:
        state (TravelState): The current state of the travel planning process.
    """
    # Extract the user's query from the state
    user_query = state.get("user_query", "")
    
    # Search for hotels using the tavily_tool
    hotel_results = tavily_search(user_query)
    
    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content=f"Hotel search results fetched:\n{hotel_results}")],
        # "llm_call": state.get("llm_call", 0) + 1
    }

def itinerary_agent(state: TravelState) -> TravelState:
    """
    Itinerary agent that generates an itinerary based on the user's query.

    Args:
        state (TravelState): The current state of the travel planning process.
    """
    # Extract the user's query from the state
    user_query = state.get("user_query", "")
    
    prompt = f"""Generate a travel itinerary based on the following 
    user query: {user_query}
    flight results: {state.get("flight_results", "")}
    hotel results: {state.get("hotel_results", "")}
    make the itinerary practical and budget-aware
    """
    response = llm.invoke([SystemMessage(content="You are a travel planning assistant."), HumanMessage(content=prompt)])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_call": state.get("llm_call", 0) + 1
    }

def final_agent(state: TravelState) -> TravelState:
    """
    Final agent that compiles the final travel plan based on the user's query.
    Args:
        state (TravelState): The current state of the travel planning process.
    """
            
    prompt = f"""Compile a final travel plan based on the following 
    user query: {state.get("user_query", "")}
    flight results: {state.get("flight_results", "")}
    hotel results: {state.get("hotel_results", "")}
    itinerary: {state.get("itinerary", "")}
    format the final plan in a clear and concise manner, highlighting key details and recommendations.
    1. trip summary
    2. flight details
    3. hotel details
    4. day-by-day itinerary
    5. recommendations
    6. budget breakdown
    Important: Ensure that the final plan is well-structured and easy to read, with appropriate headings and bullet points where necessary.
    """
    response = llm.invoke([SystemMessage(content="You are a travel planning assistant."), HumanMessage(content=prompt)])
    return {
        "messages": [response],
        "llm_call": state.get("llm_call", 0) + 1
    }

# build the state graph

graph = StateGraph(TravelState)
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge(START, "hotel_agent")
graph.add_edge(["flight_agent","hotel_agent"],"itinerary_agent")
# graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")    
graph.add_edge("final_agent", END)

# postgres saver for state graph
database_url = get_postgres_connection()
_conn = psycopg.connect(database_url,autocommit=True, row_factory=dict_row)

checkpoint = PostgresSaver(_conn)
checkpoint.setup()

travel_graph = graph.compile(checkpointer=checkpoint)



# function for fastapi 

def run_travel_agent(user_input:str, tread_id:str|None=None) -> dict:
    """
    Run the travel agent with the given user input.

    Args:
        user_input (str): The user's query for travel planning.
        tread_id (str | None): Optional thread ID for tracking the state graph.

    Returns:
        dict: The final travel plan and related information.
    """
    if tread_id is None:
        tread_id = f"user_{uuid.uuid4().hex}"
    config={
        "configurable":{
            "thread_id":tread_id
        }
    }
    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": [],
            "hotel_results": "",
            "itinerary": "",
            "final_plan": "",
            "llm_call": 0
        },
        config=config
    )
    final_answer = result["messages"][-1].content 
    
    return {
        "thread_id": tread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_call_count": result.get("llm_call", 0),
    }