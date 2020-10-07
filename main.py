from Schedule_Tracking import main_tracking
from Schedule_Analytics import main_analytics
from Schedule_Scheduling import main_scheduling
import sys
import os
dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)\
        else sys.path[0]
path = os.path.join(dir, "Schedule.db")
functions = (main_tracking, main_analytics, main_scheduling)
quitted, state = (False, 1)
while not quitted:
    quitted, state = functions[state-1](path)