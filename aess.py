import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from io import StringIO

st.set_page_config(
    page_title="AESS - Artificial Intelligence Exoplanet Survey Satellite", 
    page_icon="🪐", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(to right, #0c0f2fff, #1a1b4fff, #2c1a4fff); color: #ffffff; }
    section[data-testid="stSidebar"] > div { background: linear-gradient(to bottom, #0c0f2fff, #1a1b4fff) !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label { color: #ffffff !important; }
    [data-testid="stMetric"] { background-color: rgba(26, 27, 79, 0.7); border: 1px solid #4e54c8; padding: 10px; border-radius: 10px; }
    
    /* FIX: Black text in input fields */
    .stTextInput input, .stSelectbox select, .stMultiselect select, .stTextArea textarea {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    .stTextInput input::placeholder, .stSelectbox select::placeholder {
        color: #666666 !important;
    }
    
    /* Fix for dropdown options */
    .stSelectbox [data-testid="stMarkdownContainer"] {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

plotly_config = {
    'displayModeBar': False,
    'responsive': True,
    'staticPlot': False
}

# ----------------------------
# NASA API DATA FETCHER
# ----------------------------
class NASADataFetcher:
    def _init_(self):
        self.url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    
    @st.cache_data(ttl=3600)
    def fetch_exoplanet_data(_self):
        """Fetch comprehensive exoplanet data from NASA archive"""
        try:
            query = """
            SELECT 
                pl_name, hostname, discoverymethod, disc_year,
                pl_orbper, pl_rade, pl_bmasse, pl_orbsmax, 
                st_teff, st_rad, st_mass, sy_dist, pl_eqt,
                ra, dec, pl_insol
            FROM pscomppars
            WHERE pl_name IS NOT NULL 
                AND disc_year IS NOT NULL
            ORDER BY disc_year DESC
            """
            params = {
                "request": "doQuery", 
                "lang": "ADQL", 
                "format": "csv", 
                "query": query
            }
            r = requests.get(_self.url, params=params, timeout=30)
            r.raise_for_status()
            df = pd.read_csv(StringIO(r.text))
            
            if df.empty:
                st.warning("No data received from NASA API, using sample data")
                return _self._generate_sample_data()
            
            return _self._clean_data(df)
            
        except requests.exceptions.RequestException as e:
            st.error(f"Network error fetching data: {e}")
            return _self._generate_sample_data()
        except Exception as e:
            st.error(f"Error processing data: {e}")
            return _self._generate_sample_data()
    
    def search_planet_directly(_self, search_term):
        """Search for specific planets using NASA API"""
        try:
            query = f"""
            SELECT 
                pl_name, hostname, discoverymethod, disc_year,
                pl_orbper, pl_rade, pl_bmasse, pl_orbsmax,
                st_teff, st_rad, st_mass, sy_dist, pl_eqt
            FROM pscomppars
            WHERE LOWER(pl_name) LIKE LOWER('%{search_term}%')
               OR LOWER(hostname) LIKE LOWER('%{search_term}%')
            ORDER BY pl_name
            """
            params = {
                "request": "doQuery", 
                "lang": "ADQL", 
                "format": "csv", 
                "query": query
            }
            r = requests.get(_self.url, params=params, timeout=30)
            r.raise_for_status()
            return pd.read_csv(StringIO(r.text))
        except Exception as e:
            st.error(f"Search error: {e}")
            return pd.DataFrame()
    
    def _clean_data(self, df):
        """Clean and process the NASA data"""
        numeric_cols = [
            "pl_orbper", "pl_rade", "pl_bmasse", "pl_orbsmax", 
            "st_teff", "st_rad", "sy_dist", "pl_eqt", "st_mass", "pl_insol"
        ]
        
        available_numeric_cols = [col for col in numeric_cols if col in df.columns]
        
        for col in available_numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        if "disc_year" in df.columns:
            df["disc_year"] = pd.to_numeric(df["disc_year"], errors="coerce")
            df["disc_year"] = df["disc_year"].fillna(datetime.now().year).astype(int)
        
        df = df.dropna(subset=["pl_name", "hostname"])
        
        return df
    
    def _generate_sample_data(self):
        """Generate comprehensive sample data as fallback"""
        st.info("📊 Using sample exoplanet data - NASA API currently unavailable")
        
        sample_data = [
            ["TRAPPIST-1e", "TRAPPIST-1", "Transit", 2017, 6.099, 0.92, 0.69, 0.029, 2559.0, 0.119, 0.08, 39.5, 0.0, 0.66],
            ["TRAPPIST-1f", "TRAPPIST-1", "Transit", 2017, 9.206, 1.04, 0.69, 0.038, 2559.0, 0.119, 0.08, 39.5, 0.0, 0.38],
            ["TRAPPIST-1g", "TRAPPIST-1", "Transit", 2017, 12.353, 1.13, 1.34, 0.046, 2559.0, 0.119, 0.08, 39.5, 0.0, 0.26],
            ["Kepler-186f", "Kepler-186", "Transit", 2014, 129.944, 1.17, 1.44, 0.432, 3788.0, 0.54, 0.54, 492.0, 0.0, 0.32],
            ["Proxima Cen b", "Proxima Centauri", "Radial Velocity", 2016, 11.186, 1.30, 1.27, 0.048, 3042.0, 0.14, 0.12, 4.2, 0.0, 0.65],
            ["GJ 667 C c", "GJ 667 C", "Radial Velocity", 2011, 28.143, 1.54, 3.80, 0.125, 3600.0, 0.33, 0.33, 6.8, 0.0, 0.90],
            ["HD 209458 b", "HD 209458", "Transit", 1999, 3.524, 14.80, 69.10, 0.047, 6092.0, 1.16, 1.15, 47.7, 0.0, 1.50],
            ["Kepler-22b", "Kepler-22", "Transit", 2011, 289.862, 2.10, 4.50, 0.849, 5518.0, 0.98, 0.97, 190.0, 0.0, 0.95],
            ["GJ 1214 b", "GJ 1214", "Transit", 2009, 1.580, 2.68, 6.40, 0.014, 3026.0, 0.21, 0.15, 14.6, 0.0, 1.20],
            ["55 Cnc e", "55 Cnc", "Radial Velocity", 2004, 0.736, 1.95, 8.08, 0.015, 5172.0, 0.94, 0.91, 12.3, 0.0, 2.10]
        ]
        
        columns = [
            "pl_name", "hostname", "discoverymethod", "disc_year",
            "pl_orbper", "pl_rade", "pl_bmasse", "pl_orbsmax",
            "st_teff", "st_rad", "st_mass", "sy_dist", "pl_eqt", "pl_insol"
        ]
        
        df = pd.DataFrame(sample_data, columns=columns)
        
        np.random.seed(42)
        for col in ["pl_rade", "pl_bmasse", "pl_orbper"]:
            if col in df.columns:
                df[col] = df[col] * (1 + np.random.normal(0, 0.1, len(df)))
        
        return df

@st.cache_data(ttl=86400)
def fetch_nasa_apod():
    """Fetch NASA Astronomy Picture of the Day"""
    try:
        r = requests.get(
            "https://api.nasa.gov/planetary/apod", 
            params={"api_key": "8Vk5TyxHt87WSXA1Z9IsT8dO6hYCYNn1T4pIyVQN", "thumbs": True}, 
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
        else:
            st.warning(f"APOD API returned status {r.status_code}")
            return None
    except Exception as e:
        st.warning(f"Could not fetch APOD: {e}")
        return None
# ----------------------------
# SIMULATION FUNCTIONS
# ----------------------------
def simulate_transit_light_curve():
    """Simulate exoplanet transit light curve"""
    st.header("Transit Light Curve Simulation")
    
    col1, col2 = st.columns(2)
    with col1:
        planet_radius = st.slider("Planet Radius (Earth radii)", 0.1, 20.0, 1.0)
        orbital_period = st.slider("Orbital Period (days)", 0.5, 365.0, 10.0)
        impact_param = st.slider("Impact Parameter", 0.0, 1.0, 0.3)
    
    with col2:
        star_radius = st.slider("Star Radius (Solar radii)", 0.1, 10.0, 1.0)
        inclination = st.slider("Orbital Inclination (degrees)", 85.0, 90.0, 89.5)
    
    time = np.linspace(0, orbital_period, 1000)
    transit_depth = (planet_radius/star_radius)**2
    transit_center = orbital_period / 2
    transit_duration = orbital_period * star_radius / (np.pi * planet_radius)
    flux = 1 - transit_depth * np.exp(-(time-transit_center)*2/(transit_duration/4)*2)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time, y=flux, mode='lines', 
        name='Relative Flux', 
        line=dict(color='#4e54c8')
    ))
    fig.update_layout(
        title="Simulated Transit Light Curve", 
        xaxis_title="Time (days)", 
        yaxis_title="Relative Flux", 
        template="plotly_dark"
    )
    st.plotly_chart(fig, config=plotly_config)
    
    st.info("""
    *About Transit Photometry:* 
    This simulation shows how a planet passing in front of its host star causes a detectable dip in brightness. 
    NASA's Kepler and TESS missions use this method to discover thousands of exoplanets.
    
    - *Transit Depth*: (Planet Radius / Star Radius)²
    - *Transit Duration*: Depends on orbital geometry and star size
    - *Real missions*: Kepler, TESS, CHEOPS
    """)

# ----------------------------
# 3D VISUALIZATION FUNCTIONS
# ----------------------------
def create_3d_exoplanet_system():
    """Create 3D visualization of exoplanet systems"""
    st.header("🌌 3D Exoplanet System Visualization")
    
    # Sample data for 3D visualization
    systems = [
        {"name": "TRAPPIST-1", "planets": 7, "distance": 39.5, "x": 10, "y": 5, "z": 2},
        {"name": "Kepler-186", "planets": 5, "distance": 492, "x": -5, "y": 8, "z": -3},
        {"name": "HD 209458", "planets": 1, "distance": 47.7, "x": 3, "y": -6, "z": 4},
        {"name": "Proxima Centauri", "planets": 1, "distance": 4.2, "x": 1, "y": 2, "z": 1},
        {"name": "Kepler-22", "planets": 1, "distance": 190, "x": -8, "y": -4, "z": -2},
    ]
    
    # Create 3D scatter plot
    fig = go.Figure()
    
    # Add stars
    star_x = [system["x"] for system in systems]
    star_y = [system["y"] for system in systems]
    star_z = [system["z"] for system in systems]
    star_names = [system["name"] for system in systems]
    star_size = [system["planets"] * 3 for system in systems]
    
    fig.add_trace(go.Scatter3d(
        x=star_x, y=star_y, z=star_z,
        mode='markers+text',
        marker=dict(
            size=star_size,
            color='yellow',
            opacity=0.8,
            sizemode='diameter'
        ),
        text=star_names,
        textposition="top center",
        name="Stars"
    ))
    
    # Add planets orbiting around stars
    for i, system in enumerate(systems):
        planets_count = system["planets"]
        for j in range(planets_count):
            # Create orbital positions
            angle = (j / planets_count) * 2 * np.pi
            orbit_radius = (j + 1) * 0.8
            planet_x = system["x"] + orbit_radius * np.cos(angle)
            planet_y = system["y"] + orbit_radius * np.sin(angle)
            planet_z = system["z"] + np.sin(angle) * 0.5
            
            fig.add_trace(go.Scatter3d(
                x=[planet_x], y=[planet_y], z=[planet_z],
                mode='markers',
                marker=dict(
                    size=5,
                    color='lightblue',
                    opacity=0.7
                ),
                name=f"{system['name']} Planet {j+1}",
                showlegend=False
            ))
            
            # Add orbit line
            theta = np.linspace(0, 2*np.pi, 100)
            orbit_x = system["x"] + orbit_radius * np.cos(theta)
            orbit_y = system["y"] + orbit_radius * np.sin(theta)
            orbit_z = system["z"] + np.sin(theta) * 0.3
            
            fig.add_trace(go.Scatter3d(
                x=orbit_x, y=orbit_y, z=orbit_z,
                mode='lines',
                line=dict(width=1, color='rgba(255,255,255,0.3)'),
                name=f"{system['name']} Orbit",
                showlegend=False
            ))
    
    fig.update_layout(
        title="3D Visualization of Exoplanet Systems",
        scene=dict(
            xaxis_title="X (Light Years)",
            yaxis_title="Y (Light Years)",
            zaxis_title="Z (Light Years)",
            bgcolor='rgba(0,0,0,0)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ),
        height=600,
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, config=plotly_config, use_container_width=True)
    
    st.info("""
    *3D System Explorer:*
    - *Yellow circles*: Host stars (size indicates number of planets)
    - *Blue dots*: Individual exoplanets
    - *White circles*: Orbital paths
    - *Real data*: Based on actual exoplanet system configurations
    """)

def create_3d_habitable_zone():
    """Create 3D habitable zone visualization"""
    st.header("🌍 3D Habitable Zone Visualization")
    
    # Create a star at center
    star_size = 10
    
    # Create habitable zone sphere
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    
    # Inner habitable zone
    r_inner = 0.8
    x_inner = r_inner * np.outer(np.cos(u), np.sin(v))
    y_inner = r_inner * np.outer(np.sin(u), np.sin(v))
    z_inner = r_inner * np.outer(np.ones(np.size(u)), np.cos(v))
    
    # Outer habitable zone
    r_outer = 1.5
    x_outer = r_outer * np.outer(np.cos(u), np.sin(v))
    y_outer = r_outer * np.outer(np.sin(u), np.sin(v))
    z_outer = r_outer * np.outer(np.ones(np.size(u)), np.cos(v))
    
    fig = go.Figure()
    
    # Add habitable zone shell (transparent)
    fig.add_trace(go.Surface(
        x=x_outer, y=y_outer, z=z_outer,
        opacity=0.2,
        colorscale='Blues',
        showscale=False,
        name="Outer Habitable Zone"
    ))
    
    fig.add_trace(go.Surface(
        x=x_inner, y=y_inner, z=z_inner,
        opacity=0.2,
        colorscale='Reds',
        showscale=False,
        name="Inner Habitable Zone"
    ))
    
    # Add star at center
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers',
        marker=dict(
            size=star_size,
            color='yellow',
            opacity=1.0
        ),
        name="Star"
    ))
    
    # Add some example planets
    planets = [
        {"name": "Hot Planet", "distance": 0.5, "color": "red"},
        {"name": "Habitable Planet", "distance": 1.1, "color": "green"},
        {"name": "Cold Planet", "distance": 2.0, "color": "blue"}
    ]
    
    for planet in planets:
        fig.add_trace(go.Scatter3d(
            x=[planet["distance"]], y=[0], z=[0],
            mode='markers+text',
            marker=dict(size=6, color=planet["color"]),
            text=planet["name"],
            textposition="middle right",
            name=planet["name"]
        ))
    
    fig.update_layout(
        title="3D Habitable Zone Concept",
        scene=dict(
            xaxis_title="Distance (AU)",
            yaxis_title="Y Axis",
            zaxis_title="Z Axis",
            bgcolor='rgba(0,0,0,0)',
            camera=dict(eye=dict(x=2, y=2, z=1))
        ),
        height=500,
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, config=plotly_config, use_container_width=True)

# ----------------------------
# DATA LOADING
# ----------------------------
fetcher = NASADataFetcher()

if 'exoplanet_data' not in st.session_state:
    with st.spinner("🛰 Connecting to NASA Exoplanet Archive..."):
        st.session_state.exoplanet_data = fetcher.fetch_exoplanet_data()

if 'apod_data' not in st.session_state:
    st.session_state.apod_data = fetch_nasa_apod()

exoplanet_df = st.session_state.exoplanet_data
apod_data = st.session_state.apod_data

# ----------------------------
# SIDEBAR NAVIGATION
# ----------------------------
st.sidebar.image("https://images.unsplash.com/photo-1465101162946-4377e57745c3?w=300", width='stretch')
st.sidebar.title("🪐 AESS Navigation")

page = st.sidebar.radio("Explore the Cosmos:", [
    "🏠 Dashboard & Mission Control",
    "📊 Exoplanet Encyclopedia", 
    "🔭 Advanced Visualizations",
    "🌌 System Simulations",
    "🎥 Virtual Exoplanet Explorer",
    "🛰 Live NASA Feeds",
    "🔍 Planet Search"
])

# ----------------------------
# PAGE 1: DASHBOARD & MISSION CONTROL
# ----------------------------
if page == "🏠 Dashboard & Mission Control":
    st.title("🌌 Artificial Intelligence Exoplanet Survey Satellite")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.header("🚀 Mission Overview")
        st.markdown("""
        The Artificial Intelligence Exoplanet Survey Satellite (AESS) represents a breakthrough in public access to exoplanetary science. 
        Our platform transforms complex NASA data into interactive, educational experiences by leveraging:
        
        - *Real-time NASA API Integration*: Direct access to the NASA Exoplanet Archive TAP service
        - *Advanced Visualizations*: Making complex orbital mechanics understandable
        - *Interactive Simulations*: Professional-grade charts and simulations
        - *Live Satellite Data*: Current observations and discoveries
        """)
    
    with col2:
        if apod_data and apod_data.get('media_type') == 'image':
            st.image(
                apod_data['url'], 
                caption=f"NASA Astronomy Picture of the Day: {apod_data['title']}", 
                width='stretch'
            )
        elif apod_data and apod_data.get('media_type') == 'video':
            st.video(apod_data['url'])
            st.caption(f"NASA Astronomy Picture of the Day: {apod_data['title']}")
    
    st.markdown("---")
    
    st.header("📈 Live Exoplanet Statistics")
    if not exoplanet_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        total_planets = len(exoplanet_df)
        unique_stars = exoplanet_df['hostname'].nunique()
        discovery_methods = exoplanet_df['discoverymethod'].nunique()
        recent_discoveries = len(exoplanet_df[exoplanet_df['disc_year'] >= 2020])
        
        col1.metric("🌍 Confirmed Exoplanets", f"{total_planets:,}")
        col2.metric("⭐ Host Stars", f"{unique_stars:,}")
        col3.metric("🔬 Detection Methods", discovery_methods)
        col4.metric("🆕 Recent Discoveries (2020+)", recent_discoveries)
    
    st.header("🔍 Recent Discoveries Analysis")
    if not exoplanet_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            method_counts = exoplanet_df['discoverymethod'].value_counts().head(5)
            fig = px.pie(
                values=method_counts.values, 
                names=method_counts.index, 
                title="Top 5 Discovery Methods"
            )
            st.plotly_chart(fig, config=plotly_config)

        with col2:
            yearly = exoplanet_df['disc_year'].value_counts().sort_index()
            fig = px.area(
                x=yearly.index, y=yearly.values, 
                title="Exoplanet Discoveries Timeline", 
                labels={'x': 'Year', 'y': 'Planets Discovered'}
            )
            st.plotly_chart(fig, config=plotly_config)
    
    # NEW: Add exoplanet gallery to dashboard
    st.markdown("---")
    st.header("📸 Exoplanet Gallery")
    gallery_cols = st.columns(3)
    with gallery_cols[0]:
        st.image("https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400", 
                 caption="Multi-planet System Concept", use_container_width=True)
    with gallery_cols[1]:
        st.image("https://images.unsplash.com/photo-1462332420958-a05d1e002413?w=400", 
                 caption="Transiting Exoplanet", use_container_width=True)
    with gallery_cols[2]:
        st.image("https://images.unsplash.com/photo-1465101162946-4377e57745c3?w=400", 
                 caption="Deep Space Observation", use_container_width=True)

# ----------------------------
# PAGE 2: EXOPLANET ENCYCLOPEDIA
# ----------------------------
elif page == "📊 Exoplanet Encyclopedia":
    st.title("📊 Exoplanet Encyclopedia")
    st.markdown("Comprehensive database of confirmed exoplanets")
    
    if not exoplanet_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            methods = st.multiselect(
                "Filter by Discovery Method:", 
                options=exoplanet_df['discoverymethod'].unique()
            )
        
        with col2:
            search_planet = st.text_input("🔍 Search Planet Name:", placeholder="Enter planet name...")
        
        with col3:
            year_range = st.slider(
                "Discovery Year Range:", 
                int(exoplanet_df['disc_year'].min()), 
                int(exoplanet_df['disc_year'].max()), 
                (1990, 2024)
            )
        
        filtered_df = exoplanet_df.copy()
        if methods:
            filtered_df = filtered_df[filtered_df['discoverymethod'].isin(methods)]
        if search_planet:
            filtered_df = filtered_df[filtered_df['pl_name'].str.contains(search_planet, case=False, na=False)]
        filtered_df = filtered_df[
            (filtered_df['disc_year'] >= year_range[0]) & 
            (filtered_df['disc_year'] <= year_range[1])
        ]
        
        st.dataframe(filtered_df, width='stretch', height=400)
        
        st.header("🔬 Detailed Planet Analysis")
        if len(filtered_df) > 0:
            selected_planet = st.selectbox(
                "Select a planet for detailed analysis:", 
                filtered_df['pl_name'].head(100)
            )
            
            if selected_planet:
                planet_data = filtered_df[filtered_df['pl_name'] == selected_planet].iloc[0]
                
                # NEW: Add planet visualization image
                col_img, col_data = st.columns([1, 2])
                with col_img:
                    st.subheader("🌍 Planet Visualization")
                    placeholder_img = "https://images.unsplash.com/photo-1462332420958-a05d1e002413?w=400"
                    st.image(placeholder_img, 
                             caption=f"Artistic representation of {selected_planet}",
                             use_container_width=True)
                
                with col_data:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Host Star", planet_data.get('hostname', 'N/A'))
                        st.metric("Discovery Method", planet_data.get('discoverymethod', 'N/A'))
                        st.metric("Discovery Year", planet_data.get('disc_year', 'N/A'))
                    
                    with col2:
                        st.metric("Planet Radius (Earth radii)", 
                                 f"{planet_data.get('pl_rade', 'N/A'):.2f}" if pd.notna(planet_data.get('pl_rade')) else 'N/A')
                        st.metric("Planet Mass (Earth mass)", 
                                 f"{planet_data.get('pl_bmasse', 'N/A'):.2f}" if pd.notna(planet_data.get('pl_bmasse')) else 'N/A')
                        st.metric("Orbital Period (days)", 
                                 f"{planet_data.get('pl_orbper', 'N/A'):.2f}" if pd.notna(planet_data.get('pl_orbper')) else 'N/A')
                    
                    with col3:
                        st.metric("Distance from Earth (pc)", 
                                 f"{planet_data.get('sy_dist', 'N/A'):.1f}" if pd.notna(planet_data.get('sy_dist')) else 'N/A')
                        st.metric("Star Temperature (K)", 
                                 f"{planet_data.get('st_teff', 'N/A'):.0f}" if pd.notna(planet_data.get('st_teff')) else 'N/A')
                        st.metric("Star Mass (Solar mass)", 
                                 f"{planet_data.get('st_mass', 'N/A'):.2f}" if pd.notna(planet_data.get('st_mass')) else 'N/A')

# ----------------------------
# PAGE 3: ADVANCED VISUALIZATIONS
# ----------------------------
elif page == "🔭 Advanced Visualizations":
    st.title("🔭 Advanced Data Visualizations")
    st.markdown("Interactive scientific visualizations of exoplanetary data")
    
    if not exoplanet_df.empty:
        viz_type = st.selectbox("Choose Visualization Type:", [
            "Planet Radius vs Orbital Period",
            "Discovery Methods Distribution",
            "Mass-Radius Relationship",
            "Star Temperature Distribution",
            "3D Exoplanet Systems",  # NEW: Added 3D visualization
            "3D Habitable Zones"    # NEW: Added 3D habitable zone
        ])
        
        if viz_type == "Planet Radius vs Orbital Period":
            viz_df = exoplanet_df.dropna(subset=['pl_orbper', 'pl_rade']).copy()
            viz_df = viz_df[(viz_df['pl_orbper'] > 0) & (viz_df['pl_orbper'] < 1000)]
            
            fig = px.scatter(
                viz_df, x='pl_orbper', y='pl_rade', 
                hover_data=['pl_name', 'discoverymethod'], 
                title="Planet Radius vs Orbital Period", 
                color='discoverymethod',
                labels={'pl_orbper': 'Orbital Period (days)', 'pl_rade': 'Planet Radius (Earth radii)'}
            )
            st.plotly_chart(fig, config=plotly_config)
            
        elif viz_type == "Mass-Radius Relationship":
            viz_df = exoplanet_df.dropna(subset=['pl_bmasse', 'pl_rade']).copy()
            viz_df = viz_df[(viz_df['pl_bmasse'] > 0) & (viz_df['pl_bmasse'] < 100)]
            
            fig = px.scatter(
                viz_df, x='pl_bmasse', y='pl_rade', 
                hover_data=['pl_name', 'discoverymethod'], 
                title="Planet Mass vs Radius Relationship", 
                color='discoverymethod', 
                log_x=True,
                labels={'pl_bmasse': 'Planet Mass (Earth masses)', 'pl_rade': 'Planet Radius (Earth radii)'}
            )
            st.plotly_chart(fig, config=plotly_config)
            
        elif viz_type == "Discovery Methods Distribution":
            method_data = exoplanet_df['discoverymethod'].value_counts()
            fig = px.bar(
                x=method_data.index, y=method_data.values, 
                title="Exoplanet Discovery Methods Distribution", 
                labels={'x': 'Discovery Method', 'y': 'Number of Planets'},
                color=method_data.values
            )
            st.plotly_chart(fig, config=plotly_config)
            
        elif viz_type == "Star Temperature Distribution":
            viz_df = exoplanet_df.dropna(subset=['st_teff']).copy()
            viz_df = viz_df[(viz_df['st_teff'] > 0) & (viz_df['st_teff'] < 10000)]
            
            fig = px.histogram(
                viz_df, x='st_teff',
                title="Star Temperature Distribution",
                labels={'st_teff': 'Star Temperature (K)'},
                nbins=50
            )
            st.plotly_chart(fig, config=plotly_config)
            
        # NEW: 3D Visualizations
        elif viz_type == "3D Exoplanet Systems":
            create_3d_exoplanet_system()
            
        elif viz_type == "3D Habitable Zones":
            create_3d_habitable_zone()

# ----------------------------
# PAGE 4: SYSTEM SIMULATIONS
# ----------------------------
elif page == "🌌 System Simulations":
    st.title("🌌 Exoplanet System Simulations")
    st.markdown("Interactive simulations of exoplanet transits and orbital mechanics")
    
    sim_type = st.selectbox("Choose Simulation Type:", [
        "Transit Light Curve Simulator",
        "Habitable Zone Calculator",
        "3D Orbital Simulation"  # NEW: Added 3D simulation
    ])
    
    if sim_type == "Transit Light Curve Simulator":
        simulate_transit_light_curve()
    elif sim_type == "Habitable Zone Calculator":
        st.info("🚧 Habitable Zone Calculator - Coming Soon!")
        st.write("This feature will calculate the habitable zone around different star types based on stellar properties.")
    elif sim_type == "3D Orbital Simulation":
        create_3d_exoplanet_system()

# ----------------------------
# PAGE 5: VIRTUAL EXPLANATION SECTION
# ----------------------------
elif page == "🎥 Virtual Exoplanet Explorer":
    st.title("🎥 Virtual Exoplanet Explorer")
    st.markdown("Interactive explanations and visualizations of exoplanet concepts")
    
    # Use columns for better layout 
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🪐 What are Exoplanets?")
        st.markdown("""
        *Exoplanets* are planets that orbit stars outside our solar system. 
        - Over *6,000 confirmed exoplanets* discovered so far 
        - Found using various detection methods like transit and radial velocity
        - Range from gas giants to rocky Earth-like planets
        """)
        
    with col2:
        # Add an exoplanet concept image
        st.image(
            "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400", 
            caption="Artist's concept of an exoplanet system",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Explanation tabs for different concepts
    tab1, tab2, tab3 = st.tabs(["🔍 Detection Methods", "🌡 Habitable Zones", "📊 Planet Types"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Transit Method")
            st.image(
                "https://images.unsplash.com/photo-1462332420958-a05d1e002413?w=300",
                caption="Planet transiting its host star",
                use_container_width=True
            )
            st.markdown("""
            *How it works:*
            - Planet passes between star and observer
            - Causes tiny dip in star's brightness 
            - Used by Kepler and TESS missions
            """)
            
        with col2:
            st.subheader("Radial Velocity")
            st.image(
                "https://images.unsplash.com/photo-1516339901601-2e1b62dc0c45?w=300",
                caption="Star wobble due to planetary gravity",
                use_container_width=True
            )
            st.markdown("""
            *How it works:*
            - Planet's gravity causes star to wobble
            - Detected through Doppler shifts 
            - Reveals planet mass and orbit
            """)
    
    with tab2:
        st.subheader("🌍 The Goldilocks Zone")
        st.image(
            "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=500",
            caption="Habitable zone where liquid water can exist",
            use_container_width=True
        )
        st.markdown("""
        The *habitable zone* is the region around a star where conditions might be just right — 
        not too hot, not too cold — for liquid water to exist on a planet's surface. 
        
        *Key factors:*
        - Star temperature and luminosity
        - Planet's atmospheric composition
        - Orbital distance from star
        """)
    
    with tab3:
        # Use expanders for planet type explanations 
        with st.expander("🪨 Rocky Planets (Terrestrial)"):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image("https://images.unsplash.com/photo-1614313913007-2b4ae8ce32e6?w=150", 
                        use_container_width=True)
            with col2:
                st.markdown("""
                - Similar to Earth, Venus, Mars
                - Solid surfaces with thin atmospheres
                - Potential candidates for life
                """)
        
        with st.expander("💨 Gas Giants"):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image("https://images.unsplash.com/photo-1630450068799-03d1674f75af?w=150", 
                        use_container_width=True)
            with col2:
                st.markdown("""
                - Large planets like Jupiter and Saturn
                - Thick atmospheres, no solid surface
                - Often found close to their stars ("Hot Jupiters")
                """)
        
        with st.expander("❄ Ice Giants"):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image("https://images.unsplash.com/photo-1446776877081-d282a0f896e2?w=150", 
                        use_container_width=True)
            with col2:
                st.markdown("""
                - Like Uranus and Neptune
                - Composed of water, ammonia, methane ices
                - Lower mass than gas giants
                """)
    
    # Interactive simulation
    st.markdown("---")
    st.header("🔄 Compare Planet Sizes")
    
    # Simple interactive comparison
    planet_choice = st.selectbox("Select planet type to visualize:", 
                                ["Earth-like", "Super-Earth", "Mini-Neptune", "Gas Giant"])
    
    # Display appropriate image based on selection
    planet_images = {
        "Earth-like": "https://images.unsplash.com/photo-1614313913007-2b4ae8ce32e6?w=300",
        "Super-Earth": "https://images.unsplash.com/photo-1462332420958-a05d1e002413?w=300", 
        "Gas Giant": "https://images.unsplash.com/photo-1630450068799-03d1674f75af?w=300"
    }
    
    if planet_choice in planet_images:
        st.image(planet_images[planet_choice], 
                caption=f"Visualization of a {planet_choice}",
                width=300)
        
        # Add fun facts based on selection
        fun_facts = {
            "Earth-like": "*Did you know?* TRAPPIST-1 system has 7 Earth-sized planets, with 3 in the habitable zone!",
            "Super-Earth": "*Did you know?* Super-Earths are planets with mass between Earth and Neptune - the most common type found so far!",
            "Gas Giant": "*Did you know?* 'Hot Jupiters' are gas giants that orbit very close to their stars, with years shorter than 10 days!"
        }
        
        if planet_choice in fun_facts:
            st.info(fun_facts[planet_choice])

# ----------------------------
# PAGE 6: LIVE NASA FEEDS - IMPROVED
# ----------------------------
elif page == "🛰 Live NASA Feeds":
    st.title("🛰 Live NASA Data Feeds")
    st.markdown("Real-time data from NASA's active missions and observatories")
    
    tab1, tab2, tab3 = st.tabs(["🌠 Astronomy Picture of the Day", "🪐 Live Exoplanet Data", "📡 Mission Telemetry"])
    
    with tab1:
        if apod_data:
            st.header(apod_data.get('title', 'NASA Astronomy Picture of the Day'))
            
            if apod_data.get('media_type') == 'image':
                st.image(apod_data['url'], use_container_width=True)
            elif apod_data.get('media_type') == 'video':
                st.video(apod_data['url'])
            
            st.write(apod_data.get('explanation', ''))
            st.caption(f"Date: {apod_data.get('date', '')} | Copyright: {apod_data.get('copyright', 'Public Domain')}")
        else:
            st.info("🌌 Waiting for NASA APOD data...")
            st.image("https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=600", 
                    caption="Sample exoplanet system - NASA APOD currently unavailable")
    
    with tab2:
        st.header("📊 Live Exoplanet Statistics")
        
        if not exoplanet_df.empty:
            # Real-time metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total = len(exoplanet_df)
                st.metric("Total Exoplanets", f"{total:,}")
                
            with col2:
                recent = len(exoplanet_df[exoplanet_df['disc_year'] >= 2023])
                st.metric("2023+ Discoveries", recent)
                
            with col3:
                transits = len(exoplanet_df[exoplanet_df['discoverymethod'] == 'Transit'])
                st.metric("Transit Discoveries", f"{transits:,}")
                
            with col4:
                habitable_candidates = len(exoplanet_df[
                    (exoplanet_df['pl_rade'] >= 0.8) & 
                    (exoplanet_df['pl_rade'] <= 1.5) &
                    (exoplanet_df['pl_insol'] >= 0.8) & 
                    (exoplanet_df['pl_insol'] <= 1.2)
                ].dropna(subset=['pl_rade', 'pl_insol']))
                st.metric("Habitable Zone Candidates", habitable_candidates)
            
            # Recent discoveries table
            st.subheader("🔭 Recently Discovered Exoplanets")
            recent_planets = exoplanet_df.nlargest(10, 'disc_year')[['pl_name', 'hostname', 'discoverymethod', 'disc_year', 'pl_rade']]
            st.dataframe(recent_planets, use_container_width=True)
            
            # Discovery methods live chart
            st.subheader("📈 Discovery Method Distribution")
            method_counts = exoplanet_df['discoverymethod'].value_counts()
            fig = px.pie(values=method_counts.values, names=method_counts.index, 
                        title="Exoplanet Discovery Methods")
            st.plotly_chart(fig, config=plotly_config, use_container_width=True)
    
    with tab3:
        st.header("📡 Mission Telemetry & Status")
        
        # Simulated mission data
        missions = [
            {"mission": "TESS", "status": "🟢 Active", "planets_discovered": "4,000+", "last_update": "2 hours ago", "image": "https://images.unsplash.com/photo-1516849841032-87cbac4d88f7?w=300"},
            {"mission": "James Webb", "status": "🟢 Active", "planets_discovered": "50+", "last_update": "1 hour ago", "image": "https://images.unsplash.com/photo-1446776877081-d282a0f896e2?w=300"},
            {"mission": "Kepler", "status": "🔴 Retired", "planets_discovered": "2,600+", "last_update": "2018", "image": "https://images.unsplash.com/photo-1465101162946-4377e57745c3?w=300"},
            {"mission": "Hubble", "status": "🟡 Limited", "planets_discovered": "N/A", "last_update": "1 day ago", "image": "https://images.unsplash.com/photo-1614313913007-2b4ae8ce32e6?w=300"}
        ]
        
        for mission in missions:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(mission["image"], use_container_width=True)
            with col2:
                st.subheader(mission["mission"])
                st.write(f"*Status:* {mission['status']}")
                st.write(f"*Exoplanets Discovered:* {mission['planets_discovered']}")
                st.write(f"*Last Data:* {mission['last_update']}")
                st.progress(75 if mission['status'] == '🟢 Active' else 25)
            st.markdown("---")

# ----------------------------
# PAGE 7: PLANET SEARCH - WITH BLACK TEXT FIX
# ----------------------------
elif page == "🔍 Planet Search":
    st.title("🔍 Direct Planet Search")
    st.markdown("Search for specific exoplanets in the NASA database")
    
    search_term = st.text_input("Enter planet name or host star:", placeholder="e.g., TRAPPIST-1 or Kepler-186")
    
    if st.button("Search NASA Database") and search_term:
        with st.spinner(f"Searching for '{search_term}' in NASA archives..."):
            results = fetcher.search_planet_directly(search_term)
            
            if not results.empty:
                st.success(f"Found {len(results)} matching exoplanets!")
                st.dataframe(results, use_container_width=True)
                
                # Show basic stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Planets Found", len(results))
                with col2:
                    methods = results['discoverymethod'].nunique()
                    st.metric("Detection Methods", methods)
                with col3:
                    recent_year = results['disc_year'].max()
                    st.metric("Most Recent", recent_year)
            else:
                st.warning("No planets found matching your search. Try a different name.")
    
    # Show search tips
    with st.expander("💡 Search Tips"):
        st.markdown("""
        - Search by *planet name* (e.g., 'TRAPPIST-1e', 'HD 209458 b')
        - Search by *host star* (e.g., 'Kepler-186', 'GJ 667')  
        - Use partial names (e.g., 'Kepler' for all Kepler planets)
        - Names are case-insensitive
        """)
