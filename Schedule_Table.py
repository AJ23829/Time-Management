import tkinter as tk
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from tkcalendar import Calendar, DateEntry

class get_date():
    def __init__(self, root, prompt, use_root=False):
        self.current_day = datetime.now() + timedelta(days=1)
        date_kw = {'year': self.current_day.year, 
                'month': self.current_day.month, 'day': self.current_day.day}
        self.current_day = self.current_day.strftime(r"%m/%d/%Y")
        self.win = root if use_root else tk.Toplevel(root)
        tk.Label(self.win, text=prompt)
        self.cal = Calendar(self.win,
                    font="Arial 14", selectmode='day',
                    cursor="hand1", **date_kw)
        self.cal.pack(fill="both", expand=True)
        tk.Button(self.win, text="Select Highlighted Date",
                command=self.get_current_day).pack()
        tk.Button(self.win, text="Use Today's Date",
                command=lambda: self.get_current_day(current=True))
        if not use_root:
            self.win.transient(root)
            self.win.grab_set()
            root.wait_window(self.win)

    def get_current_day(self, current=False):
        if current:
            self.current_day = datetime.now().strftime(r"%m/%d/%Y")
        else:
            date = str(self.cal.selection_get()).split('-')
            self.current_day = f'{date[1]}/{date[2]}/{date[0]}'
        self.win.destroy()

class bare_table():
    def __init__(self, master, df, schedule_df, current_day):
        self.master = master
        self.df = df
        self.schedule_df = schedule_df
        self.num_cols = len(df.columns) - 1
        self.num_rows = df.__len__()
        self.current_day = current_day
        self.schedule_entries = []
        self.value_entries = []
        self.edit_mode = False
        self.quitted = True
        self.state = 0
        self.master.bind('<Escape>', self.quitting)
        self.master.state("zoomed")
    #Quit
    def quitting(self, *args):
        self.master.quit()
    
    def load_switching(self, menu):
        if self.state != 1:
            menu.add_command(
                label="Switch to Tracking (Alt+T)",
                command=lambda: self.switch(1))
            self.master.bind('<Alt-t>', lambda event: self.switch(1))
        if self.state != 2:
            menu.add_command(
                label="Switch to Analytics (Alt+A)",
                command=lambda: self.switch(2))
            self.master.bind('<Alt-a>', lambda event: self.switch(2))
        if self.state != 3:
            menu.add_command(
                label="Switch to Scheduling (Alt+S)",
                command=lambda: self.switch(3))
            self.master.bind('<Alt-s>', lambda event: self.switch(3))

    def switch(self, state):
        self.state = state
        self.quitted = False
        self.master.quit()
        self.master.destroy()
    #Set edit_mode to whatever is input (meant to be boolean)
    def set_edit_mode(self, edit_mode_to):
        self.edit_mode = edit_mode_to

    #Destroy all objects in args (args can be a nested list too)
    def Destroy(self, *args):
        for thing in args:
            if type(thing) == list:
                self.Destroy(*thing)
            else:
                thing.destroy()

    #Creates the Table structure from the dataframe
    def Table(self, scheduling=False, start_col=1, 
              end_edit_mode=lambda confirm, warning: None):
        if scheduling:
            self.schedule_df, self.df = self.df, self.schedule_df
            self.num_cols = len(self.df.columns) - 1
            self.num_rows = self.df.__len__()
            self.schedule_entries, self.value_entries = (self.value_entries,
                                                    self.schedule_entries)
        self.Destroy(self.value_entries)
        #Multi-dimensional list to store the entries
        #(so they can be destroyed later)
        value_entries_num = []
        for row in range(self.num_rows):
            value_entry = tk.Label(
                self.master, text=(self.df.index[row] + 1), font=('Helvetica',8)
                )
            value_entries_num.append(value_entry)
            value_entry.grid(row=row + 2, column=start_col)
            tk.Label(self.master, text='     ').grid(
                row=1, column=start_col + 1)
        self.value_entries = [value_entries_num]
        for col in range(self.num_cols):
            #Creating column labels and spacing
            tk.Label(
                self.master, text=self.df.columns[col], 
                font=('Helvetica',9,'italic')).grid(
                    row=1, column=2*col + 2 + start_col)
            tk.Label(self.master, text='     ').grid(
                row=1, column=2*col + 3 + start_col)
            #Creating table entries
            value_entries_col = []
            for row in range(self.num_rows):
                value_entry = tk.Entry(self.master)
                value_entry.grid(row=row + 2, column=2*col + 2 + start_col)
                value_entry.insert(0, self.df.iloc[row,col])
                #If not in edit mode or the column is left most,
                #then entry will be converted to label.
                if not self.edit_mode or col == self.num_cols - 1:
                    text = value_entry.get()
                    value_entry.destroy()
                    value_entry = tk.Label(
                        self.master, text=text, font=('Helvetica',8))
                    value_entry.grid(row=row + 2, column=2*col + 2 + start_col)
                value_entries_col.append(value_entry)
            self.value_entries.append(value_entries_col)
        if scheduling:
            self.schedule_df, self.df = self.df, self.schedule_df
            self.num_cols = len(self.df.columns) - 1
            self.num_rows = self.df.__len__()
            self.schedule_entries, self.value_entries = (self.value_entries,
                                                    self.schedule_entries)
        #If in edit mode, it will add a confirm button
        if self.edit_mode:
            warning = tk.Label(
                self.master, 
                text=("Make sure all times are in format HH:MM\n"
                      "(like 09:10) or it will not continue"))
            warning.grid(row=1, column=2*self.num_cols + 2 + start_col)
            conf_func = lambda: end_edit_mode(confirm, warning)
            confirm = tk.Button(
                self.master, text="Confirm Edits", width=15, command=conf_func)
            confirm.bind("<Return>", lambda event: conf_func())
            confirm.grid(row=2, column=2*self.num_cols + 2 + start_col)

