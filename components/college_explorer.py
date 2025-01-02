import streamlit as st
import plotly.express as px
import pandas as pd
from models.database import Database
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)

def get_user_favorites() -> List[int]:
    """Get list of institution IDs favorited by the current user."""
    if not hasattr(st.session_state, 'user'):
        return []

    try:
        db = Database()
        favorites = db.execute("""
            SELECT institution_id 
            FROM user_favorite_institutions 
            WHERE user_id = %s
        """, (st.session_state.user.id,))
        return [f['institution_id'] for f in favorites]
    except Exception as e:
        logger.error(f"Error fetching user favorites: {str(e)}")
        return []

def toggle_favorite(institution_id: int):
    """Toggle favorite status for an institution."""
    if not hasattr(st.session_state, 'user'):
        st.warning("Please log in to save favorites.")
        return

    try:
        db = Database()
        # Check if already favorited
        existing = db.execute_one("""
            SELECT id FROM user_favorite_institutions 
            WHERE user_id = %s AND institution_id = %s
        """, (st.session_state.user.id, institution_id))

        if existing:
            db.execute("""
                DELETE FROM user_favorite_institutions 
                WHERE user_id = %s AND institution_id = %s
            """, (st.session_state.user.id, institution_id))
            st.success("Removed from favorites!")
        else:
            db.execute("""
                INSERT INTO user_favorite_institutions (user_id, institution_id)
                VALUES (%s, %s)
            """, (st.session_state.user.id, institution_id))
            st.success("Added to favorites!")

        # Force streamlit to rerun to update the UI
        st.rerun()
    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}")
        st.error("Failed to update favorites. Please try again.")

def calculate_admission_chance(student_profile: Dict, institution_stats: Dict) -> float:
    """Calculate rough admission chance based on student profile and institution stats."""
    # This is a simplified calculation - we can make it more sophisticated later
    base_chance = 0.5

    # SAT score comparison
    if student_profile.get('sat_score') and institution_stats.get('sat_75th_percentile'):
        if student_profile['sat_score'] >= institution_stats['sat_75th_percentile']:
            base_chance += 0.3
        elif student_profile['sat_score'] >= institution_stats['sat_75th_percentile'] * 0.9:
            base_chance += 0.15

    # GPA comparison (if available)
    if student_profile.get('gpa') and institution_stats.get('avg_gpa'):
        if student_profile['gpa'] >= institution_stats['avg_gpa']:
            base_chance += 0.2

    # Cap the chance at 95%
    return min(0.95, base_chance)

def render_geographic_view():
    """Render the geographic distribution view with filters."""
    st.subheader("Geographic Distribution")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        selected_states = st.multiselect(
            "Select States",
            options=sorted(list(set(st.session_state.get('all_states', [])))),
            placeholder="All States"
        )

    with col2:
        institution_types = st.multiselect(
            "Institution Type",
            options=["Public", "Private Not-for-Profit", "Private For-Profit"],
            placeholder="All Types"
        )

    # Fetch filtered data
    try:
        db = Database()
        query = """
            SELECT 
                state_abbreviation,
                COUNT(*) as count,
                control_of_institution
            FROM institutions
            WHERE 1=1
        """
        params = []

        if selected_states:
            query += " AND state_abbreviation = ANY(%s)"
            params.append(selected_states)

        if institution_types:
            query += " AND control_of_institution = ANY(%s)"
            params.append(institution_types)

        query += " GROUP BY state_abbreviation, control_of_institution"

        results = db.execute(query, tuple(params))

        if results:
            # Convert to DataFrame for plotting
            df = pd.DataFrame(results)

            # Create choropleth map
            fig = px.choropleth(
                df,
                locations='state_abbreviation',
                locationmode="USA-states",
                color='count',
                scope="usa",
                color_continuous_scale="Viridis",
                title="Institution Distribution by State"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Show statistics
            st.markdown("### Quick Statistics")
            total_institutions = sum(r['count'] for r in results)
            st.write(f"Total Institutions: {total_institutions}")

            # Show distribution by type
            if institution_types:
                st.write("Distribution by Type:")
                for type_name in institution_types:
                    type_count = sum(r['count'] for r in results if r['control_of_institution'] == type_name)
                    st.write(f"- {type_name}: {type_count} ({(type_count/total_institutions*100):.1f}%)")

        else:
            st.info("No institutions found matching the selected criteria.")

    except Exception as e:
        logger.error(f"Error rendering geographic view: {str(e)}")
        st.error("Failed to load geographic distribution data.")

def render_college_explorer():
    """Main function to render the college explorer dashboard."""
    st.title("🏛️ College Explorer Dashboard")

    if not hasattr(st.session_state, 'user'):
        st.warning("Please log in to access all features of the College Explorer.")
        return

    # Initialize session state for filters if needed
    if 'all_states' not in st.session_state:
        try:
            db = Database()
            states = db.execute("SELECT DISTINCT state_abbreviation FROM institutions ORDER BY state_abbreviation")
            st.session_state.all_states = [s['state_abbreviation'] for s in states if s['state_abbreviation']]
        except Exception as e:
            logger.error(f"Error fetching states: {str(e)}")
            st.session_state.all_states = []

    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs([
        "Geographic View",
        "Cost Analysis",
        "Housing & Facilities"
    ])

    with tab1:
        render_geographic_view()

    with tab2:
        st.info("Cost Analysis features coming soon!")

    with tab3:
        st.info("Housing & Facilities features coming soon!")

    # User's favorite institutions
    st.markdown("### ⭐ My Favorite Institutions")
    favorites = get_user_favorites()

    if favorites:
        try:
            db = Database()
            fav_institutions = db.execute("""
                SELECT 
                    i.*,
                    CASE 
                        WHEN ufi.id IS NOT NULL THEN true 
                        ELSE false 
                    END as is_favorite
                FROM institutions i
                LEFT JOIN user_favorite_institutions ufi 
                    ON ufi.institution_id = i.unitid 
                    AND ufi.user_id = %s
                WHERE i.unitid = ANY(%s)
            """, (st.session_state.user.id, favorites))

            for inst in fav_institutions:
                with st.container():
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"### {inst['institution_name']}")
                        st.markdown(f"**Location:** {inst['city']}, {inst['state_abbreviation']}")
                        st.markdown(f"**Type:** {inst['control_of_institution']}")

                        if inst['typical_housing_charge']:
                            st.markdown(f"**Housing Cost:** ${inst['typical_housing_charge']:,.2f}/year")

                    with col2:
                        if st.button("❤️", key=f"fav_{inst['unitid']}"):
                            toggle_favorite(inst['unitid'])

                    st.markdown("---")
        except Exception as e:
            logger.error(f"Error rendering favorites: {str(e)}")
            st.error("Failed to load favorite institutions.")
    else:
        st.info("You haven't added any institutions to your favorites yet.")

if __name__ == "__main__":
    render_college_explorer()