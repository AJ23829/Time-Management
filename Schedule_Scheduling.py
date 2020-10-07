import sys
import os
import tkinter as tk
from Schedule_Table import get_date, get_data
from Schedule_Tracking import tracking, postprocessing

def main_scheduling(path):
    root = tk.Tk()
    date_obj = get_date(root, "Select Date for Scheduling", True)
    root.mainloop()
    current_day = date_obj.current_day
    empty, id_seed, error, df = get_data(
                                    current_day, path, schedule_only=True)[:-1]
    root = tk.Tk()
    app = tracking(
        root, df, empty, current_day, id_seed, error, scheduling=True)
    root.mainloop()
    postprocessing(app, "scheduling", path)
    return (app.quitted, app.state)

if __name__ == "__main__":
    path = os.path.join(sys.path[0], "Schedule.db")
    main_scheduling(path)