import streamlit as st
from models.database import Database
from datetime import datetime
import logging
import json
import traceback
from typing import Dict, List
import pandas as pd

logger = logging.getLogger(__name__)

def show_error_message(error_message, error_trace=None):
    """Display an error message with expandable details."""
    st.error(error_message)
    if error_trace:
        with st.expander("Show Error Details"):
            st.code(error_trace)

def initialize_sample_programs():
    """Initialize sample internship programs if none exist."""
    try:
        db = Database()
        count = db.execute_one("SELECT COUNT(*) as count FROM internship_programs")

        if count['count'] == 0:
            sample_programs = [
                {
                    'name': 'California State Summer School for Mathematics and Science (COSMOS)',
                    'organization': 'University of California',
                    'description': 'Four-week summer residential program for students with demonstrated interest in STEM.',
                    'website_url': 'https://cosmos.ucsc.edu/',
                    'program_type': 'Summer Research',
                    'subject_areas': ['Mathematics', 'Science', 'Engineering'],
                    'grade_levels': ['10th Grade', '11th Grade'],
                    'application_deadline': '2025-02-15',
                    'program_duration': '4 weeks',
                    'location_type': 'In-person',
                    'locations': ['UC Davis', 'UC Irvine', 'UC San Diego', 'UC Santa Cruz'],
                    'requirements': {
                        'gpa_minimum': 3.5,
                        'materials': [
                            'Application Form',
                            'Teacher Recommendation',
                            'Transcript',
                            'Personal Statement'
                        ]
                    }
                }
            ]

            for program in sample_programs:
                try:
                    # Convert requirements to JSON, leave arrays as arrays
                    program_data = {
                        'name': program['name'],
                        'organization': program['organization'],
                        'description': program['description'],
                        'website_url': program['website_url'],
                        'program_type': program['program_type'],
                        'subject_areas': program['subject_areas'],  # Keep as array
                        'grade_levels': program['grade_levels'],    # Keep as array
                        'application_deadline': program['application_deadline'],
                        'program_duration': program['program_duration'],
                        'location_type': program['location_type'],
                        'locations': program['locations'],          # Keep as array
                        'requirements': json.dumps(program['requirements'])  # Convert dict to JSON
                    }

                    db.execute("""
                        INSERT INTO internship_programs (
                            name, organization, description, website_url, program_type,
                            subject_areas, grade_levels, application_deadline,
                            program_duration, location_type, locations, requirements
                        ) VALUES (
                            %(name)s, %(organization)s, %(description)s, %(website_url)s,
                            %(program_type)s, %(subject_areas)s, %(grade_levels)s,
                            %(application_deadline)s, %(program_duration)s, %(location_type)s,
                            %(locations)s, %(requirements)s::jsonb
                        )
                    """, program_data)

                except Exception as e:
                    logger.error(f"Error inserting program {program['name']}: {str(e)}")
                    continue

            logger.info("Sample internship programs initialized")

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error initializing sample programs: {str(e)}\n{error_trace}")
        show_error_message("Failed to initialize sample programs", error_trace)

def get_student_interests() -> List[str]:
    """Get student's interests from their profile."""
    try:
        if not hasattr(st.session_state, 'user'):
            return []

        db = Database()
        profile = db.execute_one("""
            SELECT interests, target_majors
            FROM profiles
            WHERE user_id = %s
        """, (st.session_state.user.id,))

        if not profile:
            return []

        interests = set()
        if profile['interests']:
            interests.update(json.loads(profile['interests']))
        if profile['target_majors']:
            interests.update(json.loads(profile['target_majors']))

        return list(interests)
    except Exception as e:
        logger.error(f"Error getting student interests: {str(e)}")
        return []

