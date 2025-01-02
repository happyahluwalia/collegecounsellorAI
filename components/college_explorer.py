import streamlit as st
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

def search_institutions(search_term: str) -> List[Dict]:
    """Search institutions by name with autocomplete."""
    try:
        db = Database()
        results = db.execute("""
            SELECT DISTINCT institution_name, unitid
            FROM institutions
            WHERE LOWER(institution_name) LIKE LOWER(%s)
            ORDER BY institution_name
            LIMIT 10
        """, (f"%{search_term}%",))
        return results
    except Exception as e:
        logger.error(f"Error searching institutions: {str(e)}")
        return []

def get_institution_details(institution_id: int) -> Optional[Dict]:
    """Get detailed information about a specific institution."""
    try:
        db = Database()
        details = db.execute_one("""
            SELECT i.*,
                CASE WHEN ufi.id IS NOT NULL THEN true ELSE false END as is_favorite
            FROM institutions i
            LEFT JOIN user_favorite_institutions ufi 
                ON ufi.institution_id = i.unitid 
                AND ufi.user_id = %s
            WHERE i.unitid = %s
        """, (st.session_state.user.id, institution_id))
        return details
    except Exception as e:
        logger.error(f"Error fetching institution details: {str(e)}")
        return None

def render_institution_details(institution_id: int):
    """Render detailed view of a specific institution."""
    details = get_institution_details(institution_id)
    if not details:
        st.error("Failed to load institution details.")
        return

    # Back button
    if st.button("← Back to List"):
        st.session_state.selected_institution = None
        st.rerun()

    # Header with favorite button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(details['institution_name'])
    with col2:
        if st.button("❤️" if details['is_favorite'] else "🤍", 
                   key=f"fav_detail_{institution_id}"):
            toggle_favorite(institution_id)

    # Basic Information
    st.subheader("📍 Location & Contact")
    st.markdown(f"""
        - **Address:** {details['city']}, {details['state_abbreviation']} {details['zip']}
        - **Institution Type:** {details['control_of_institution']}
        - **Region:** {details.get('geographic_region', 'Not specified')}
    """)

    # Academic Information
    st.subheader("🎓 Academic Profile")
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Degrees Offered:**")
        if details.get('degree_levels'):
            for degree in json.loads(details['degree_levels']):
                st.markdown(f"- {degree}")
        else:
            st.markdown("- Information not available")

    with cols[1]:
        st.markdown("**Programs & Specializations:**")
        if details.get('program_offerings'):
            for program in json.loads(details['program_offerings']):
                st.markdown(f"- {program}")
        else:
            st.markdown("- Information not available")

    # Costs & Financial Information
    st.subheader("💰 Costs & Financial Aid")
    if details.get('tuition_and_fees') or details.get('typical_housing_charge'):
        cols = st.columns(2)
        with cols[0]:
            if details.get('tuition_and_fees'):
                st.metric("Annual Tuition & Fees", f"${details['tuition_and_fees']:,.2f}")
        with cols[1]:
            if details.get('typical_housing_charge'):
                st.metric("Housing Cost", f"${details['typical_housing_charge']:,.2f}")
    else:
        st.info("Cost information not available")

    # Additional Information
    if details.get('additional_information'):
        st.subheader("ℹ️ Additional Information")
        st.markdown(details['additional_information'])

