import streamlit as st
import pandas as pd
import time
import datetime
import random
import matplotlib.pyplot as plt
import altair as alt
import statistics

st.set_page_config(
    page_title="MLB - Major League Birthdays",
    layout="wide",  # Use "wide" to expand the content to fill more of the screen
)

@st.cache_data
def load_data():
    month_lengths = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    jan, feb, mar, apr, may, jun, jul, aug, sep, octo, nov, dec = [[], [], [], [], [], [], [], [],[], [], [], []]
    all_data = [jan, feb, mar, apr, may, jun, jul, aug, sep, octo, nov, dec]

    for i in range(12):
        for j in range(month_lengths[i]):
            all_data[i].append(pd.read_csv(f"Data/{month_names[i]}/{month_names[i]}_{str(j+1).zfill(2)}.csv"))

    return all_data

# Adds innings pitched data by converting the "outs" format to decimals, then back to outs
# @param ip_list - list of innings pitched to sum
# return - returns the sum of the innings in "outs" format
def sum_ip(ip_list):
    sum = 0
    for ip in ip_list:
        sum = sum + int(ip) + (ip % 1) * 10/3
    
    if sum % 1 < .995 and sum % 1 > 0.05:
        return int(sum) + (sum % 1 * 3 / 10)
    else:
        return sum

# Calculates each day's total or average of the parameter statistic and returns values in list form
# @param all_data - list of lists containing dataframes for each day
# @param stat_totals - string representing name of statistic
# @param stat_list - list of totals or averages - overwritten each time to reduce memory strain
# @param is_avg - boolean value representing whether the function should calculate totals (False) or average (True)
# @param war_min - float representing the minimum WAR for the "Players Over _ WAR" calculation. Optional because not used for any other calculation
# @return - lists representing the totals or averages for each day for the input statistic
def calculate_total_or_avg_stats(all_data, stat_name, stat_list, is_avg, war_min=0):
    month_lengths = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    stat_list = []

    for i in range(12):
        for j in range(month_lengths[i]):
            if is_avg:
                # All rate statistics need to have a weighted average
                if stat_name == "BA":
                    stat_list.append(all_data[i][j]["H"].sum() / all_data[i][j]["AB"].sum())

                elif stat_name == "OBP":
                    est_pa = (all_data[i][j]["AB"] + all_data[i][j]["BB"]).sum()
                    est_times_ob = ((all_data[i][j]["AB"] + all_data[i][j]["BB"]) * all_data[i][j]["OBP"]).sum()
                    stat_list.append(est_times_ob / est_pa)

                elif stat_name == "SLG":
                    total_bases = (all_data[i][j]["AB"] * all_data[i][j]["SLG"]).sum()
                    stat_list.append(total_bases / all_data[i][j]["AB"].sum())

                elif stat_name == "OPS":
                    est_pa = (all_data[i][j]["AB"] + all_data[i][j]["BB"]).sum()
                    est_ob_plus_tb = ((all_data[i][j]["AB"] + all_data[i][j]["BB"]) * all_data[i][j]["OPS"]).sum()
                    stat_list.append(est_ob_plus_tb / est_pa)

                elif stat_name == "ERA":
                    stat_list.append(((all_data[i][j]["IP"] * all_data[i][j]["ERA"]).sum()) / all_data[i][j]["IP"].sum())

                elif stat_name == "ERA+":
                    stat_list.append(((all_data[i][j]["IP"] * all_data[i][j]["ERA+"]).sum()) / all_data[i][j]["IP"].sum())
                
                elif stat_name == "WHIP":
                    stat_list.append(((all_data[i][j]["IP"] * all_data[i][j]["WHIP"]).sum()) / all_data[i][j]["IP"].sum())
                
                else:
                    stat_list.append(statistics.mean(all_data[i][j][stat_name]))
                    
            else:
                if stat_name == "Number of Players":
                    stat_list.append(len(all_data[i][j]))
                elif stat_name == "Players Over _ WAR":
                    stat_list.append(len(all_data[i][j][all_data[i][j]["WAR"] > war_min]))
                elif stat_name == "IP":
                    stat_list.append(sum_ip(all_data[i][j]["IP"]))
                else:
                    # No rate stats or weird addition, totals are basic sum
                    stat_list.append(all_data[i][j][stat_name].sum())
                

    return stat_list

