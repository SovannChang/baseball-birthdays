#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import random


# In[2]:


def pull_date(url):
    # Pull the table from the page
    table = pd.DataFrame(pd.read_html(url)[0])
    
    # Dropping and renaming columns, replacing null values with 0
    table = table.drop(columns=["Rk", "From", "To", "H.1", "HR.1", "BB.1"]).rename(columns={"Yrs": "Years", "G": "G_bat", "G.1": "G_pit"}).fillna(0)
    
    # Changing data types from float to integer
    table = table.astype({"R": "int", "H": "int", "HR": "int", "RBI": "int", "SB": "int", "BB": "int", "OPS+": "int", "W": "int", "L": "int", "G_pit": "int", "GS": "int", "SV": "int", "SO": "int"})
    
    # Converting innings pitched from .1 .2 to .33 .67
    table["IP"] = table["IP"].astype(int) + table["IP"] * 10 % 5 / 3
    
    return table


# In[3]:


month_lengths = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
month_folders = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


for i in range(12):
    folder = month_folders[i]
    for j in range(month_lengths[i]):     
        day = pull_date(f"https://www.baseball-reference.com/friv/birthdays.cgi?month={i+1}&day={j+1}")
        day.to_csv(f"Data/{folder}/{folder}_{str(j+1).zfill(2)}.csv", index=False)
        
        # Keep requests under 20 per minute (https://www.sports-reference.com/429.html)
        time.sleep(random.uniform(3.5, 5))

