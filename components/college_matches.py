import streamlit as st
from agents.counselor import CounselorAgent
from utils.error_handling import handle_error, APIError, DatabaseError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@handle_error
def render_college_matches():
    """Render personalized college recommendations."""
    if not hasattr(st.session_state, 'user'):
        st.warning("Please log in to see personalized college recommendations.")
        return

    st.subheader("🎓 College Matches")

    try:
        profile = st.session_state.user.get_profile()
        if not profile:
            st.warning("Please complete your profile to get personalized college recommendations.")
            return

        db = st.session_state.user.db

        # Add refresh button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Your personalized college matches based on your profile")
        with col2:
            force_refresh = st.button("🔄 Refresh Matches")

        # Check for cached matches
        cached_matches = None if force_refresh else db.execute_one("""
            SELECT matches, updated_at 
            FROM college_matches 
            WHERE user_id = %s 
            ORDER BY updated_at DESC 
            LIMIT 1
        """, (st.session_state.user.id,))

        # Generate new matches if needed
        if not cached_matches or force_refresh:
            with st.spinner("Generating personalized college matches..."):
                counselor = CounselorAgent()
                matches = counselor.generate_college_matches(profile)

                # Cache the new matches
                db.execute("""
                    INSERT INTO college_matches (user_id, matches)
                    VALUES (%s, %s)
                """, (st.session_state.user.id, matches))

                logger.info(f"Generated and cached new college matches for user {st.session_state.user.id}")
        else:
            matches = cached_matches['matches']
            st.caption(f"Last updated: {cached_matches['updated_at'].strftime('%Y-%m-%d %H:%M')}")

        # Display college matches
        for college in matches.get('colleges', []):
            with st.expander(f"📚 {college['name']} - Match Score: {college['match_score']:.0%}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Why it's a good fit")
                    st.write(college['why_good_fit'])

                    st.markdown("### Program Strengths")
                    for strength in college['program_strengths']:
                        st.markdown(f"- {strength}")

                with col2:
                    st.markdown("### Academic Fit")
                    st.write(college['academic_fit'])

                    st.markdown("### Admission Stats")
                    stats = college['admission_stats']
                    st.metric("Acceptance Rate", f"{stats['acceptance_rate']:.1%}")
                    st.write(f"GPA Range: {stats['gpa_range']['min']:.1f} - {stats['gpa_range']['max']:.1f}")

                    st.markdown("### Extracurricular Matches")
                    for match in college['extracurricular_matches']:
                        st.markdown(f"- {match}")

        logger.info(f"Displayed college matches for user {st.session_state.user.id}")

    except APIError as e:
        logger.error(f"API error while generating college matches: {str(e)}")
        st.error("😕 Unable to generate college matches at the moment. Please try again later.")
    except DatabaseError as e:
        logger.error(f"Database error while handling college matches: {str(e)}")
        st.error("Unable to retrieve college matches. Please try again later.")
    except Exception as e:
        logger.error(f"Error displaying college matches: {str(e)}")
        st.error("Something went wrong while displaying college matches.")

if __name__ == "__main__":
    render_college_matches()