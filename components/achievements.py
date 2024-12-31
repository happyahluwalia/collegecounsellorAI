import streamlit as st
from models.achievement import Achievement
from utils.error_handling import handle_error, DatabaseError
import logging

logger = logging.getLogger(__name__)

@handle_error
def render_achievements():
    """Render the achievements panel showing user progress."""
    if not hasattr(st.session_state, 'user'):
        return

    try:
        user_achievements = Achievement.get_user_achievements(st.session_state.user.id)
        total_points = sum(ach['points'] for ach in user_achievements if ach['completed'])
        
        st.subheader("🏆 Achievements")
        st.write(f"Total Points: {total_points}")
        
        # Progress Overview
        completed = sum(1 for ach in user_achievements if ach['completed'])
        total = len(user_achievements)
        progress = (completed / total) * 100 if total > 0 else 0
        st.progress(progress / 100, f"Overall Progress: {progress:.1f}%")
        
        # Achievement Categories
        categories = set(ach['category'] for ach in user_achievements)
        for category in sorted(categories):
            with st.expander(f"📋 {category.title()}"):
                category_achievements = [
                    ach for ach in user_achievements if ach['category'] == category
                ]
                
                for achievement in category_achievements:
                    col1, col2 = st.columns([0.1, 0.9])
                    with col1:
                        st.write(achievement['icon_name'])
                    with col2:
                        if achievement['completed']:
                            st.markdown(f"✅ **{achievement['name']}** - {achievement['points']} pts")
                        else:
                            st.markdown(f"⭕ **{achievement['name']}**")
                        st.caption(achievement['description'])
                        
                        if achievement['completed']:
                            st.caption(f"Completed on: {achievement['completed_at'].strftime('%Y-%m-%d')}")
                        
                    st.divider()
                    
        logger.info(f"Rendered achievements for user {st.session_state.user.id}")
    except DatabaseError as e:
        logger.error(f"Error rendering achievements: {str(e)}")
        st.error("Unable to load achievements. Please try again later.")
