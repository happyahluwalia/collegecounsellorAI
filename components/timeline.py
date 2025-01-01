import streamlit as st
from datetime import datetime, timedelta
import plotly.figure_factory as ff
import pandas as pd
from models.database import Database
from utils.error_handling import handle_error, DatabaseError
import logging
import json
import traceback

logger = logging.getLogger(__name__)

def show_error_message(error_message, error_trace=None):
    """Display an error message with expandable details."""
    st.error(error_message)
    if error_trace:
        with st.expander("Show Error Details"):
            st.code(error_trace)

@handle_error
def render_timeline():
    """Render the application timeline and deadline tracker."""
    if not hasattr(st.session_state, 'user'):
        st.warning("Please log in to view your application timeline.")
        return

    st.title("📅 Application Timeline")

    # Create tabs for different timeline views
    tab1, tab2 = st.tabs(["Timeline View", "Manage Deadlines"])

    with tab1:
        render_timeline_view()

    with tab2:
        manage_deadlines()

def render_timeline_view():
    """Render the visual timeline of applications and milestones."""
    try:
        db = Database()
        
        # Fetch deadlines and milestones
        deadlines = db.execute("""
            SELECT college_name, deadline_type, deadline_date, status
            FROM application_deadlines
            WHERE user_id = %s
            ORDER BY deadline_date
        """, (st.session_state.user.id,))

        milestones = db.execute("""
            SELECT title, description, due_date, category, status
            FROM timeline_milestones
            WHERE user_id = %s
            ORDER BY due_date
        """, (st.session_state.user.id,))

        if not deadlines and not milestones:
            st.info("No deadlines or milestones added yet. Start by adding some in the 'Manage Deadlines' tab!")
            return

        # Prepare data for timeline visualization
        timeline_data = []
        colors = []

        for deadline in deadlines:
            timeline_data.append(dict(
                Task=f"📌 {deadline['college_name']} ({deadline['deadline_type']})",
                Start=deadline['deadline_date'],
                Finish=deadline['deadline_date'],
                Status=deadline['status']
            ))
            colors.append('rgb(255, 100, 100)' if deadline['status'] == 'pending' else 'rgb(100, 255, 100)')

        for milestone in milestones:
            timeline_data.append(dict(
                Task=f"🎯 {milestone['title']}",
                Start=milestone['due_date'],
                Finish=milestone['due_date'],
                Status=milestone['status']
            ))
            colors.append('rgb(100, 100, 255)' if milestone['status'] == 'pending' else 'rgb(100, 255, 100)')

        if timeline_data:
            df = pd.DataFrame(timeline_data)
            
            # Create Gantt chart
            fig = ff.create_gantt(
                df,
                colors=colors,
                index_col='Status',
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True,
                showgrid_y=True
            )
            
            # Update layout
            fig.update_layout(
                title='Application Timeline',
                xaxis_title='Date',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # Show upcoming deadlines
            st.subheader("📅 Upcoming Deadlines")
            upcoming = sorted(
                [d for d in timeline_data if d['Status'] == 'pending'],
                key=lambda x: x['Start']
            )[:5]

            for item in upcoming:
                days_left = (item['Start'] - datetime.now().date()).days
                status_color = "🔴" if days_left <= 7 else "🟡" if days_left <= 14 else "🟢"
                
                st.markdown(f"""
                    {status_color} **{item['Task']}**  
                    Due: {item['Start'].strftime('%B %d, %Y')} ({days_left} days left)
                """)

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error rendering timeline view: {str(e)}\n{error_trace}")
        show_error_message("Unable to display timeline.", error_trace)

def manage_deadlines():
    """Interface for managing application deadlines and milestones."""
    try:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Add Application Deadline")
            with st.form("add_deadline"):
                college_name = st.text_input("College Name")
                deadline_type = st.selectbox(
                    "Deadline Type",
                    ["Early Decision", "Early Action", "Regular Decision", "Rolling", "Transfer"]
                )
                deadline_date = st.date_input("Deadline Date")
                requirements = st.text_area("Requirements/Notes")

                if st.form_submit_button("Add Deadline"):
                    try:
                        db = Database()
                        db.execute("""
                            INSERT INTO application_deadlines 
                            (user_id, college_name, deadline_type, deadline_date, requirements)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            st.session_state.user.id,
                            college_name,
                            deadline_type,
                            deadline_date,
                            json.dumps({"notes": requirements})
                        ))
                        st.success("Deadline added successfully!")
                        
                        # Add automatic reminder
                        reminder_date = deadline_date - timedelta(days=7)
                        db.execute("""
                            INSERT INTO deadline_reminders 
                            (user_id, deadline_id, reminder_date, reminder_type)
                            VALUES (
                                %s,
                                (SELECT id FROM application_deadlines WHERE user_id = %s 
                                 AND college_name = %s AND deadline_type = %s),
                                %s,
                                'one_week'
                            )
                        """, (
                            st.session_state.user.id,
                            st.session_state.user.id,
                            college_name,
                            deadline_type,
                            reminder_date
                        ))

                    except Exception as e:
                        error_trace = traceback.format_exc()
                        logger.error(f"Error adding deadline: {str(e)}\n{error_trace}")
                        show_error_message("Failed to add deadline.", error_trace)

        with col2:
            st.subheader("Add Milestone")
            with st.form("add_milestone"):
                title = st.text_input("Milestone Title")
                description = st.text_area("Description")
                category = st.selectbox(
                    "Category",
                    ["Essay", "Recommendation", "Test Score", "Financial Aid", "Other"]
                )
                priority = st.select_slider(
                    "Priority",
                    options=["Low", "Medium", "High"]
                )
                due_date = st.date_input("Due Date")

                if st.form_submit_button("Add Milestone"):
                    try:
                        db = Database()
                        db.execute("""
                            INSERT INTO timeline_milestones 
                            (user_id, title, description, category, priority, due_date)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            st.session_state.user.id,
                            title,
                            description,
                            category,
                            priority.lower(),
                            due_date
                        ))
                        st.success("Milestone added successfully!")
                    except Exception as e:
                        error_trace = traceback.format_exc()
                        logger.error(f"Error adding milestone: {str(e)}\n{error_trace}")
                        show_error_message("Failed to add milestone.", error_trace)

        # Display existing deadlines and milestones with status updates
        st.subheader("Manage Existing Items")
        existing_items = st.tabs(["Application Deadlines", "Milestones"])

        with existing_items[0]:
            display_existing_deadlines()

        with existing_items[1]:
            display_existing_milestones()

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in deadline management: {str(e)}\n{error_trace}")
        show_error_message("Something went wrong while managing deadlines.", error_trace)

