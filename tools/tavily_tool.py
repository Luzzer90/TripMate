from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
    )

def tavily_search(query,limit=5):
    """
    Search for a query using the Tavily API.

    Args:
        query (str): The search query.
        limit (int): The maximum number of results to return.

    Returns:
        dict: The search results.
    """
    result = []
    response = tavily_client.search(query, max_results=limit)
    # Process the search results
    for i,r in enumerate(response['results'],1):
        title = r.get('title')
        url = r.get('url')
        snippet = r.get('content')
        # Truncate the snippet if it exceeds 300 characters
        if len(snippet) > 300:
            snippet = snippet[:300].rstrip(" ")[0] + "..."
        # Append the formatted result to the list

        result.append(f"{i}. {title}\n{url}\n{snippet}\n")

    return "\n\n".join(result)