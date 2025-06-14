import streamlit as st
import json
import os

def load_theme_settings():
    """Load theme settings from session state or set defaults"""
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'  # Default theme

def toggle_theme():
    """Toggle between light and dark theme"""
    if st.session_state.theme == 'light':
        st.session_state.theme = 'dark'
    else:
        st.session_state.theme = 'dark'

def get_theme_colors():
    """Get colors for current theme"""
    if st.session_state.theme == 'dark':
        return {
            'background': '#121212',
            'surface': '#1E1E1E',
            'primary': '#64B5F6',  # Lighter blue for better contrast in dark mode
            'secondary': '#81C784',  # Lighter green for better contrast
            'text': '#FFFFFF',
            'text_secondary': '#CCCCCC',  # Lighter gray for better contrast
            'border': '#444444',
            'success': '#81C784',  # Lighter green for better contrast
            'warning': '#FFD54F',  # Lighter yellow for better contrast
            'error': '#E57373',    # Lighter red for better contrast
            'info': '#64B5F6',     # Lighter blue for better contrast
            'card_text': '#FFFFFF', # Text color for cards in dark mode
            'card_heading': '#FFFFFF', # Heading color for cards in dark mode
        }
    else:
        return {
            'background': '#FFFFFF',
            'surface': '#F5F5F5',
            'primary': '#1E88E5',
            'secondary': '#4CAF50',
            'text': '#212121',
            'text_secondary': '#757575',
            'border': '#E0E0E0',
            'success': '#4CAF50',
            'warning': '#FFC107',
            'error': '#F44336',
            'info': '#2196F3',
            'card_text': '#212121', # Text color for cards in light mode
            'card_heading': '#212121', # Heading color for cards in light mode
        }

