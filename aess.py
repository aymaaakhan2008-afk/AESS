# aess_app.py
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# ----------------------------
# PAGE CONFIGURATION & GALAXY THEME
# ----------------------------
st.set_page_config(
    page_title="AESS - Artificial Intelligence Exoplanet Survey Satellite",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for galaxy theme
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(to right, #0c0f2fff, #1a1b4fff, #2c1a4fff);
        color: #ffffff;
    }
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(to bottom, #0c0f2fff, #1a1b4fff) !important;
    }
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #ffffff !important;
    }
    [data-testid="stMetric"] {
        background-color: rgba(26, 27, 79, 0.7);
        border: 1px solid #4e54c8;
        padding: 10px;
        border-radius: 10px;
    }
    .stDataFrame {
        background-color: rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# NASA API DATA FETCHING FUNCTIONS
# ----------------------------
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_nasa_exoplanet_data():
    """
    Fetches comprehensive exoplanet data from NASA Exoplanet Archive TAP service.
    Uses the Planetary Systems (PS) Table for all confirmed planets.
    """
    try:
        # Using a simpler query that's more reliable
        url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
        query = """
        SELECT 
            pl_name, hostname, sy_snum, sy_pnum, discoverymethod, disc_year,
            pl_orbper, pl_rade, pl_bmasse, pl_orbsmax, pl_orbeccen, pl_insol,
            st_spectype, st_teff, st_rad, st_mass, st_met, st_metratio, st_lum,
            sy_dist, sy_vmag, ra, dec, glat, glon
        FROM ps 
        WHERE default_flag = 1
        ORDER BY disc_year DESC
        LIMIT 1000
        """
        
        params = {
            'request': "doQuery",
            'lang': "ADQL",
            'format': "csv",  # Using CSV format for better compatibility
            'query': query
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # Read the CSV data
        df = pd.read_csv(pd.compat.StringIO(response.text))
        
        # Create readable column names
        column_mapping = {
            'pl_name': 'Planet Name', 'hostname': 'Host Star', 'discoverymethod': 'Discovery Method',
            'disc_year': 'Discovery Year', 'pl_orbper': 'Orbital Period (days)', 
            'pl_rade': 'Planet Radius (Earth radii)', 'pl_bmasse': 'Planet Mass (Earth mass)',
            'pl_orbsmax': 'Orbit Semi-Major Axis (AU)', 'pl_orbeccen': 'Orbital Eccentricity',
            'sy_dist': 'Distance from Earth (pc)', 'st_teff': 'Star Temperature (K)',
            'st_rad': 'Star Radius (Solar radii)', 'st_mass': 'Star Mass (Solar mass)',
            'st_lum': 'Star Luminosity (log Solar)', 'ra': 'Right Ascension', 'dec': 'Declination'
        }
        
        # Only rename columns that exist in the dataframe
        existing_columns = [col for col in column_mapping.keys() if col in df.columns]
        df.rename(columns={k: v for k, v in column_mapping.items() if k in existing_columns}, inplace=True)
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching data from NASA API: {str(e)}")
        # Return a sample dataframe if API fails
        return pd.DataFrame({
            'Planet Name': ['Kepler-186f', 'TRAPPIST-1e', 'Proxima Centauri b'],
            'Host Star': ['Kepler-186', 'TRAPPIST-1', 'Proxima Centauri'],
            'Discovery Method': ['Transit', 'Transit', 'Radial Velocity'],
            'Discovery Year': [2014, 2017, 2016],
            'Planet Radius (Earth radii)': [1.17, 0.92, 1.30],
            'Planet Mass (Earth mass)': [1.44, 0.69, 1.27],
            'Orbital Period (days)': [129.9, 6.10, 11.18]
        })

@st.cache_data(ttl=86400)  # Cache for 24 hours
def fetch_nasa_apod():
    """
    Fetches NASA's Astronomy Picture of the Day.
    """
    try:
        url = "https://api.nasa.gov/planetary/apod"
        params = {'api_key': 'DEMO_KEY', 'thumbs': True}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None
# ----------------------------
# SIDEBAR NAVIGATION
# ----------------------------
st.sidebar.markdown("""
<div style="text-align: center;">
    <h2>🪐 AESS Navigation</h2>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("Explore the Cosmos:", [
    "🏠 Dashboard & Mission Control",
    "📊 Exoplanet Encyclopedia", 
    "🔭 Advanced Visualizations",
    "🌌 System Simulations",
    "🛰 Live NASA Feeds",
    "📡 Mission Overview"
])

# ----------------------------
# LOAD DATA
# ----------------------------
with st.spinner('🛰 Connecting to NASA Exoplanet Archive...'):
    exoplanet_df = fetch_nasa_exoplanet_data()
apod_data = fetch_nasa_apod()

# ----------------------------
# PAGE 1: DASHBOARD & MISSION CONTROL
# ----------------------------
if page == "🏠 Dashboard & Mission Control":
    st.title("🌌 Artificial Intelligence Exoplanet Survey Satellite")
    st.markdown("---")
    
    # Mission Overview
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header("🚀 Mission Overview")
        st.markdown("""
        The Artificial Intelligence Exoplanet Survey Satellite (AESS) represents a breakthrough in public access to exoplanetary science. 
        Our platform transforms complex NASA data into interactive, educational experiences by leveraging:
        
        - Real-time NASA API Integration: Direct access to the NASA Exoplanet Archive TAP service
        - Advanced AI Processing: Making complex orbital mechanics understandable
        - Interactive Visualizations: Professional-grade charts and simulations
        - Live Satellite Data: Current observations and discoveries
        """)
    
    with col2:
        if apod_data and apod_data.get('media_type') == 'image':
            st.image(apod_data['url'], caption=f"NASA Astronomy Picture of the Day: {apod_data['title']}", 
                    use_column_width=True)
    
    st.markdown("---")
    
    # Real-time Statistics Dashboard
    st.header("📈 Live Exoplanet Statistics")
    if not exoplanet_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        total_planets = len(exoplanet_df)
        unique_stars = exoplanet_df['Host Star'].nunique() if 'Host Star' in exoplanet_df.columns else 0
        discovery_methods = exoplanet_df['Discovery Method'].nunique() if 'Discovery Method' in exoplanet_df.columns else 0
        recent_discoveries = len(exoplanet_df[exoplanet_df['Discovery Year'] >= 2020]) if 'Discovery Year' in exoplanet_df.columns else 0
        
        col1.metric("🌍 Confirmed Exoplanets", f"{total_planets:,}")
        col2.metric("⭐ Host Stars", f"{unique_stars:,}")
        col3.metric("🔬 Detection Methods", discovery_methods)
        col4.metric("🆕 Recent Discoveries (2020+)", recent_discoveries)
    
    # Quick Discovery Analysis
    st.header("🔍 Recent Discoveries Analysis")
    if not exoplanet_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Discovery Method' in exoplanet_df.columns:
                method_counts = exoplanet_df['Discovery Method'].value_counts().head(5)
                fig = px.pie(values=method_counts.values, names=method_counts.index,
                           title="Top 5 Discovery Methods")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'Discovery Year' in exoplanet_df.columns:
                yearly = exoplanet_df['Discovery Year'].value_counts().sort_index()
                fig = px.area(x=yearly.index, y=yearly.values,
                            title="Exoplanet Discoveries Timeline",
                            labels={'x': 'Year', 'y': 'Planets Discovered'})
                st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# PAGE 2: EXOPLANET ENCYCLOPEDIA
# ----------------------------
elif page == "📊 Exoplanet Encyclopedia":
    st.title("📊 Exoplanet Encyclopedia")
    st.markdown("Comprehensive database of all confirmed exoplanets from NASA archives")
    
    if not exoplanet_df.empty:
        # Interactive Filters
        col1, col2, col3 = st.columns(3)
        
        methods = []
        if 'Discovery Method' in exoplanet_df.columns:
            with col1:
                methods = st.multiselect("Filter by Discovery Method:", 
                                       options=exoplanet_df['Discovery Method'].unique())
        
        with col2:
            search_planet = st.text_input("🔍 Search Planet Name:")
        
        year_range = (1990, 2024)
        if 'Discovery Year' in exoplanet_df.columns:
            with col3:
                min_year = int(exoplanet_df['Discovery Year'].min())
                max_year = int(exoplanet_df['Discovery Year'].max())
                year_range = st.slider("Discovery Year Range:", 
                                     min_year, max_year,
                                     (min_year, max_year))
        
        # Apply filters
        filtered_df = exoplanet_df.copy()
        if methods and 'Discovery Method' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Discovery Method'].isin(methods)]
        if search_planet and 'Planet Name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Planet Name'].str.contains(search_planet, case=False, na=False)]
        if 'Discovery Year' in filtered_df.columns:
            filtered_df = filtered_df[(filtered_df['Discovery Year'] >= year_range[0]) & 
                                    (filtered_df['Discovery Year'] <= year_range[1])]
        
        # Display data
        st.dataframe(filtered_df, use_container_width=True, height=400)
        
        # Individual Planet Details
        st.header("🔬 Detailed Planet Analysis")
        if len(filtered_df) > 0 and 'Planet Name' in filtered_df.columns:
            selected_planet = st.selectbox("Select a planet for detailed analysis:", 
                                         filtered_df['Planet Name'].head(100))
            
            if selected_planet:
                planet_data = filtered_df[filtered_df['Planet Name'] == selected_planet].iloc[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Host Star", planet_data.get('Host Star', 'N/A'))
                    st.metric("Discovery Method", planet_data.get('Discovery Method', 'N/A'))
                    st.metric("Discovery Year", planet_data.get('Discovery Year', 'N/A'))
                
                with col2:
                    st.metric("Planet Radius (Earth radii)", planet_data.get('Planet Radius (Earth radii)', 'N/A'))
                    st.metric("Planet Mass (Earth mass)", planet_data.get('Planet Mass (Earth mass)', 'N/A'))
                    st.metric("Orbital Period (days)", planet_data.get('Orbital Period (days)', 'N/A'))
                
                with col3:
                    st.metric("Distance from Earth (pc)", planet_data.get('Distance from Earth (pc)', 'N/A'))
                    st.metric("Star Temperature (K)", planet_data.get('Star Temperature (K)', 'N/A'))
                    st.metric("Star Mass (Solar mass)", planet_data.get('Star Mass (Solar mass)', 'N/A'))

# ----------------------------
# PAGE 3: ADVANCED VISUALIZATIONS
# ----------------------------
elif page == "🔭 Advanced Visualizations":
    st.title("🔭 Advanced Data Visualizations")
    st.markdown("Interactive scientific visualizations of exoplanetary data")
    
    if not exoplanet_df.empty:
        viz_type = st.selectbox("Choose Visualization Type:", [
            "Planet Radius vs Orbital Period",
            "Star Temperature vs Planet Count", 
            "Discovery Methods Distribution",
            "Distance from Earth Analysis",
            "Mass-Radius Relationship"
        ])
        
        if viz_type == "Planet Radius vs Orbital Period" and 'Orbital Period (days)' in exoplanet_df.columns and 'Planet Radius (Earth radii)' in exoplanet_df.columns:
            fig = px.scatter(exoplanet_df, x='Orbital Period (days)', y='Planet Radius (Earth radii)',
                           hover_data=['Planet Name', 'Discovery Method'] if 'Discovery Method' in exoplanet_df.columns else ['Planet Name'],
                           title="Planet Radius vs Orbital Period",
                           color='Discovery Method' if 'Discovery Method' in exoplanet_df.columns else None)
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Mass-Radius Relationship" and 'Planet Mass (Earth mass)' in exoplanet_df.columns and 'Planet Radius (Earth radii)' in exoplanet_df.columns:
            fig = px.scatter(exoplanet_df, x='Planet Mass (Earth mass)', y='Planet Radius (Earth radii)',
                           hover_data=['Planet Name', 'Discovery Method'] if 'Discovery Method' in exoplanet_df.columns else ['Planet Name'],
                           title="Planet Mass vs Radius Relationship",
                           color='Discovery Method' if 'Discovery Method' in exoplanet_df.columns else None,
                           log_x=True, log_y=True)
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Discovery Methods Distribution" and 'Discovery Method' in exoplanet_df.columns:
            method_data = exoplanet_df['Discovery Method'].value_counts()
            fig = px.bar(x=method_data.index, y=method_data.values,
                       title="Exoplanet Discovery Methods Distribution",
                       labels={'x': 'Discovery Method', 'y': 'Number of Planets'})
            st.plotly_chart(fig, use_container_width=True)
# ----------------------------
# PAGE 4: SYSTEM SIMULATIONS
# ----------------------------
elif page == "🌌 System Simulations":
    st.title("🌌 Exoplanet System Simulations")
    st.markdown("Interactive simulations of exoplanet transits and orbital mechanics")
    
    sim_type = st.selectbox("Choose Simulation Type:", [
        "Transit Light Curve Simulator",
        "Habitable Zone Calculator",
        "Orbital Resonance Model"
    ])
    
    if sim_type == "Transit Light Curve Simulator":
        st.header("Transit Light Curve Simulation")
        
        col1, col2 = st.columns(2)
        with col1:
            planet_radius = st.slider("Planet Radius (Earth radii)", 0.1, 20.0, 1.0)
            orbital_period = st.slider("Orbital Period (days)", 0.5, 365.0, 10.0)
            impact_param = st.slider("Impact Parameter", 0.0, 1.0, 0.3)
        
        with col2:
            star_radius = st.slider("Star Radius (Solar radii)", 0.1, 10.0, 1.0)
            inclination = st.slider("Orbital Inclination (degrees)", 85.0, 90.0, 89.5)
        
        # Generate realistic light curve
        time = np.linspace(0, orbital_period, 1000)
        transit_depth = (planet_radius/star_radius)**2
        transit_center = orbital_period / 2
        transit_duration = orbital_period * star_radius / (np.pi * planet_radius)
        
        flux = 1 - transit_depth * np.exp(-(time-transit_center)*2/(transit_duration/4)*2)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time, y=flux, mode='lines', name='Relative Flux',
                               line=dict(color='#4e54c8')))
        fig.update_layout(title="Simulated Transit Light Curve",
                         xaxis_title="Time (days)",
                         yaxis_title="Relative Flux",
                         template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        About Transit Photometry: 
        This simulation shows how a planet passing in front of its host star causes a detectable dip in brightness. 
        NASA's Kepler and TESS missions use this method to discover thousands of exoplanets.
        """)

# ----------------------------
# PAGE 5: LIVE NASA FEEDS
# ----------------------------
elif page == "🛰 Live NASA Feeds":
    st.title("🛰 Live NASA Data Feeds")
    st.markdown("Real-time data from NASA's active missions and observatories")
    
    tab1, tab2, tab3 = st.tabs(["🌠 Astronomy Picture of the Day", "🪐 Mission Updates", "📡 Live Data Sources"])
    
    with tab1:
        if apod_data:
            if apod_data.get('media_type') == 'image':
                st.image(apod_data['url'], caption=apod_data['title'], use_column_width=True)
                st.write(apod_data['explanation'])
            elif apod_data.get('media_type') == 'video':
                st.video(apod_data['url'])
                st.write(apod_data['explanation'])
            else:
                st.warning("Unsupported media type in APOD data")
        else:
            st.warning("Could not fetch current APOD data. NASA's demo key may have rate limit restrictions.")
    
    with tab2:
        st.header("Active Exoplanet Missions")
        missions = [
            {"name": "TESS", "status": "Active", "discoveries": "5,000+ candidates", "focus": "All-sky survey"},
            {"name": "James Webb Space Telescope", "status": "Active", "discoveries": "Atmospheric studies", "focus": "Characterization"},
            {"name": "Kepler", "status": "Completed", "discoveries": "2,800+ confirmed", "focus": "Planet statistics"}
        ]
        
        for mission in missions:
            with st.expander(f"🚀 {mission['name']} - {mission['status']}"):
                st.write(f"Discoveries: {mission['discoveries']}")
                st.write(f"Primary Focus: {mission['focus']}")
# ----------------------------
# PAGE 6: MISSION OVERVIEW
# ----------------------------
elif page == "📡 Mission Overview":
    st.title("📡 AESS Mission Overview")
    
    st.header("🎯 Scientific Purpose & Need")
    st.markdown("""
    The Artificial Intelligence Exoplanet Survey Satellite (AESS) addresses critical challenges in modern exoplanetary science:
    
    ### 🔬 The Data Complexity Problem
    - NASA archives contain complex, multi-parameter datasets from various missions and surveys
    - Raw astronomical data requires specialized knowledge to interpret and analyze
    - Multiple discovery methods (Transit, Radial Velocity, Microlensing, etc.) produce different data types
    
    ### 🌍 The Accessibility Challenge
    - Cutting-edge research should be accessible to educators, students, and enthusiasts
    - Real-time discovery data needs consolidated, understandable presentation
    - Interactive tools enable better understanding of orbital mechanics and planetary characteristics
    
    ### 🛰 Technical Architecture
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Data Sources")
        st.markdown("""
        - NASA Exoplanet Archive TAP Service
        - Planetary Systems (PS) Table - Confirmed planets
        - NASA APOD API
        - Live mission feeds and observational data
        """)
    
    with col2:
        st.subheader("Technology Stack")
        st.markdown("""
        - Streamlit - Reactive web application framework
        - Plotly - Interactive scientific visualizations
        - Pandas - Data processing and analysis
        - NASA APIs - Real-time data integration
        """)
    
    st.header("🚀 Future Enhancements")
    st.markdown("""
    - Additional NASA API integrations (TESS data feeds, JWST observations)
    - Machine learning analysis for pattern recognition in planetary characteristics
    - 3D orbital visualizations and virtual reality experiences
    - Educational curriculum integration for classroom use
    - Citizen science initiatives and public participation
    """)

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🛰 <b>AESS - Artificial Intelligence Exoplanet Survey Satellite</b></p>
        <p>Data sourced from <a href='https://exoplanetarchive.ipac.caltech.edu' target='_blank'>NASA Exoplanet Archive</a> • 
        Built with <a href='https://streamlit.io' target='_blank'>Streamlit</a> • 
        💫 Exploring new worlds through data</p>
    </div>
    """, 
    unsafe_allow_html=True
)






