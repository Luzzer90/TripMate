import json

from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
"""tavily search is a function that takes a query and an optional limit parameter, 
and returns the search results from the Tavily API. 
The results are formatted as a string with each result on a new line, 
including the title, URL, and a snippet of content. 
The snippet is truncated to 300 characters if it exceeds that length.
limit is set to 3 in this case, so it will return a maximum of 3 results for the query""" 

# results = tavily_search("best restaurants", limit=3)
results = search_flights("Flights from JFK to LHR", limit=10)
print(json.dumps(results, indent=2, ensure_ascii=False)) 