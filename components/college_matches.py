import streamlit as st
from agents.counselor import CounselorAgent
from utils.error_handling import handle_error, APIError, DatabaseError
import logging
import json
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

def show_error_message(error_message, error_trace=None):
    """Display an error message with expandable details."""
    st.error(error_message)
    if error_trace:
        with st.expander("Show Error Details"):
            st.code(error_trace)

def show_walkthrough():
    """Display the college match recommendation walkthrough."""
    try:
        st.subheader("🎯 Find Your Best College Matches")

        # Initialize walkthrough state
        if 'walkthrough_step' not in st.session_state:
            st.session_state.walkthrough_step = 0
        if 'walkthrough_data' not in st.session_state:
            st.session_state.walkthrough_data = {}

        # Progress bar
        steps = ["Preferences", "Location", "Campus Life", "Review"]
        progress = st.session_state.walkthrough_step / (len(steps) - 1)
        st.progress(progress, f"Step {st.session_state.walkthrough_step + 1} of {len(steps)}")

        # Step content
        if st.session_state.walkthrough_step == 0:
            st.markdown("### Academic Preferences")
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox(
                    "Preferred Class Size",
                    ["Small (< 20)", "Medium (20-50)", "Large (50+)", "No Preference"],
                    key="class_size"
                )
                st.multiselect(
                    "Preferred Teaching Style",
                    ["Lecture-based", "Discussion-based", "Project-based", "Research-focused"],
                    key="teaching_style"
                )
            with col2:
                st.selectbox(
                    "Campus Setting",
                    ["Urban", "Suburban", "Rural", "No Preference"],
                    key="campus_setting"
                )
                st.multiselect(
                    "Special Programs Interest",
                    ["Honors Program", "Study Abroad", "Internship Programs", "Research Opportunities"],
                    key="special_programs"
                )

        elif st.session_state.walkthrough_step == 1:
            st.markdown("### Location Preferences")
            st.multiselect(
                "Preferred Regions",
                ["Northeast", "Southeast", "Midwest", "Southwest", "West Coast"],
                key="regions"
            )
            st.slider(
                "Maximum Distance from Home (miles)",
                0, 3000, 500,
                key="max_distance"
            )
            st.multiselect(
                "Preferred Climate",
                ["Warm", "Cold", "Moderate", "No Preference"],
                key="climate"
            )

        elif st.session_state.walkthrough_step == 2:
            st.markdown("### Campus Life Preferences")
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox(
                    "Housing Preference",
                    ["On-campus", "Off-campus", "No Preference"],
                    key="housing"
                )
                st.multiselect(
                    "Important Campus Activities",
                    ["Sports", "Arts", "Music", "Theater", "Greek Life", "Cultural Organizations"],
                    key="activities"
                )
            with col2:
                st.selectbox(
                    "Athletics Importance",
                    ["Very Important", "Somewhat Important", "Not Important"],
                    key="athletics"
                )
                st.slider(
                    "Importance of Campus Diversity (1-5)",
                    1, 5, 3,
                    key="diversity"
                )

        else:  # Review step
            st.markdown("### Review Your Preferences")
            if st.session_state.walkthrough_data:
                for category, preferences in st.session_state.walkthrough_data.items():
                    st.markdown(f"**{category}**")
                    if isinstance(preferences, (list, tuple)):
                        for pref in preferences:
                            st.markdown(f"- {pref}")
                    else:
                        st.markdown(f"- {preferences}")

        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.walkthrough_step > 0:
                if st.button("← Previous"):
                    st.session_state.walkthrough_step -= 1
                    st.rerun()

        with col2:
            if st.session_state.walkthrough_step < len(steps) - 1:
                if st.button("Next →"):
                    try:
                        # Save current step data
                        current_step_data = {}
                        if st.session_state.walkthrough_step == 0:
                            current_step_data = {
                                "Class Size": st.session_state.class_size,
                                "Teaching Style": st.session_state.teaching_style,
                                "Campus Setting": st.session_state.campus_setting,
                                "Special Programs": st.session_state.special_programs
                            }
                        elif st.session_state.walkthrough_step == 1:
                            current_step_data = {
                                "Preferred Regions": st.session_state.regions,
                                "Maximum Distance": st.session_state.max_distance,
                                "Climate": st.session_state.climate
                            }
                        elif st.session_state.walkthrough_step == 2:
                            current_step_data = {
                                "Housing": st.session_state.housing,
                                "Campus Activities": st.session_state.activities,
                                "Athletics": st.session_state.athletics,
                                "Diversity Importance": st.session_state.diversity
                            }

                        st.session_state.walkthrough_data.update(current_step_data)
                        st.session_state.walkthrough_step += 1
                        st.rerun()
                    except Exception as e:
                        error_trace = traceback.format_exc()
                        logger.error(f"Error saving walkthrough step data: {str(e)}\n{error_trace}")
                        show_error_message("Error saving your preferences", error_trace)
            elif st.button("Generate Recommendations"):
                try:
                    generate_recommendations(st.session_state.walkthrough_data)
                    st.rerun()
                except Exception as e:
                    error_trace = traceback.format_exc()
                    logger.error(f"Error generating recommendations: {str(e)}\n{error_trace}")
                    show_error_message("Unable to generate recommendations", error_trace)

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in walkthrough: {str(e)}\n{error_trace}")
        show_error_message("Something went wrong in the walkthrough", error_trace)