def render_program_browser(interests: List[str]):
    """Render the program browser with filters."""
    try:
        st.subheader("Available Programs")

        # Define available options
        program_types = [
            "Summer Research", "Leadership Development",
            "Research & Development", "Internship", "Workshop", "Fellowship"
        ]

        subject_areas = [
            "Mathematics", "Science", "Engineering", "Computer Science",
            "Leadership", "Community Service", "Business", "Arts"
        ]

        location_types = ["Remote", "In-person", "Hybrid"]

        # Filter matching interests
        matching_interests = [interest for interest in interests if interest in subject_areas]

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_types = st.multiselect(
                "Program Type",
                program_types,
                placeholder="All Types"
            )

        with col2:
            selected_subjects = st.multiselect(
                "Subject Areas",
                subject_areas,
                default=matching_interests if matching_interests else None,
                placeholder="All Subjects"
            )

        with col3:
            selected_locations = st.multiselect(
                "Location Type",
                location_types,
                placeholder="All Locations"
            )

        # Fetch programs with filters
        db = Database()
        query_params = {}
        conditions = []

        # Build dynamic query conditions
        if selected_types:
            conditions.append("program_type = ANY(%(types)s)")
            query_params['types'] = selected_types

        if selected_subjects:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM unnest(subject_areas) subject
                    WHERE subject = ANY(%(subjects)s)
                )
            """)
            query_params['subjects'] = selected_subjects

        if selected_locations:
            conditions.append("location_type = ANY(%(locations)s)")
            query_params['locations'] = selected_locations

        # Construct final query
        query = """
            SELECT * FROM internship_programs
            {}
            ORDER BY application_deadline;
        """.format(" WHERE " + " AND ".join(conditions) if conditions else "")

        programs = db.execute(query, query_params)

        # Display programs
        for program in programs:
            st.markdown(f"### 📋 {program['name']}")
            st.markdown(f"**Deadline:** {program['application_deadline'].strftime('%B %d, %Y')}")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Organization:** {program['organization']}")
                st.markdown(f"**Description:** {program['description']}")
                st.markdown(f"**Duration:** {program['program_duration']}")
                st.markdown(f"**Location Type:** {program['location_type']}")

                # No need for json.loads since locations is already an array
                locations = program['locations']
                if locations:
                    st.markdown("**Locations:** " + ", ".join(locations))

                requirements = json.loads(program['requirements'])
                st.markdown("---")
                st.markdown("**📝 Requirements:**")
                for key, value in requirements.items():
                    if isinstance(value, list):
                        st.markdown(f"**{key.title()}:**")
                        for item in value:
                            st.markdown(f"- {item}")
                    else:
                        st.markdown(f"**{key.title()}:** {value}")

            with col2:
                # Application status and actions
                status = db.execute_one("""
                    SELECT status, application_date
                    FROM internship_applications
                    WHERE user_id = %s AND program_id = %s
                """, (st.session_state.user.id, program['id']))

                if status:
                    st.info(f"Status: {status['status'].title()}")
                    if status['application_date']:
                        st.write(f"Applied: {status['application_date'].strftime('%B %d, %Y')}")

                # Action buttons with unique keys
                button_key = f"program_interested_{program['id']}"
                if st.button("Mark Interested", key=button_key):
                    try:
                        db.execute("""
                            INSERT INTO internship_applications (user_id, program_id, status)
                            VALUES (%s, %s, 'interested')
                            ON CONFLICT (user_id, program_id)
                            DO UPDATE SET status = 'interested', updated_at = CURRENT_TIMESTAMP
                        """, (st.session_state.user.id, program['id']))
                        st.success("Marked as interested!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update status: {str(e)}")

                st.markdown(f"[Visit Website]({program['website_url']})")

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error rendering program browser: {str(e)}\n{error_trace}")
        show_error_message("Unable to display internship programs.", error_trace)

def render_applications():
    """Render the student's internship applications."""
    try:
        st.subheader("My Applications")

        db = Database()
        applications = db.execute("""
            SELECT 
                ia.id, ia.status, ia.application_date, ia.notes,
                ip.name, ip.organization, ip.application_deadline,
                ip.website_url
            FROM internship_applications ia
            JOIN internship_programs ip ON ia.program_id = ip.id
            WHERE ia.user_id = %s
            ORDER BY ip.application_deadline
        """, (st.session_state.user.id,))

        if not applications:
            st.info("You haven't marked any programs yet. Browse available programs and mark the ones you're interested in!")
            return

        # Group applications by status
        status_order = ['interested', 'in_progress', 'submitted', 'accepted', 'rejected']
        status_colors = {
            'interested': '🤔',
            'in_progress': '📝',
            'submitted': '✉️',
            'accepted': '🎉',
            'rejected': '😔'
        }

        for status in status_order:
            status_apps = [app for app in applications if app['status'] == status]
            if status_apps:
                st.markdown(f"### {status_colors[status]} {status.title()}")

                for app in status_apps:
                    with st.container():
                        st.markdown(f"**{app['name']} - {app['organization']}**")

                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.markdown(f"**Deadline:** {app['application_deadline'].strftime('%B %d, %Y')}")
                            if app['application_date']:
                                st.markdown(f"**Applied:** {app['application_date'].strftime('%B %d, %Y')}")

                            # Notes editor with unique key
                            notes_key = f"app_notes_{app['id']}_{status}"
                            new_notes = st.text_area(
                                "Application Notes",
                                value=app['notes'] or '',
                                key=notes_key
                            )

                            if new_notes != app['notes']:
                                update_key = f"update_notes_{app['id']}_{status}"
                                if st.button("Update Notes", key=update_key):
                                    try:
                                        db.execute("""
                                            UPDATE internship_applications
                                            SET notes = %s, updated_at = CURRENT_TIMESTAMP
                                            WHERE id = %s AND user_id = %s
                                        """, (new_notes, app['id'], st.session_state.user.id))
                                        st.success("Notes updated!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed to update notes: {str(e)}")

                        with col2:
                            # Status updater with unique key
                            status_key = f"app_status_{app['id']}_{status}"
                            new_status = st.selectbox(
                                "Update Status",
                                status_order,
                                index=status_order.index(app['status']),
                                key=status_key
                            )

                            if new_status != app['status']:
                                try:
                                    application_date = None
                                    if new_status == 'submitted':
                                        application_date = datetime.now().date()

                                    db.execute("""
                                        UPDATE internship_applications
                                        SET status = %s,
                                            application_date = COALESCE(%s, application_date),
                                            updated_at = CURRENT_TIMESTAMP
                                        WHERE id = %s AND user_id = %s
                                    """, (new_status, application_date, app['id'], st.session_state.user.id))
                                    st.success("Status updated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to update status: {str(e)}")

                            st.markdown(f"[Visit Website]({app['website_url']})")

                        st.markdown("---")

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error rendering applications: {str(e)}\n{error_trace}")
        show_error_message("Unable to display your applications.", error_trace)

def render_internships():
    """Render the internship programs tracker interface."""
    if not hasattr(st.session_state, 'user'):
        st.warning("Please log in to access the internship tracker.")
        return

    st.title("🎯 Summer Internship Tracker")

    try:
        # Initialize sample programs if needed
        initialize_sample_programs()

        # Get student's interests
        interests = get_student_interests()

        # Create tabs for different views
        tab1, tab2 = st.tabs(["Browse Programs", "My Applications"])

        with tab1:
            render_program_browser(interests)

        with tab2:
            render_applications()

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in internship tracker: {str(e)}\n{error_trace}")
        show_error_message("Something went wrong while loading the internship tracker.", error_trace)

if __name__ == "__main__":
    render_internships()