# Takes an int representing the day of the year and translates it into the month and day
# @param day_of_year - int representing a number of days into the year
# @return - a tuple containing the month and the day of the month
def get_month_and_day(day_of_year):
    day = day_of_year + 1 # Adjust for 0-indexed
    month_lengths = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    for i in range(12):
        if day <= month_lengths[i]:
            return (i, day)
        else:
            day = day - month_lengths[i]

# Returns a list of the 5 players born closest to the input date
# @param all_data - list of lists containing dataframes for each day
# @param date - datetime.date value representing the target day
# return - a list of lists, with each sublist representing a player and containing name, WAR, and birthdate
def find_5_closest_players(all_data, date):
    closest = []
    younger_than_all = False

    # If the selected date is within 18 years of the current date, set to 18 years (give or take a day b/c leap years) before today, and set to only go backwards
    # Saves calculation time
    # Assumes no players younger than 18
    if date.today() - date < datetime.timedelta(days = 365 * 18 + 4):
        younger_than_all = True
        date = date - datetime.timedelta(days = 365 * 18 + 4)

    day = date.day
    month = date.month
    year = date.year

    day_results = search_day(all_data, day, month, year)
    if len(day_results.index) != 0:
        for i in range(len(day_results)):
            closest.append([day_results.loc[i, "Name"], day_results.loc[i, "WAR"], datetime.date(year, month, day)])

    # Setup for the loop
    next_day = [day, month, year]
    prev_day = [day, month, year]

    # Loop through days getting progressively farther away from the birthday until 5 players found
    while len(closest) < 5:
        if not younger_than_all:
            next_day = add_day(next_day[0], next_day[1], next_day[2])
            nextday_results = search_day(all_data, next_day[0], next_day[1], next_day[2])
            if len(nextday_results.index) != 0:
                for i in range(len(nextday_results)):
                    closest.append([nextday_results.loc[i, "Name"], nextday_results.loc[i, "WAR"], datetime.date(next_day[2], next_day[1], next_day[0])])

        prev_day = subtract_day(prev_day[0], prev_day[1], prev_day[2])
        prevday_results = search_day(all_data, prev_day[0], prev_day[1], prev_day[2])
        if len(prevday_results.index) != 0:
            for i in range(len(prevday_results)):
                closest.append([prevday_results.loc[i, "Name"], prevday_results.loc[i, "WAR"], datetime.date(prev_day[2], prev_day[1], prev_day[0])])

    return closest

# Returns all players born on the parameter day, month, and year. Empty DF if none
# @param all_data - list of lists containing dataframes for each day
# @param day - a number representing the day to search for
# @param month - a number representing the month to search for
# @param year - the year to search for
# return - a dataframe containing all players born on the parameter day, month, and year, or empty if none were
def search_day(all_data, day, month, year):
    birthday_df = all_data[month-1][day-1]
    return birthday_df[birthday_df["Born"] == year].reset_index()

# Returns the day, month, and year of the date following the input date
# @param day - the day
# @param month - the month
# @param year - the year
# return - the day, month, and year of the date following the input date
def add_day(day, month, year):
    month_lengths = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if day == 28 and month == 2 and year % 4 != 0:
        # February 28 on a non-leap year is the end of the month
        return [1, 3, year]
    elif day < month_lengths[month-1]:
        return [day + 1, month, year]
    else:
        if month < 12:
            return [1, month + 1, year]
        else:
            return [1, 1, year + 1]
        