def render_institutions_list(filters: Dict):
    """Render paginated list of institutions with filters."""
    try:
        # Get page number from session state
        if 'page_number' not in st.session_state:
            st.session_state.page_number = 0

        # Initialize database connection
        db = Database()

        # Build query with filters
        query = """
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
            WHERE 1=1
        """
        params = [st.session_state.user.id]

        # Apply filters
        if filters.get('name'):
            query += " AND LOWER(institution_name) LIKE LOWER(%s)"
            params.append(f"%{filters['name']}%")

        if filters.get('states'):
            query += " AND state_abbreviation = ANY(%s)"
            params.append(filters['states'])

        if filters.get('types'):
            query += " AND control_of_institution = ANY(%s)"
            params.append(filters['types'])

        # Get total count first
        count_query = f"""
            SELECT COUNT(*) as count
            FROM institutions i
            LEFT JOIN user_favorite_institutions ufi 
                ON ufi.institution_id = i.unitid 
                AND ufi.user_id = %s
            WHERE 1=1
            {' AND LOWER(institution_name) LIKE LOWER(%s)' if filters.get('name') else ''}
            {' AND state_abbreviation = ANY(%s)' if filters.get('states') else ''}
            {' AND control_of_institution = ANY(%s)' if filters.get('types') else ''}
        """
        count_result = db.execute_one(count_query, tuple(params))
        total_count = count_result['count'] if count_result else 0

        # Add pagination to main query
        query += " ORDER BY institution_name LIMIT 10 OFFSET %s"
        params.append(st.session_state.page_number * 10)

        # Execute main query
        institutions = db.execute(query, tuple(params))

        if not institutions:
            st.info("No institutions found matching your criteria.")
            return

        # Display institutions
        for inst in institutions:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    if st.button(f"### {inst['institution_name']}", 
                               key=f"select_{inst['unitid']}"):
                        st.session_state.selected_institution = inst['unitid']
                        st.rerun()
                    st.markdown(f"**Location:** {inst['city']}, {inst['state_abbreviation']}")
                    st.markdown(f"**Type:** {inst['control_of_institution']}")

                    if inst['typical_housing_charge']:
                        st.markdown(f"**Housing Cost:** ${inst['typical_housing_charge']:,.2f}/year")

                with col2:
                    if st.button("❤️" if inst['is_favorite'] else "🤍", 
                               key=f"fav_{inst['unitid']}"):
                        toggle_favorite(inst['unitid'])

                st.markdown("---")

        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.session_state.page_number > 0:
                if st.button("← Previous", key="prev_page"):
                    st.session_state.page_number -= 1
                    st.rerun()

        with col2:
            total_pages = (total_count - 1) // 10 + 1
            st.markdown(f"Page {st.session_state.page_number + 1} of {total_pages}")

        with col3:
            if (st.session_state.page_number + 1) * 10 < total_count:
                if st.button("Next →", key="next_page"):
                    st.session_state.page_number += 1
                    st.rerun()

    except Exception as e:
        logger.error(f"Error rendering institutions list: {str(e)}")
        st.error("Failed to load institutions. Please try again.")

def render_college_explorer():
    """Main function to render the college explorer dashboard."""
    st.title("🏛️ College Explorer Dashboard")

    if not hasattr(st.session_state, 'user'):
        st.warning("Please log in to access all features of the College Explorer.")
        return

    # Initialize session states
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    if 'selected_institution' not in st.session_state:
        st.session_state.selected_institution = None

    # If an institution is selected, show its details
    if st.session_state.selected_institution:
        render_institution_details(st.session_state.selected_institution)
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

    # Filters section
    st.subheader("Filter Institutions")

    # Search by name with dynamic suggestions
    name_filter = st.text_input(
        "Search by Institution Name",
        value=st.session_state.search_term,
        placeholder="Enter institution name...",
        key="institution_search"
    )

    # Show suggestions if user is typing
    if name_filter and name_filter != st.session_state.search_term:
        suggestions = search_institutions(name_filter)
        if suggestions:
            st.markdown("### Suggestions:")
            for suggestion in suggestions:
                if st.button(suggestion['institution_name'], 
                           key=f"suggest_{suggestion['unitid']}"):
                    st.session_state.search_term = suggestion['institution_name']
                    st.session_state.page_number = 0
                    st.rerun()

    # Update search term in session state
    if name_filter != st.session_state.search_term:
        st.session_state.search_term = name_filter
        st.session_state.page_number = 0  # Reset pagination when search changes

    # State and type filters
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

    # Combine all filters
    filters = {
        'name': name_filter,
        'states': selected_states if selected_states else None,
        'types': institution_types if institution_types else None
    }

    # Display filtered institutions
    st.subheader("Institutions")
    render_institutions_list(filters)

    # User's favorite institutions
    st.markdown("### ⭐ My Favorite Institutions")
    favorites = get_user_favorites()

    if favorites:
        try:
            db = Database()
            fav_institutions = db.execute("""
                SELECT 
                    i.*,
                    true as is_favorite
                FROM institutions i
                WHERE i.unitid = ANY(%s)
                ORDER BY institution_name
            """, (favorites,))

            for inst in fav_institutions:
                with st.container():
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        if st.button(f"### {inst['institution_name']}", 
                                   key=f"fav_select_{inst['unitid']}"):
                            st.session_state.selected_institution = inst['unitid']
                            st.rerun()
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