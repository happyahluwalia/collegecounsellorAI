import icalendar
import pytz
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Union
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

def create_calendar_event(deadline: Dict) -> icalendar.Event:
    """Create an iCalendar event from a deadline."""
    event = icalendar.Event()
    
    # Create event
    event.add('summary', f"College Application: {deadline['college_name']} ({deadline['deadline_type']})")
    event.add('dtstart', deadline['deadline_date'])
    
    # End date is end of the day
    end_date = deadline['deadline_date'] + timedelta(days=1)
    event.add('dtend', end_date)
    
    # Add description with requirements if available
    description = f"College Application Deadline\n\n"
    description += f"College: {deadline['college_name']}\n"
    description += f"Type: {deadline['deadline_type']}\n"
    
    if isinstance(deadline['requirements'], dict) and deadline['requirements'].get('notes'):
        description += f"\nNotes: {deadline['requirements']['notes']}"
    
    event.add('description', description)
    
    # Add reminder (1 week before)
    alarm = icalendar.Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('trigger', timedelta(days=-7))
    alarm.add('description', f"Reminder: {deadline['college_name']} application due in 1 week")
    event.add_component(alarm)
    
    return event

def generate_ics_file(deadlines: List[Dict]) -> bytes:
    """Generate an ICS file containing all deadlines."""
    try:
        # Create calendar
        cal = icalendar.Calendar()
        cal.add('prodid', '-//College Compass//collegecompass.app//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        
        # Add timezone
        tz = pytz.timezone('UTC')
        cal.add('x-wr-timezone', tz.zone)
        
        # Add each deadline as an event
        for deadline in deadlines:
            event = create_calendar_event(deadline)
            cal.add_component(event)
        
        return cal.to_ical()
    
    except Exception as e:
        logger.error(f"Error generating calendar file: {str(e)}")
        raise ValueError("Failed to generate calendar file")

def get_calendar_link(cal_bytes: bytes, calendar_type: str) -> str:
    """Generate a calendar link based on the calendar type."""
    try:
        b64_cal = base64.b64encode(cal_bytes).decode('utf-8')
        
        if calendar_type == "google":
            # Google Calendar import link
            return f"https://calendar.google.com/calendar/r/settings/export?data={b64_cal}"
        
        elif calendar_type == "outlook":
            # Outlook Web import link
            return f"https://outlook.live.com/calendar/0/addcalendar?data={b64_cal}"
        
        elif calendar_type == "apple":
            # For Apple Calendar, we'll return the base64 encoded ICS file
            # which can be downloaded and opened in Apple Calendar
            return f"data:text/calendar;base64,{b64_cal}"
        
        else:
            raise ValueError(f"Unsupported calendar type: {calendar_type}")
    
    except Exception as e:
        logger.error(f"Error generating calendar link: {str(e)}")
        raise ValueError("Failed to generate calendar link")