# Returns the day, month, and year of the date before the input date
# @param day - the day
# @param month - the month
# @param year - the year
# return - the day, month, and year of the date before the input date
def subtract_day(day, month, year):
    month_lengths = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if day == 1 and month == 3 and year % 4 != 0:
        # February 28 on a non-leap year is the end of the month
        return [28, 2, year]
    elif day > 1:
        return [day - 1, month, year]
    else:
        if month > 1:
            return [month_lengths[month-2], month-1, year]
        else:
            return [31, 12, year - 1]

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------


st.title("MLB - Major League Birthdays")

st.write("Note: this page looks best when used in a window that is not full screen, but feel free to adjust the size to your liking.")

st.subheader("Table of Contents")
st.write("1. Individual Day Data - Select a birthday and view  players who were born on that day, plus some adjustable graphs")
st.write("2. Group Statistics - Compare statistics across birthdays, with each day's players' statistics aggregated")

all_data = load_data()

with st.expander("Individual Day Data"):

    # --------------------------------------------------------------------------------------------------------------------------------------------------------------
    st.subheader("Birthday Selection")

    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    bday = st.date_input("Choose birthday here", max_value=datetime.date(2024, 12, 31), min_value=datetime.date(1900, 1, 1), format="MM/DD/YYYY")

    selected_month = month_names[bday.month - 1]

    bday_df = all_data[bday.month-1][bday.day-1]

    # --------------------------------------------------------------------------------------------------------------------------------------------------------------
    st.subheader("Player Table")

    st.write("Career statistics of all players born on ", selected_month, str(bday.day))
    st.write("Sortable - default is by birth year")
    st.write("Players with \"HOF\" next to their name are in the Hall of Fame")

    # Creating a copy to display the IP column with standard baseball notation without altering the underlying data
    # Standard baseball notation has 1/3 of an inning as .1 and 2/3 of an inning as .2
    bday_df_copy = bday_df.copy()
    bday_df_copy["IP"] = bday_df_copy["IP"].apply(lambda x: int(x) + (x % 1 * 3 / 10) if x % 1 != 0 else int(x))

    st.dataframe(bday_df_copy, column_config={
        "Born": st.column_config.TextColumn(), 
        "From": st.column_config.TextColumn(), 
        "To": st.column_config.TextColumn()})

    # --------------------------------------------------------------------------------------------------------------------------------------------------------------
    st.subheader("Figures")

    # Dictionary to convert human-friendly stat names to column names
    stat_dict = {
        "Number of Players": "Number of Players",
        "WAR" : "WAR",
        "Players Over _ WAR": "Players Over _ WAR",
        "All Star Games" : "ASG",
        "Games Played (Batted)" : "G_bat",
        "Games Played (Pitched)" : "G_pit",
        "AB" : "AB",
        "H" : "H",
        "HR" : "HR",
        "RBI" : "RBI",
        "SB" : "SB",
        "AVG" : "BA",
        "OBP*" : "OBP",
        "SLG" : "SLG",
        "OPS*" : "OPS",
        "IP" : "IP",
        "Pitching Wins" : "W",
        "Pitching Losses" : "L",
        "ERA" : "ERA",
        "ERA+": "ERA+",
        "WHIP" : "WHIP",
        "Saves" : "SV",
        "K" : "SO"
    }

    stat_scatterplot = st.selectbox(f"Statistic for {selected_month} {str(bday.day)} player scatterplot",
                        ("WAR", "All Star Games", "Games Played (Batted)", "Games Played (Pitched)", "AB", "H", "HR", "RBI", "SB", "IP", "Pitching Wins", "Pitching Losses", "Saves", "K"))

    st.write("Hover over data point for details")

    stat_chart = (
        alt.Chart(bday_df).mark_circle().encode(x=stat_dict[stat_scatterplot], y=alt.Y("Born", scale=alt.Scale(domain=[1830, bday_df["Born"].max()+5]), axis=alt.Axis(format="d")), tooltip=["Name", "Seasons", stat_dict[stat_scatterplot], "Born"])
    )

    # Vertical line at 0 - originally meant to separate +WAR players from -WAR players
    zero_line = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="black", strokeWidth=0.75).encode(
        x=alt.X("x:Q", axis=alt.Axis(title=f"Career {stat_dict[stat_scatterplot]}"))
    )

    st.altair_chart(stat_chart + zero_line)

    # --------------------------------------------------------------------------------------------------------------------------------------------------------------
    st.subheader("Bonus - Closest Player to Your Age")
    st.text(f"Which players were born closest to {selected_month} {str(bday.day)}, {str(bday.year)}?")
    closest_5 = find_5_closest_players(all_data, bday)
    for i in range(len(closest_5)):
        days_apart = (closest_5[i][2] - bday).days

        day_s = "days"

        if abs(days_apart) == 1:
             day_s = "day"

        if days_apart == 0:
            st.text(f"{i+1}.   {closest_5[i][0]}:    born {closest_5[i][2]}     ({closest_5[i][1]} WAR)      -      you are the exact same age!")

        else:
            if days_apart > 0:
                old_young = "older"
            else:
                old_young = "younger"
            st.text(f"{i+1}.   {closest_5[i][0]}:    born {closest_5[i][2]}     ({closest_5[i][1]} WAR)      -      you are {abs(days_apart)} {day_s} {old_young}")


    # --------------------------------------------------------------------------------------------------------------------------------------------------------------
    show_franchises = st.checkbox("Show franchise player counts (not recommended for mobile)")

    if show_franchises:

        st.write(f"Number of players born on {selected_month} {str(bday.day)} to play for each franchise")
        
        player_count_dict = {}

        franchises_col_string = ','.join(bday_df_copy["Franchises"])
        
        for team in str.split(franchises_col_string, sep=","):
            player_count_dict[team] = player_count_dict.get(team, 0) + 1

        team_logos = [
            ["BAL.png", "BOS.png", "NYY.png", "TB.png", "TOR.png"],
            ["CHW.png", "CLE.png", "DET.png", "KC.png", "MIN.png"],
            ["HOU.png", "LAA.png", "OAK.png", "SEA.png", "TEX.png"],
            ["ATL.png", "MIA.png", "NYM.png", "PHI.png", "WAS.png"],
            ["CHC.png", "CIN.png", "MIL.png", "PIT.png", "STL.png"],
            ["ARI.png", "COL.png", "LAD.png", "SD.png", "SF.png"]
        ]

        team_player_count = [
            [player_count_dict.get("BAL", 0), player_count_dict.get("BOS", 0), player_count_dict.get("NYY", 0), player_count_dict.get("TBD", 0), player_count_dict.get("TOR", 0)],
            [player_count_dict.get("CHW", 0), player_count_dict.get("CLE", 0), player_count_dict.get("DET", 0), player_count_dict.get("KCR", 0), player_count_dict.get("MIN", 0)],
            [player_count_dict.get("HOU", 0), player_count_dict.get("ANA", 0), player_count_dict.get("OAK", 0), player_count_dict.get("SEA", 0), player_count_dict.get("TEX", 0)],
            [player_count_dict.get("ATL", 0), player_count_dict.get("FLA", 0), player_count_dict.get("NYM", 0), player_count_dict.get("PHI", 0), player_count_dict.get("WSN", 0)],
            [player_count_dict.get("CHC", 0), player_count_dict.get("CIN", 0), player_count_dict.get("MIL", 0), player_count_dict.get("PIT", 0), player_count_dict.get("STL", 0)],
            [player_count_dict.get("ARI", 0), player_count_dict.get("COL", 0), player_count_dict.get("LAD", 0), player_count_dict.get("SDP", 0), player_count_dict.get("SFG", 0)]
        ]

        for i in range(11):
            if i % 2 == 1:
                st.markdown(
                    """
                    <hr style="width: 85%; height: 1px; background-color: lightgrey; border: none; margin: 0 auto">
                    """, 
                    unsafe_allow_html=True)
                
            else:
                with st.container():
                    cols = st.columns(11)
                    for j in range(11):
                        with cols[j]:
                            if j % 2 == 1:
                                st.image(f"Logos/{team_logos[i // 2][j // 2]}")
                                st.markdown(f"<div style='text-align:center; font-weight:bold;'>{team_player_count[i // 2][j // 2]}</div>", unsafe_allow_html=True)
                                st.write("\n")
                        

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

