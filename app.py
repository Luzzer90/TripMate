from pathlib import Path
import traceback
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from backend import run_travel_agent

app = FastAPI(
    title="AI Travel Planner",
    description="Create a personalized travel plan.",
    version="1.0.0",
)


class PlanRequest(BaseModel):
    user_input: str 
    thread_id: str | None = None




@app.post("/api/plan")
async def create_plan(request: PlanRequest) -> dict:
    user_input = request.user_input.strip()
    if not user_input:
        raise HTTPException(status_code=422, detail="Please enter a travel request.")

    result = run_travel_agent(user_input, request.thread_id)

    return JSONResponse(
        content={
                "success": True,
                "thread_id": result["thread_id"],
                "answer": result["answer"],
                "flight_results": result["flight_results"],
                "hotel_results": result["hotel_results"],
                "itinerary": result["itinerary"],
                "llm_calls": result["llm_calls"],
            }
    )
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "AI Travel Planner API is running"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )