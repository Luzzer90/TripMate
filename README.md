# TripMate
Multi Agent workflow for trip management
which has flight search agents,hotel research agent, itineary agent,final response agentss

flight agent:
we are using aviationstack api for real time flight status
hotel agent:
tavily search or we can use google api 
itineary agent:
tavily search also google map api
final response:
groq llm(lama3) with tavily search

# create virtual env
conda create -n travel python=3.13.2 -y

# activate the env
conda activate travel

# deactivate
conda deactivate