def apply_theme():
    """Apply theme to Streamlit app"""
    colors = get_theme_colors()
    
    # Apply theme using custom CSS
    css = f"""
    <style>
        /* Base colors */
        :root {{
            --background-color: {colors['background']};
            --surface-color: {colors['surface']};
            --primary-color: {colors['primary']};
            --secondary-color: {colors['secondary']};
            --text-color: {colors['text']};
            --text-secondary-color: {colors['text_secondary']};
            --border-color: {colors['border']};
        }}
        
        /* Override Streamlit's base styles */
        .stApp {{
            background-color: var(--background-color);
            color: var(--text-color);
        }}
        
        /* Main content */
        .main .block-container {{
            background-color: var(--background-color);
            color: var(--text-color);
        }}
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-color) !important;
        }}
        
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: var(--surface-color);
            border-right: 1px solid var(--border-color);
        }}
        
        /* Cards and containers */
        .stCard, div[data-testid="stExpander"] {{
            background-color: var(--surface-color) !important;
            border-color: var(--border-color) !important;
        }}
        
        /* Custom card class */
        .custom-card {{
            background-color: var(--surface-color);
            border-radius: 10px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }}
        
        /* Role badges */
        .role-badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            margin-right: 0.5rem;
        }}
        
        .role-badge-manager {{
            background-color: {colors['primary']};
            color: #FFFFFF;
        }}
        
        .role-badge-frontdesk {{
            background-color: {colors['success']};
            color: #FFFFFF;
        }}
        
        .role-badge-housekeeping {{
            background-color: {colors['warning']};
            color: #212121;
        }}
        
        .role-badge-maintenance {{
            background-color: {colors['info']};
            color: #FFFFFF;
        }}
        
        .role-badge-sales {{
            background-color: {colors['secondary']};
            color: #FFFFFF;
        }}
        
        .role-badge-inspector {{
            background-color: {colors['error']};
            color: #FFFFFF;
        }}
        
        /* Avatar */
        .user-avatar {{
            border-radius: 50%;
            border: 2px solid var(--primary-color);
        }}
        
        /* Message containers */
        .message-container {{
            padding: 0.8rem;
            border-radius: 10px;
            margin-bottom: 0.5rem;
        }}
        
        .message-sent {{
            background-color: var(--primary-color);
            color: #FFFFFF;
            border-top-right-radius: 0;
            margin-left: 1rem;
        }}
        
        .message-received {{
            background-color: var(--surface-color);
            border: 1px solid var(--border-color);
            border-top-left-radius: 0;
            margin-right: 1rem;
        }}
        
        /* Mobile navigation bar */
        .mobile-nav {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: var(--surface-color);
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-around;
            padding: 0.5rem 0;
            z-index: 1000;
        }}
        
        .mobile-nav-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            color: var(--text-secondary-color);
            text-decoration: none;
            font-size: 0.8rem;
        }}
        
        .mobile-nav-item.active {{
            color: var(--primary-color);
        }}
        
        /* Log entry */
        .log-entry {{
            padding: 1rem;
            border-left: 4px solid var(--primary-color);
            background-color: var(--surface-color);
            margin-bottom: 1rem;
            border-radius: 0 5px 5px 0;
        }}
        
        .log-entry-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }}
        
        .log-entry-title {{
            font-weight: 600;
            color: var(--text-color);
        }}
        
        .log-entry-meta {{
            font-size: 0.8rem;
            color: var(--text-secondary-color);
        }}
        
        .log-entry-message {{
            color: var(--text-color);
        }}
        
        /* Dividers */
        hr {{
            border-color: var(--border-color);
            margin: 1.5rem 0;
        }}
        
        /* Last-updated timestamp */
        .last-updated {{
            font-size: 0.8rem;
            color: var(--text-secondary-color);
            text-align: right;
            margin-top: 1rem;
        }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

def render_role_badge(role):
    """Render a role badge with appropriate styling"""
    role_class = role.lower().replace(" ", "")
    return f'<span class="role-badge role-badge-{role_class}">{role}</span>'

def format_timestamp(timestamp, format="%b %d, %Y %I:%M %p"):
    """Format a timestamp"""
    return timestamp.strftime(format)

def render_card(content, padding="1.5rem", margin="0 0 1rem 0"):
    """Render content in a card container"""
    colors = get_theme_colors()
    return f"""
    <div style="background-color: var(--surface-color); 
                border-radius: 10px; 
                padding: {padding}; 
                border: 1px solid var(--border-color); 
                margin: {margin}; 
                color: {colors['card_text']};">
        {content}
    </div>
    """

    
    st.markdown(is_mobile, unsafe_allow_html=True)
    
    # Add mobile-specific styles
    mobile_styles = """
    <style>
        @media (max-width: 768px) {
            /* Adjust main content to make room for bottom nav */
            .main .block-container {
                padding-bottom: 70px;
            }
            
            /* Hide sidebar on mobile */
            section[data-testid="stSidebar"] {
                display: none;
            }
            
            /* Make columns stack on mobile */
            .row-widget.stHorizontal {
                flex-direction: column;
            }
            
            /* Adjust metrics for mobile */
            [data-testid="stMetric"] {
                width: 100%;
            }
        }
    </style>
    """
    
    st.markdown(mobile_styles, unsafe_allow_html=True)
    
    # Create a component to handle navigation
    component_id = "mobile_nav_component"
    
    if component_id not in st.session_state:
        st.session_state[component_id] = None
    
    # Create simplified mobile navigation with buttons instead of JavaScript
    cols = st.columns(len(pages))
    
    for i, page in enumerate(pages):
        with cols[i]:
            is_active = page["page_id"] == active_page
            button_type = "primary" if is_active else "secondary"
            
            if st.button(
                f"{page['icon']}\n{page['name']}", 
                key=f"nav_{page['page_id']}",
                use_container_width=True,
                type=button_type
            ):
                st.session_state.page = page["page_id"]
                st.rerun()
    
    # Return empty string since we're using Streamlit components now
    return ""