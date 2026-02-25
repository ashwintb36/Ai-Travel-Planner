import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from dotenv import load_dotenv
import ai_planner

# Load environment variables, overriding any existing ones to ensure .env updates take effect
load_dotenv(override=True)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Student Travel Planner AI",
    page_icon="🎒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4ECDC4;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45b7af;
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("🗺️ Plan Your Trip")
    
    # Get API key from environment variable
    api_key = os.getenv("GEMINI_API_KEY")
        
    st.divider()
    
    # Trip Inputs
    destination = st.text_input("Destination (City/Country)", placeholder="e.g., Paris, France")
    
    col1, col2 = st.columns(2)
    with col1:
        duration_days = st.number_input("Days", min_value=1, max_value=14, value=3)
    with col2:
        budget_level = st.selectbox("Budget", ["Ultra-budget", "Budget", "Moderate"])
        
    interests = st.multiselect(
        "Interests",
        ["History", "Art & Museums", "Food", "Nature", "Nightlife", "Shopping", "Adventure"],
        default=["History", "Food"]
    )
    
    additional_notes = st.text_area("Additional Notes (Optional)", placeholder="e.g., Vegetarian food only, no early mornings")
    
    st.divider()
    
    generate_btn = st.button("🚀 Generate Itinerary", use_container_width=True)

# --- STATE INITIALIZATION ---
if "itinerary_data" not in st.session_state:
    st.session_state.itinerary_data = None
if "error_message" not in st.session_state:
    st.session_state.error_message = None

if generate_btn:
    # Reset state on new generation
    st.session_state.itinerary_data = None
    st.session_state.error_message = None
    
    if not api_key or api_key == "your_api_key_here":
        st.error("Please provide a Gemini API Key in the sidebar or `.env` file to proceed.")
    elif not destination:
        st.warning("Please enter a destination.")
    else:
        with st.spinner("✨ Gemini is planning your perfect trip..."):
            result = ai_planner.generate_itinerary(
                api_key=api_key,
                destination=destination,
                days=duration_days,
                budget=budget_level,
                interests=interests,
                notes=additional_notes
            )
            
        if result and result.get("status") == "success":
            st.session_state.itinerary_data = result["data"]
            st.session_state.error_message = None
        else:
            st.session_state.itinerary_data = None
            st.session_state.error_message = result.get("message", "An unknown error occurred.") if result else "Failed to get a response from the AI planner."

# --- MAIN UI ---
st.markdown('<h1 class="main-title">AI Travel Planner for Students</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Personalized, budget-friendly itineraries powered by Gemini</p>', unsafe_allow_html=True)

# Render content based on session state
if st.session_state.error_message:
    st.error(f"Failed to generate itinerary: {st.session_state.error_message}")
elif st.session_state.itinerary_data:
    itinerary_data = st.session_state.itinerary_data
    # Display Trip Overview
    st.success(f"Trip to {itinerary_data['destination']} planned successfully!")
    st.markdown(f"**Estimated Total Cost:** {itinerary_data['total_estimated_cost']}")
    
    with st.expander("💡 Budget Tips for Students", expanded=True):
        for tip in itinerary_data['budget_tips']:
            st.markdown(f"- {tip}")
    
    st.divider()
    
    # Map Implementation
    st.subheader("📍 Your Trip Highlights")
            
    # Gather all coordinates to calculate map bounds
    all_coords = []
    for day in itinerary_data['itinerary']:
        for act in day['activities']:
            all_coords.append([act['latitude'], act['longitude']])
    
    if all_coords:
        # Center map on the first activity
        m = folium.Map(location=all_coords[0], zoom_start=12)
        
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
        
        # Add markers for each activity
        for day in itinerary_data['itinerary']:
            day_color = colors[(day['day'] - 1) % len(colors)]
            for act in day['activities']:
                folium.Marker(
                    [act['latitude'], act['longitude']],
                    popup=f"<b>{act['name']}</b><br>Day {day['day']}: {act['time']}<br>Cost: {act['cost_estimate']}",
                    tooltip=f"Day {day['day']}: {act['name']}",
                    icon=folium.Icon(color=day_color, icon='info-sign')
                ).add_to(m)
        
        # Fit bounds to show all markers
        m.fit_bounds(all_coords)
        st_folium(m, width=900, height=500)
    else:
        st.info("No coordinates returned to display on the map.")
        
    st.divider()
            
    # Itinerary Implementation
    st.subheader("📅 Your Itinerary")
    for day in itinerary_data['itinerary']:
        with st.container():
            st.markdown(f"### Day {day['day']}: {day['theme']}")
            for act in day['activities']:
                st.markdown(f"**{act['time']}** - {act['name']} ({act['cost_estimate']})")
                st.markdown(f"*{act['description']}*")
            st.markdown("---")
            
else:
    # Empty State
    st.info("👈 Fill out the details in the sidebar and click 'Generate Itinerary' to start planning your adventure!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🎒 Student Focused")
        st.write("Find free museums, student discounts, and cheap eats.")
    with col2:
        st.markdown("### 💰 Budget Friendly")
        st.write("Strictly budget considerations: hostels, public transport.")
    with col3:
        st.markdown("### 🗺️ Interactive Maps")
        st.write("See your daily routes and stops on a beautifully rendered map.")
