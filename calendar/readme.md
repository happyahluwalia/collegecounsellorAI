You are an AI assistant tasked with building a calendar-based application for students to manage their 4-year plans and important deadlines. The key features the application should have are:

1. Calendar Interface (High Priority):
   - The main view should be a calendar that displays the student's 4-year plan, with each item represented as an event or task.
   - The calendar should have clear visual cues to differentiate between different categories (e.g., courses, extracurriculars, summer programs) and the student's commitment level (committed vs. stretch goal).
   - Allow the student to easily drag and drop items within the calendar to reschedule or rearrange their plan.

2. Plan vs. Deadlines Toggle (Medium Priority):
   - Provide a clear way for the student to switch between viewing their personalized plan and the external deadlines (college applications, internships, etc.).
   - The deadlines view should be read-only, as these are externally controlled and cannot be modified by the student.
   - However, the student should be able to add reminders or notes to these deadlines within their plan.

3. Versioning and Audit History (Low Priority):
   - Implement a versioning system that automatically tracks changes to the student's plan, including who made the changes and when.
   - Allow the student to easily revert to previous versions of their plan if needed.
   - Provide a clear audit history that the student can review to understand the evolution of their plan over time.

4. Sharing and Printing (Medium Priority):
   - Enable the student to share their plan with trusted advisors, such as parents or counselors, for feedback and guidance.
   - Provide options for the student to print their plan or export it in various formats (e.g., PDF, spreadsheet) for offline use or sharing.

5. Notifications and Reminders (High Priority):
   - Set up a robust notification system that alerts the student about upcoming deadlines, important milestones, and any changes to their plan.
   - Allow the student to customize the notification preferences (e.g., email, push notifications, in-app alerts) to suit their needs.

6. Export and Download (High Priority):
   - Offer the student the ability to download a comprehensive report of their plan, including all the actionable items, deadlines, and progress tracking.
   - This report should be available in various formats (e.g., PDF, CSV) to accommodate the student's preferences and needs.

Based on the requirements, I recommend using the FullCalendar library for Python to build this application. FullCalendar is a well-tested and supported open-source calendar library that provides the necessary features and functionality to meet the requirements outlined above.

Please provide a detailed plan on how you would implement this application using FullCalendar, including the specific steps and technologies you would use.