with st.expander("Group Statistics"):
    st.subheader("Birthday Aggregated Graphs")

    # Totals

    stat_total = st.selectbox("Statistic for Totals graph",
                        ("WAR", "Number of Players", "Players Over _ WAR", "All Star Games", "Games Played (Batted)", "Games Played (Pitched)", "AB", "H", "HR", "RBI", "SB", "IP", "Pitching Wins", "Pitching Losses", "Saves", "K"))
    
    if stat_total == "Players Over _ WAR":
        war_min = st.number_input("Minimum WAR", min_value=-10.0, max_value=200.0, value=0.0, step=0.5, format="%0.1f")
    else:
        war_min = 0

    # Initializing lists
    totals = []
    avgs = []

    stat_totals = calculate_total_or_avg_stats(all_data, stat_dict[stat_total], totals, False, war_min)

    plt.figure(figsize=(10, 3))
    plt.xticks([0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335], labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.xlabel("Birthday")
    plt.ylabel(f"Total {stat_total}")
    plt.title(f"Total {stat_total} For Each Birthday")
    plt.plot(stat_totals)

    st.pyplot(plt.gcf())

    stat_totals_l_to_h = sorted(stat_totals)
    stat_totals_h_to_l = sorted(stat_totals, reverse=True)

    st.write(f"**Top 5 birthdays by total {stat_total} (with top 3 contributors):**")

    # Variable to keep track of previous index to avoid duplicates
    idx = -1

    for i in range(0, 5):
        if i > 0 and stat_totals_h_to_l[i] == stat_totals_h_to_l[i-1] :
            # If 2+ birthdays share a stat, ensure no duplicate date retrieval
            idx = stat_totals.index(stat_totals_h_to_l[i], idx+1)
        else:
            # Current birthday stat is different from previous stat
            idx = stat_totals.index(stat_totals_h_to_l[i])

        m, d = get_month_and_day(idx)
        st.text(f"{i+1}.  {month_names[m]} {d}    --    {f'{stat_totals_h_to_l[i]:.1f}'.rstrip('0').rstrip('.')}")

        if stat_total != "Number of Players" and stat_total != "Players Over _ WAR":
            top_daily_players = all_data[m][d-1].sort_values(stat_dict[stat_total], ascending=False).reset_index(drop=True)
            top_daily_stats = list(top_daily_players.loc[0:3, stat_dict[stat_total]])

            if stat_total == "IP":
                top_daily_ip = [int(x) + (x % 1 * 3 / 10) if x % 1 != 0 else int(x) for x in top_daily_stats]
                st.caption(f"""{top_daily_players.loc[0, 'Name']} ({top_daily_ip[0]}), 
                           {top_daily_players.loc[1, 'Name']} ({top_daily_ip[1]}), 
                           {top_daily_players.loc[2, 'Name']} ({top_daily_ip[2]})""")
            else:
                st.caption(f"""{top_daily_players.loc[0, 'Name']} ({top_daily_stats[0]}), 
                           {top_daily_players.loc[1, 'Name']} ({top_daily_stats[1]}), 
                           {top_daily_players.loc[2, 'Name']} ({top_daily_stats[2]})""")
                   
    st.text("\n")
    st.write(f"**Bottom 5 birthdays by total {stat_total} (with top 3 contributors):**")

    # Variable to keep track of previous index to avoid duplicates 
    idx = -1

    for i in range(0, 5):
        if i > 0 and stat_totals_l_to_h[i] == stat_totals_l_to_h[i-1] :
            # If 2+ birthdays share a stat, ensure no duplicate date retrieval
            idx = stat_totals.index(stat_totals_l_to_h[i], idx+1)
        else:
            # Current birthday stat is different from previous stat
            idx = stat_totals.index(stat_totals_l_to_h[i])

        m, d = get_month_and_day(idx)
        st.text(f"{i+1}.  {month_names[m]} {d}    --    {f'{stat_totals_l_to_h[i]:.1f}'.rstrip('0').rstrip('.')}")

        if stat_total != "Number of Players" and stat_total != "Players Over _ WAR":
            top_daily_players = all_data[m][d-1].sort_values(stat_dict[stat_total], ascending=False).reset_index(drop=True)
            top_daily_stats = list(top_daily_players.loc[0:3, stat_dict[stat_total]])

            if stat_total == "IP":
                top_daily_ip = [int(x) + (x % 1 * 3 / 10) if x % 1 != 0 else int(x) for x in top_daily_stats]
                st.caption(f"""{top_daily_players.loc[0, 'Name']} ({top_daily_ip[0]}), 
                           {top_daily_players.loc[1, 'Name']} ({top_daily_ip[1]}), 
                           {top_daily_players.loc[2, 'Name']} ({top_daily_ip[2]})""")
            else:
                st.caption(f"""{top_daily_players.loc[0, 'Name']} ({top_daily_stats[0]}), 
                           {top_daily_players.loc[1, 'Name']} ({top_daily_stats[1]}), 
                           {top_daily_players.loc[2, 'Name']} ({top_daily_stats[2]})""")


    st.text("\n")
    st.text("\n")
    # Averages

    stat_avg = st.selectbox("Statistic for Averages graph",
                        ("WAR", "All Star Games", "Games Played (Batted)", "Games Played (Pitched)", "AB", "H", "HR", "RBI", "SB", "AVG", "OBP*", "SLG", "OPS*", "IP", "Pitching Wins", "Pitching Losses", "ERA", "ERA+", "WHIP", "Saves", "K"))
    st.write("\* Due to lack of a Plate Appearances stat in the data, aggregated OBP and OPS are estimated based on a rough calculation of PA as AB + BB. This excludes HBP, IBB, and sacrifices, but should be close enough to the correct numbers on a large scale.")

    stat_avgs = calculate_total_or_avg_stats(all_data, stat_dict[stat_avg], avgs, True)

    plt.figure(figsize=(10, 3))
    plt.xticks([0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335], labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.xlabel("Birthday")
    plt.ylabel(f"Average {stat_avg}")
    plt.title(f"Average {stat_avg} For Each Birthday")
    plt.plot(stat_avgs)

    st.pyplot(plt.gcf())
    


    stat_avgs_l_to_h = sorted(stat_avgs)
    stat_avgs_h_to_l = sorted(stat_avgs, reverse=True)

    if stat_avg in ["ERA", "WHIP"]:
        good = stat_avgs_l_to_h
        bad = stat_avgs_h_to_l
    else:
        good = stat_avgs_h_to_l
        bad = stat_avgs_l_to_h


    st.write(f"**Top 5 birthdays by average {stat_avg}:**")

    # Variable to keep track of previous index to avoid duplicates 
    idx = -1

    for i in range(0, 5):
        if i > 0 and good[i] == good[i-1] :
            # If 2+ birthdays share a stat, ensure no duplicate date retrieval
            idx = stat_avgs.index(good[i], idx+1)
        else:
            # Current birthday stat is different from previous stat
            idx = stat_avgs.index(good[i])

        m, d = get_month_and_day(idx)
        st.text(f"{i+1}.  {month_names[m]} {d}    --    {good[i]:.3f}")

    
    st.text("\n")
    st.write(f"**Bottom 5 birthdays by average {stat_avg}:**")

    # Variable to keep track of previous index to avoid duplicates 
    idx = -1

    for i in range(0, 5):
        if i > 0 and bad[i] == bad[i-1] :
            # If 2+ birthdays share a stat, ensure no duplicate date retrieval
            idx = stat_avgs.index(bad[i], idx+1)
        else:
            # Current birthday stat is different from previous stat
            idx = stat_avgs.index(bad[i])

        m, d = get_month_and_day(idx)
        st.text(f"{i+1}.  {month_names[m]} {d}    --    {bad[i]:.3f}")
