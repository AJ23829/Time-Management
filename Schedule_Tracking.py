import sys
import os
import tkinter as tk
import pandas as pd
import sqlite3
import re
from datetime import datetime, timedelta
from Schedule_Table import bare_table, get_data

class tracking(bare_table):
    def __init__(self, master, df, schedule_df, current_day, id_seed, error,
                 scheduling=False):
        super().__init__(master, df, schedule_df, current_day)
        self.id = id_seed
        self.scheduling = scheduling
        self.tracking_ended = False
        self.state = 3 if scheduling else 1
        self.create_menu_tracking()
        if error:
            self.edit_mode = True
            tk.Label(self.master, text='Session for today already ended').pack()
        else:
            #Creating left margin and creating current day label
            tk.Label(self.master, text='       ').grid(row=1, column=0)
            tk.Label(
                self.master, text=self.current_day, 
                font=('Helvetica',12,'italic','bold')).grid(row=0, column=1)
            if len(schedule_df.index):
                tk.Label(self.master, text='       ').grid(row=1, column=15)
                tk.Label(
                    self.master, text="Schedule", 
                    font=('Helvetica',12,'italic','bold')).grid(row=0, column=15)
                self.Table(scheduling=True, start_col=16)
            self.Table()
    #End tracking
    def end_tracking(self):
        if not self.edit_mode:
            #Create an are you sure window
            self.edit_mode = True
            new_window = tk.Toplevel(self.master)
            text = f"Do you really want to end tracking? \n\
                You cannot start another session on {self.current_day}."
            yes_command = new_window.destroy
            no_command = lambda: (new_window.destroy(),
                                    self.set_edit_mode(False))
            self.are_you_sure(new_window, text, yes_command, no_command)
            self.tracking_ended = self.edit_mode
        
    #Creates the menu
    def create_menu_tracking(self):
        record = lambda: self.ask_tracking(
                "Name of Finished Activity?","Confirm Activity",self.add_entry)
        delete = lambda: self.ask_tracking(
                "Enter number (#) to delete","Confirm",self.delete_entry)
        menu = tk.Menu(self.master)
        menu.add_command(label="Quit! (Esc)", command=self.quitting)
        menu.add_command(label="New activity (Alt+N)", command=record)
        self.master.bind('<Alt-n>', lambda event: record())
        menu.add_command(
            label="Edit table (Alt+E)", command=self.to_edit_mode)
        self.master.bind('<Alt-e>', lambda event: self.to_edit_mode())
        menu.add_command(
            label="Delete Activity (Alt+D)",
            command=delete)
        self.master.bind('<Alt-d>', lambda event: delete())
        if not self.scheduling:
            menu.add_command(
                label="End tracking (Alt+T)", command=self.end_tracking)
            self.master.bind('<Alt-t>', lambda event: self.end_tracking())
        self.load_switching(menu)
        self.master.config(menu=menu)

    #Creates new entry and confirm button for a prompt
    def ask_tracking(self, prompt_text, button_text, button_function):
        if not self.edit_mode:
            new_column = 2*self.num_cols + 3
            prompt = tk.Label(self.master, text=prompt_text)
            prompt.grid(row=1, column=new_column)
            e = tk.Entry(self.master, width=20)
            e.grid(row=2, column=new_column)
            self.set_edit_mode(True)
            conf_func = lambda: button_function(prompt, e, confirm)
            confirm = tk.Button(
                self.master, text=button_text, width=15, command=conf_func)
            confirm.bind("<Return>", lambda event: conf_func())
            confirm.grid(row=3, column=new_column)
            self.master.update()
    
    #Creates a confirmation window
    def are_you_sure(self, new_window, text, yes_command, no_command):
        tk.Label(
            new_window, 
            text=text
            ).pack()
        tk.Button(
            new_window,
            text='yes',
            command=yes_command
            ).pack(side='left', fill='x', expand='yes')
        tk.Button(
            new_window,
            text='no',
            command=no_command
            ).pack(side='right', fill='x', expand='yes')
        new_window.transient(self.master)
        new_window.grab_set()
        self.master.wait_window(new_window)

    #Destroys the entry and button, updating the table
    def add_entry(self, prompt, entry, button):
        #Get the entry text and destroy the prompt, entry, and button
        entry_text = entry.get()
        self.Destroy(prompt, entry, button)
        self.set_edit_mode(False)
        current_time = datetime.now().strftime("%H:%M")
        #Reading start time as string and finding elapsed time
        if self.num_rows > 0:
            start_time = self.df.iloc[self.num_rows - 1, 2]
        else:
            start_time = '00:00'
        #If scheduling, default current_time to 30 minutes after start time
        if self.scheduling:
            current_time = (datetime.strptime(start_time, "%H:%M")
                          + timedelta(minutes=30)).strftime("%H:%M")
        elapsed_time = datetime.strptime(current_time, "%H:%M")\
                     - datetime.strptime(start_time, "%H:%M")
        elapsed_time_min = int(elapsed_time.total_seconds() // 60) % 1440
        #Update the dataframe and num_rows before regenerating table
        self.num_rows += 1
        self.id += 1
        newrow = pd.DataFrame(
            [[entry_text, start_time, current_time, elapsed_time_min, 
            self.id]],
            columns=self.df.columns)
        self.df = pd.concat([self.df,newrow]).reset_index(drop=True)
        #Destroy all current entries and remake them
        self.Table()
        self.master.update()

    #Delete entry
    def delete_entry(self, prompt, entry, button):
        #Get the entry text and destroy the prompt, entry, and button
        entry_text = entry.get()
        self.Destroy(prompt, entry, button)
        try:
            #Only continue if the row is present
            del_row = int(entry_text) - 1
            if del_row not in self.df.index:
                raise ValueError
            #Verify deleting the row
            new_window = tk.Toplevel(self.master)
            yes_command = new_window.destroy
            no_command = lambda: (
                new_window.destroy(), self.set_edit_mode(False))
            text = f'Do you really want to delete activity {entry_text}?'
            self.are_you_sure(new_window, text, yes_command, no_command)
            self.master.update()
            #If user hit yes, delete the row
            if self.edit_mode:
                self.df = self.df[
                            self.df.index != del_row].reset_index(drop=True)
                self.num_rows -= 1
                #Verify that time spent is equal to the elapsed time
                for row in range(self.num_rows):
                    if row > 0:
                        self.df.iloc[row,1] = self.df.iloc[row - 1, 2]
                    elapsed_time = \
                        datetime.strptime(self.df.iloc[row,2], "%H:%M")\
                        - datetime.strptime(self.df.iloc[row,1], "%H:%M")
                    self.df.iloc[row,3] = int(elapsed_time.total_seconds() // 60) % 1440
                self.set_edit_mode(False)
                self.Table()
            self.master.update()
        #If input is invalid show the error message
        except ValueError:
            del_fail_msg = tk.Label(
                self.master, text="Please enter one of the rows")
            del_fail_msg.grid(row=1, column=2*self.num_cols + 3)
            OK_func = lambda: (self.Destroy(del_fail_msg, OK_button), 
                                 self.set_edit_mode(False))
            OK_button = tk.Button(self.master, text="Ok", command=OK_func)
            OK_button.bind("<Return>", lambda event: OK_func())
            OK_button.grid(row=2, column=2*self.num_cols + 3)


    #Convert into edit mode
    def to_edit_mode(self):
        if not self.edit_mode:
            self.set_edit_mode(True)
            self.Table(end_edit_mode = self.end_edit_mode)
    
    #Convert back into normal display
    def end_edit_mode(self, button, warning):
        #Get all text from the entries
        entries_text = [[
            ("0" if len(self.value_entries[col][row].get().strip()) == 4 and
            col in (2,3) else "") + self.value_entries[col][row].get().strip()  
                for col in range(len(self.value_entries)) 
                if 0 < col < self.num_cols] + [
                    self.df['Time Spent (min)'][row], self.df['ID'][row]
                    ] for row in range(len(self.value_entries[0]))]
        #Re-make the dataframe and the GUI table
        df = pd.DataFrame(entries_text,columns=self.df.columns)
        #Check to make sure all edit entries are in time format
        for col in (1,2):
            break_loop = False
            for value in df.iloc[:,col]:
                if not re.match(
                      "^([0-1][0-9]|2[0-3]):[0-5][0-9]$", value):
                    break_loop = True
                    break
            if break_loop:
                new_window = tk.Toplevel(self.master)
                tk.Label(new_window, 
                    text="Times not properly entered in HH:MM format.").pack()
                tk.Button(
                    new_window, text="Ok", command=new_window.destroy).pack()
                new_window.transient(self.master)
                new_window.grab_set()
                self.master.wait_window(new_window)
                break
        else:
            #Destroy the button
            self.Destroy(button,warning)            
            self.set_edit_mode(False)
            self.df = df
            #Verify that time spent is equal to the elapsed time
            for row in range(self.num_rows):
                if row > 0:
                    self.df.iloc[row,1] = self.df.iloc[row - 1, 2]
                elapsed_time = \
                    datetime.strptime(self.df.iloc[row,2], "%H:%M")\
                    - datetime.strptime(self.df.iloc[row,1], "%H:%M")
                self.df.iloc[row,3] = int(elapsed_time.total_seconds() // 60) % 1440 
            self.Table()
            self.master.update()

def postprocessing(app, table, path):
    #Create connection
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    #And a date column full of the date
    app.df.insert(0, 'Date', app.current_day)
    #If we read in the df (didn't create an empty df)
    #Delete all entries with the current date (they will be overwritten)
    with connection:
        cursor.execute(
            f'DELETE FROM {table} WHERE Date=?', (app.current_day,))
    connection.commit()
    #Rename columns to the SQLite database column names
    #And export to the dataframe
    app.df.columns = ['Date', 'Activity', 'Start', 'End', 'Elapsed', 'ID']
    if not app.scheduling:
        #Create a new finished column full of False
        app.df['Finished'] = False
        #If the user ended tracking, make the bottom value for Finished True
        if app.tracking_ended:
            app.df.iloc[-1,-1] = True
    app.df.to_sql(f'{table}', con=connection, if_exists='append', index=False)
    connection.close()

def main_tracking(path):
    #Get day, path
    current_day = datetime.now().strftime(r"%m/%d/%Y")
    #Get the data required for the tracking app
    df, id_seed, error, schedule_df, current_day = get_data(current_day, path)
    #Create the application and mainloop
    root = tk.Tk()
    app = tracking(root, df, schedule_df, current_day, id_seed, error)
    root.mainloop()
    if not error:
        postprocessing(app, "schedule", path)
    return (app.quitted, app.state)
if __name__ == '__main__':
    path = os.path.join(sys.path[0], "Schedule.db")
    main_tracking(path)