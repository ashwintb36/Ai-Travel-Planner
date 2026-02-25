import google.generativeai as genai
import json
from pydantic import BaseModel, Field
from typing import List

# Define the expected structured output from Gemini using Pydantic
class Activity(BaseModel):
    name: str = Field(description="Name of the activity, place, or restaurant")
    time: str = Field(description="Suggested time, e.g., 'Morning 09:00 AM'")
    description: str = Field(description="Short description appealing to a student")
    cost_estimate: str = Field(description="Estimated cost in INR ₹ (or 'Free')")
    latitude: float = Field(description="Latitude coordinate of the location")
    longitude: float = Field(description="Longitude coordinate of the location")

class DailyPlan(BaseModel):
    day: int = Field(description="Day number")
    theme: str = Field(description="Theme for the day, e.g., 'Historical Highlights'")
    activities: List[Activity] = Field(description="List of activities for the day")

class TripItinerary(BaseModel):
    destination: str = Field(description="The destination city/country")
    total_estimated_cost: str = Field(description="Rough total estimated cost for the trip in INR ₹")
    budget_tips: List[str] = Field(description="List of 3-5 specific budget tips for this destination")
    itinerary: List[DailyPlan] = Field(description="Day by day plan")

def generate_itinerary(api_key: str, destination: str, days: int, budget: str, interests: List[str], notes: str) -> dict:
    """
    Calls the Gemini API to generate a structured student trip itinerary.
    Returns a dictionary parsed from the JSON response.
    """
    genai.configure(api_key=api_key)
    
    # We use a standard fast model that supports structured outputs well
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    interests_str = ", ".join(interests) if interests else "General sightseeing"
    notes_str = f"\nAdditional Notes: {notes}" if notes else ""
    
    prompt = f"""
    You are an expert travel planner specializing in budget travel for college students.
    Create a detailed {days}-day itinerary for {destination}.
    
    Constraints & Preferences:
    - Budget Level: {budget}. Prioritize free activities, student discounts, street food, and cheap transport.
    - Interests: {interests_str}.{notes_str}
    
    For every activity, you must provide realistic latitude and longitude coordinates. 
    Ensure locations for a single day are geographically close to minimize transit time and costs.
    """
    
    from google.api_core.exceptions import InvalidArgument
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=TripItinerary,
                temperature=0.7,
            )
        )
        
        # The response is guaranteed to be a JSON string matching the Pydantic schema
        result_dict = json.loads(response.text)
        return {"status": "success", "data": result_dict}
        
    except InvalidArgument as e:
        return {"status": "error", "message": "Invalid API Key provided. Please check your Gemini API key."}
    except Exception as e:
        print(f"Failed to parse Gemini response: {e}")
        return {"status": "error", "message": str(e)}