def get_data(current_day, path, use_finished=True, schedule_only=False):
    #Create connection
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    if schedule_only:
        cursor.execute(
            'SELECT ID FROM schedule ORDER BY ID DESC LIMIT 1')
        result = cursor.fetchall()
        id_seed = result[0][0] if len(result) else 0
        df, error = (pd.DataFrame(),False)
    else:
        #Create SQL Table if not there
        with connection:
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS schedule (
                    Date TEXT, Activity TEXT, Start TEXT, End TEXT, 
                    Elapsed INTEGER, ID INTEGER, Finished INTEGER)'''
                    )
        connection.commit()
        #Select most recent date, id, and if it finished the session
        cursor.execute(
            '''SELECT Date, ID, Finished FROM schedule
            ORDER BY ID DESC LIMIT 1''')
        result = cursor.fetchall()
        #If there's no result, initialize the variables
        date, id_seed, finished = result[0] \
            if len(result) != 0 else (0, 0, 2)
        error = False
        #If starting a new session, make empty df
        if (finished == 2) or (finished and use_finished):
            df = pd.DataFrame(
                [],columns=[
                'Activity','Start Time','End Time','Time Spent (min)','ID'])
            if date == current_day:
                error = True
        #Otherwise read the df for the current session and rename columns
        else:
            current_day = date
            df = pd.read_sql_query(
                f'''SELECT Activity, Start, End, Elapsed, ID
                FROM schedule WHERE Date = "{current_day}"''', connection)
            df.columns = [
                'Activity','Start Time','End Time', 'Time Spent (min)','ID']
    #Find schedule for today
    #Create SQL Table if not there
    with connection:
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS scheduling (
                Date TEXT, Activity TEXT, Start TEXT, End TEXT, 
                Elapsed INTEGER, ID INTEGER)'''
                )
    connection.commit()
    schedule_df = pd.read_sql_query(
        f'''SELECT Activity, Start, End, Elapsed, ID
        FROM scheduling WHERE Date = "{current_day}"''', connection)
    schedule_df.columns = [
        'Activity','Start Time','End Time', 'Time Spent (min)','ID']
    connection.close()
    return (df, id_seed, error, schedule_df, current_day)