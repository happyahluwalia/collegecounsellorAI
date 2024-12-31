import streamlit as st
from models.user import User
from utils.error_handling import handle_error, DatabaseError, ValidationError
import logging

logger = logging.getLogger(__name__) # Assuming logger is configured elsewhere

@handle_error
def render_profile():
    """Render the user profile form with error handling"""
    st.subheader("My Profile")

    if not hasattr(st.session_state, 'user'):
        raise ValidationError("Please log in to access your profile")

    user = st.session_state.user
    try:
        profile = user.get_profile()
        logger.info(f"Retrieved profile for user {user.id}")
    except DatabaseError as e:
        logger.error(f"Failed to retrieve profile for user {user.id}: {str(e)}")
        st.error("Unable to load profile data. Please try again later.")
        return

    with st.form("profile_form"):
        try:
            gpa = st.number_input("GPA", 
                                min_value=0.0, 
                                max_value=4.0, 
                                value=float(profile['gpa']) if profile and profile['gpa'] else 0.0)

            interests = st.multiselect(
                "Academic Interests",
                options=[
                    "Computer Science", "Engineering", "Business", "Arts", 
                    "Humanities", "Social Sciences", "Natural Sciences", 
                    "Medicine", "Law"
                ],
                default=profile['interests'] if profile and profile['interests'] else []
            )

            activities = st.text_area(
                "Extracurricular Activities",
                value='\n'.join(profile['activities']) if profile and profile['activities'] else "",
                help="Enter each activity on a new line"
            )

            target_majors = st.multiselect(
                "Target Majors",
                options=[
                    "Computer Science", "Business Administration", "Engineering",
                    "Psychology", "Biology", "Economics", "English", "History",
                    "Mathematics", "Physics", "Chemistry", "Political Science"
                ],
                default=profile['target_majors'] if profile and profile['target_majors'] else []
            )

            target_schools = st.text_area(
                "Target Schools",
                value='\n'.join(profile['target_schools']) if profile and profile['target_schools'] else "",
                help="Enter each school on a new line"
            )

            if st.form_submit_button("Save Profile"):
                try:
                    user.update_profile(
                        gpa=gpa,
                        interests=interests,
                        activities=activities.split('\n') if activities else [],
                        target_majors=target_majors,
                        target_schools=target_schools.split('\n') if target_schools else []
                    )
                    st.success("✅ Profile updated successfully!")
                    logger.info(f"Profile updated for user {user.id}")
                except DatabaseError as e:
                    logger.error(f"Failed to update profile for user {user.id}: {str(e)}")
                    st.error("😕 Failed to save profile. Please try again later.")

        except Exception as e:
            logger.error(f"Error rendering profile form: {str(e)}")
            st.error("Something went wrong displaying the profile form. Please refresh the page.")