# Time-Management
App for time management with active time tracking and scheduling!
## Installation
Download all the python files and requirements.txt in one folder wherever you would like. main.py is the main script to run. Make sure to install all requirements with:
```
pip install -r requirements.txt
```
## Usage
Run the file whenever you finish an activity to log it.
### Tracking
The tracking component allows you to actively track your activities throughout the day. It will show you your tracking time as well as your schedule for the day if there is one. It will assume the first activity of the day to start at 00:00 since it has no way to know. This can be changed with "Edit table" below. Buttons are as follows:
- New activity (click to add an activity and input the name of it)
- Edit table (click to edit the table and change any times/activity names)
- Delete Activity (click to delete an activity and input its number)
- End tracking (ends tracking for the day - only click this when you're finished tracking for the day or going to sleep)
- Switching can switch to the other parts of the app
### Scheduling
The scheduling component works similarly to the tracking component, but allows you to create a schedule in advance that you can compare your tracking to. It will open by allowing you to choose a date to schedule for (tomorrow's date by default). All buttons are the same as the tracking component except that there is no End tracking button.
### Analytics
The analytics component allows you to retrieve past sessions, view the percentages of time for each activity, view totals for activities done multiple times, and export data to comma-separated-values format (.csv). Buttons are as follows:
- Export (export current or all schedules or tracking data you have by choosing an export location)
- Retrieve session (retrieve old session tracking data and schedule by choosing a date)
- Switching can switch to other parts of the app
