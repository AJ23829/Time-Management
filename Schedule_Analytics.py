import sys
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, date
from Schedule_Table import bare_table, get_data, get_date

class Analytics(bare_table):
    def __init__(self, master, df, schedule_df, current_day, path):
        self.df_current_day = df.copy()
        self.schedule_current_day = schedule_df.copy()
        self.today = current_day
        super().__init__(master, df, schedule_df, current_day)
        self.path = path
        self.state = 2
        self.day_label = []
        self.create_menu_analytics()
        #Creating left margin and creating current day label
        tk.Label(self.master, text='       ').grid(row=1, column=0)
        tk.Label(self.master, text='       ').grid(row=1, column=15)
        tk.Label(
            self.master, text="Schedule", 
            font=('Helvetica',12,'italic','bold')).grid(row=0, column=15)
        self.create_table(df, schedule_df, current_day)
    
    #Export sqlite db to csv if all is true
    #Current dataframe if all is false
    def export(self, all, schedule):
        if not self.edit_mode:
            self.master.filename = filedialog.asksaveasfilename(
                initialdir = os.path.expanduser("~"),
                title = "Select File",
                filetypes = (("csv file", "*.csv"), ("all files", "*.*")))
            if self.master.filename != "":
                self.master.filename += (
                    ".csv" if self.master.filename[-4:] != ".csv" else "")
                if all:
                    table = "scheduling" if schedule else "schedule"
                    connection = sqlite3.connect(self.path)
                    sql_data = pd.read_sql_query(f"SELECT * FROM {table}", connection)
                    connection.close()
                    sql_data.to_csv(self.master.filename, index=False)
                else:
                    df = self.schedule_df if schedule else self.df
                    df[self.current_day] = np.nan
                    df.to_csv(self.master.filename, index=False)

    #Create the menu for analytics
    def create_menu_analytics(self):
        menu = tk.Menu(self.master)
        export_menu = tk.Menu(self.master)
        current_exp_menu = tk.Menu(self.master)
        current_exp_menu.add_command(
            label="tracking data", command=lambda: self.export(False, False))
        current_exp_menu.add_command(
            label="schedule", command=lambda: self.export(False, True))
        all_exp_menu = tk.Menu(self.master)
        all_exp_menu.add_command(
            label="tracking data", command=lambda: self.export(True, False))
        all_exp_menu.add_command(
            label="schedule", command=lambda: self.export(True, True))
        export_menu.add_cascade(label="Export current", menu=current_exp_menu)
        export_menu.add_cascade(label="Export all", menu=all_exp_menu)
        menu.add_command(label="Quit! (Esc)", command=self.quitting)
        menu.add_cascade(label="Export", menu=export_menu)
        menu.add_command(
            label="Retrieve session (Alt+R)", command=self.retrieve)
        self.master.bind('<Alt-r>', lambda event: self.retrieve())
        self.load_switching(menu)
        self.master.config(menu=menu)
    #Preprocessing
    def preprocessing(self, df):
        df.columns = [
            'Activity','Start Time','End Time', 'Time Spent (min)','ID']
        total_time = sum(df['Time Spent (min)'])
        #Add a percentage column
        df['Percentage of day'] = round(
                df['Time Spent (min)'] / total_time * 100, 1)
        df['ID'] = df.pop('ID')
        #Add a row for total time for every activity that has duplicates
        for activity in set(df['Activity']):
            time_spent = df[df['Activity'] == activity]['Time Spent (min)']
            if time_spent.__len__() > 1:
                new_row = pd.DataFrame([[f'*Total time for {activity}*',
                    'N/A', 'N/A', sum(time_spent), round(
                        sum(time_spent) / total_time * 100, 1), -1]],
                    columns=df.columns)
                df = df.append(new_row, ignore_index=True)
        if len(df.index) == 0:
            new_row = pd.DataFrame([['N/A']*6], columns=df.columns)
            df = df.append(new_row)
        return df
    #Create a table given a dataframe and a day
    def create_table(self, df, schedule_df, day):
        #Preprocessing of dataframe
        self.Destroy(self.day_label)
        df = self.preprocessing(df)
        schedule_df = self.preprocessing(schedule_df)
        #Create the table
        self.df = df
        self.schedule_df = schedule_df
        self.num_cols = len(df.columns) - 1
        self.num_rows = df.__len__()
        self.current_day = day
        self.day_label = tk.Label(
            self.master, text=self.current_day, 
            font=('Helvetica',12,'italic','bold'))
        self.day_label.grid(row=0, column=1)
        self.set_edit_mode(False)
        self.Table(scheduling=True, start_col=16)
        self.Table()
        self.master.update()
    #Retrieve a session for a specific date
    def retrieve(self):
        #Get date
        date_obj = get_date(self.master, "Select date to view data")
        view_date = date_obj.current_day
        #Get dataframe for day stated
        connection = sqlite3.connect(self.path)
        df = pd.read_sql_query(
            f'''SELECT Activity, Start, End, Elapsed, ID
            FROM schedule WHERE Date = "{view_date}"''', connection)
        schedule_df = pd.read_sql_query(
            f'''SELECT Activity, Start, End, Elapsed, ID
            FROM scheduling WHERE Date = "{view_date}"''', connection)
        connection.close()
        if not df.__len__():
            warning_msg = tk.Label(
                self.master, text=f'No schedule for {view_date} found.')
            warning_msg.grid(row=1, column=2*self.num_cols + 3)
            button = tk.Button(
                self.master, text='Ok', command=lambda: (
                    self.set_edit_mode(False), button.destroy(), 
                    warning_msg.destroy()))
            button.grid(row=2, column=2*self.num_cols + 3)
            self.master.update()
        else:
            self.create_table(df, schedule_df, view_date)

def main_analytics(path):
    #Get day, path
    current_day = datetime.now().strftime(r"%m/%d/%Y")
    #Get the data required for the tracking app
    result = get_data(current_day, path, use_finished=False)
    df, schedule_df, current_day = (result[0], result[3], result[4])
    #Create the application and mainloop
    root = tk.Tk()
    app = Analytics(root, df, schedule_df, current_day, path)
    root.mainloop()
    return (app.quitted, app.state)

if __name__ == '__main__':
    path = os.path.join(sys.path[0], "Schedule.db")
    main_analytics(path)