def generate_recommendations(preferences):
    """Generate college recommendations based on walkthrough preferences."""
    try:
        counselor = CounselorAgent()
        profile = st.session_state.user.get_profile()

        # Combine profile data with walkthrough preferences
        enhanced_profile = {
            **(profile or {}),  # Handle case where profile is None
            "preferences": preferences
        }

        # Generate recommendations
        matches_json = counselor.generate_college_matches(enhanced_profile)
        matches = json.loads(matches_json)  # Convert JSON string to dict

        # Store in database
        db = st.session_state.user.db
        db.execute("""
            INSERT INTO college_matches (user_id, matches)
            VALUES (%s, %s)
        """, (st.session_state.user.id, matches_json))  # Store original JSON string

        logger.info(f"Generated new college matches for user {st.session_state.user.id} with preferences")
        st.session_state.walkthrough_complete = True

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error generating recommendations: {str(e)}\n{error_trace}")
        show_error_message("Unable to generate recommendations", error_trace)

@handle_error
def render_college_matches():
    """Render personalized college recommendations."""
    if not hasattr(st.session_state, 'user'):
        st.warning("Please log in to see personalized college recommendations.")
        return

    st.title("College Matches")

    try:
        profile = st.session_state.user.get_profile()
        if not profile:
            st.warning("Please complete your profile to get personalized college recommendations.")
            return

        db = st.session_state.user.db

        # Show walkthrough or matches
        tab1, tab2 = st.tabs(["College Matches", "Find New Matches"])

        with tab1:
            # Add refresh button
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("Your personalized college matches based on your profile")
            with col2:
                force_refresh = st.button("🔄 Refresh Matches")

            try:
                # Check for cached matches
                cached_record = None if force_refresh else db.execute_one("""
                    SELECT matches, updated_at 
                    FROM college_matches 
                    WHERE user_id = %s 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (st.session_state.user.id,))

                matches = None
                # Generate new matches if needed
                if not cached_record or force_refresh:
                    with st.spinner("Generating personalized college matches..."):
                        counselor = CounselorAgent()
                        matches_json = counselor.generate_college_matches(profile)

                        try:
                            # Parse and validate JSON
                            matches = json.loads(matches_json)
                            if not isinstance(matches, dict) or 'colleges' not in matches:
                                raise ValueError("Invalid matches structure")

                            # Store in database as JSON string
                            db.execute("""
                                INSERT INTO college_matches (user_id, matches)
                                VALUES (%s, %s)
                            """, (st.session_state.user.id, matches_json))

                            logger.info(f"Generated and cached new college matches for user {st.session_state.user.id}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON from counselor: {str(e)}")
                            raise APIError("Error processing college recommendations")
                        except ValueError as e:
                            logger.error(f"Invalid matches structure: {str(e)}")
                            raise APIError("Invalid college recommendations format")
                else:
                    try:
                        # Handle cached matches - could be string or dict
                        cached_matches = cached_record['matches']
                        if isinstance(cached_matches, str):
                            matches = json.loads(cached_matches)
                        elif isinstance(cached_matches, dict):
                            matches = cached_matches
                        else:
                            raise ValueError(f"Unexpected matches type: {type(cached_matches)}")

                        if not isinstance(matches, dict) or 'colleges' not in matches:
                            raise ValueError("Invalid cached matches structure")

                        st.caption(f"Last updated: {cached_record['updated_at'].strftime('%Y-%m-%d %H:%M')}")
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Error loading cached matches: {str(e)}")
                        raise DatabaseError("Error loading cached recommendations")

                # Display college matches
                if matches and 'colleges' in matches:
                    for college in matches['colleges']:
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
                else:
                    st.warning("No college matches found. Try refreshing or generating new matches.")

            except (json.JSONDecodeError, ValueError) as e:
                error_trace = traceback.format_exc()
                logger.error(f"JSON structure error: {str(e)}\n{error_trace}")
                show_error_message("Error processing college matches data", error_trace)
            except APIError as e:
                error_trace = traceback.format_exc()
                logger.error(f"API error: {str(e)}\n{error_trace}")
                show_error_message(str(e), error_trace)
            except DatabaseError as e:
                error_trace = traceback.format_exc()
                logger.error(f"Database error: {str(e)}\n{error_trace}")
                show_error_message(str(e), error_trace)

        with tab2:
            show_walkthrough()

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error in college matches: {str(e)}\n{error_trace}")
        show_error_message("Something went wrong while displaying college matches.", error_trace)

if __name__ == "__main__":
    render_college_matches()