def display_existing_deadlines():
    """Display and manage existing application deadlines."""
    try:
        db = Database()
        deadlines = db.execute("""
            SELECT id, college_name, deadline_type, deadline_date, status, requirements
            FROM application_deadlines
            WHERE user_id = %s
            ORDER BY deadline_date
        """, (st.session_state.user.id,))

        for deadline in deadlines:
            with st.expander(f"{deadline['college_name']} - {deadline['deadline_type']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"Due: {deadline['deadline_date'].strftime('%B %d, %Y')}")
                    st.write(f"Status: {deadline['status'].title()}")
                    requirements = deadline['requirements']
                    # Handle both string and dict cases
                    if isinstance(requirements, str):
                        try:
                            requirements = json.loads(requirements)
                        except json.JSONDecodeError:
                            requirements = {"notes": requirements}
                    if requirements.get('notes'):
                        st.write("Notes:", requirements['notes'])

                with col2:
                    new_status = st.selectbox(
                        "Update Status",
                        ["pending", "in_progress", "completed"],
                        key=f"deadline_status_{deadline['id']}",
                        index=["pending", "in_progress", "completed"].index(deadline['status'])
                    )
                    if new_status != deadline['status']:
                        db.execute("""
                            UPDATE application_deadlines
                            SET status = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s AND user_id = %s
                        """, (new_status, deadline['id'], st.session_state.user.id))
                        st.success("Status updated!")
                        st.rerun()

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error displaying deadlines: {str(e)}\n{error_trace}")
        show_error_message("Unable to display deadlines.", error_trace)

def display_existing_milestones():
    """Display and manage existing milestones."""
    try:
        db = Database()
        milestones = db.execute("""
            SELECT id, title, description, category, priority, due_date, status
            FROM timeline_milestones
            WHERE user_id = %s
            ORDER BY due_date
        """, (st.session_state.user.id,))

        for milestone in milestones:
            with st.expander(f"{milestone['title']} ({milestone['category']})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"Due: {milestone['due_date'].strftime('%B %d, %Y')}")
                    st.write(f"Priority: {milestone['priority'].title()}")
                    st.write(f"Status: {milestone['status'].title()}")
                    if milestone['description']:
                        st.write("Description:", milestone['description'])
                
                with col2:
                    new_status = st.selectbox(
                        "Update Status",
                        ["pending", "in_progress", "completed"],
                        key=f"milestone_status_{milestone['id']}",
                        index=["pending", "in_progress", "completed"].index(milestone['status'])
                    )
                    if new_status != milestone['status']:
                        db.execute("""
                            UPDATE timeline_milestones
                            SET status = %s, updated_at = CURRENT_TIMESTAMP,
                                completion_date = CASE 
                                    WHEN %s = 'completed' THEN CURRENT_TIMESTAMP
                                    ELSE NULL
                                END
                            WHERE id = %s AND user_id = %s
                        """, (new_status, new_status, milestone['id'], st.session_state.user.id))
                        st.success("Status updated!")
                        st.rerun()

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error displaying milestones: {str(e)}\n{error_trace}")
        show_error_message("Unable to display milestones.", error_trace)