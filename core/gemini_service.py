import google.generativeai as genai
import typing_extensions as typing
import os
import json
from django.conf import settings

# Configure API Key
def configure_gemini():
    """Configure Gemini API with key from settings."""
    api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', ''))
    if api_key:
        genai.configure(api_key=api_key)
    return bool(api_key)

# 1. Define the exact structure you want back
class Scheme(typing.TypedDict):
    scheme_name: str
    description: str
    benefits: str
    eligibility_criteria: str
    application_link: str

# 2. Define the container (since we want a list of schemes)
class SchemeList(typing.TypedDict):
    recommendations: list[Scheme]

def fetch_schemes_smartly(farmer_profile, current_crop):
    """
    Uses Gemini's Structured Output to get guaranteed JSON.
    
    Args:
        farmer_profile: FarmerProfile instance
        current_crop: CropCycle instance
        
    Returns:
        dict: Structured response with 'recommendations' key containing list of schemes
    """
    # Check if API is configured
    if not configure_gemini():
        print("Warning: Gemini API key not configured. Skipping scheme recommendations.")
        return {"recommendations": []}
    
    try:
        # Use the Flash model for speed, or Pro for complex reasoning
        model = genai.GenerativeModel('gemini-1.5-flash') 

        # 3. Construct the context prompt
        prompt = f"""
        Act as a government agricultural officer. 
        Review this farmer's profile and the crop they just planted.
        Return a list of 3-5 relevant government schemes (Central or State) that they can apply for RIGHT NOW.
        
        FARMER DATA:
        - State: {farmer_profile.state or 'Not specified'}
        - District: {farmer_profile.district or 'Not specified'}
        - Category: {farmer_profile.get_category_display()}
        - Land Area: {farmer_profile.total_land_area} acres
        - Has KCC: {'Yes' if farmer_profile.has_kcc else 'No'}
        
        CROP DATA:
        - Crop: {current_crop.crop_name}
        - Season Date: {current_crop.start_date}
        - Area: {current_crop.area_used} acres
        
        Provide schemes with complete details including official application links.
        Focus on schemes that are currently active and accepting applications.
        """

        # 4. The Magic Part: Force the response to follow the SchemeList structure
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=SchemeList
            )
        )

        # 5. No more string replacement! It's already valid JSON.
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"JSON Parsing Error: {e}")
            print(f"Response text: {response.text}")
            return {"recommendations": []}
            
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {"recommendations": []}
