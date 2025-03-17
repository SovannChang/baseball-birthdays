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
    
    print(sum % 1)
    if sum % 1 < .995 and sum % 1 > 0.05:
        return int(sum) + (sum % 1 * 3 / 10)
    else:
        return sum

# Calculates each day's total or average of the parameter statistic and returns values in list form
# @param all_data - list of lists containing dataframes for each day
# @param stat_totals - string representing name of statistic
# @param stat_list - list of totals or averages - overwritten each time to reduce memory strain
# @param is_avg - boolean value representing whether the function should calculate totals (False) or average (True)
# @return - lists representing the totals or averages for each day for the input statistic
def calculate_total_or_avg_stats(all_data, stat_name, stat_list, is_avg):
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
            return (i+1, day)
        else:
            day = day - month_lengths[i]


st.title("MLB - Major League Birthdays")

st.write("Note: this page looks best when used in a window that is not full screen, but feel free to adjust the size to your liking.")

st.subheader("Table of Contents")
st.write("1. Individual Day Data - Select a birthday and view  players who were born on that day, plus some visualizations of various data about them")
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
    st.write("WAR by birth year for players born on ", selected_month, str(bday.day))
    st.write("Hover over data point for details")

    war_chart = (
        alt.Chart(bday_df).mark_circle().encode(x="WAR", y=alt.Y("Born", scale=alt.Scale(domain=[1830, bday_df["Born"].max()+5]), axis=alt.Axis(format="d")), tooltip=["Name", "Seasons", "WAR", "Born"])
    )

    # Vertical line at 0 WAR to separate +WAR players from -WAR players
    zero_line = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="black", strokeWidth=0.75).encode(
        x=alt.X("x:Q", axis=alt.Axis(title="Career WAR"))
    )

    st.altair_chart(war_chart + zero_line)

    # --------------------------------------------------------------------------------------------------------------------------------------------------------------
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

    # Dictionary to convert human-friendly stat names to column names
    stat_dict = {
        "Number of Players": "Number of Players",
        "WAR" : "WAR",
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

    # Totals

    stat_total = st.selectbox("Statistic for Totals graph",
                        ("WAR", "Number of Players", "Games Played (Batted)", "Games Played (Pitched)", "AB", "H", "HR", "RBI", "SB", "IP", "Pitching Wins", "Pitching Losses", "Saves", "K"))

    # Initializing lists
    totals = []
    avgs = []

    stat_totals = calculate_total_or_avg_stats(all_data, stat_dict[stat_total], totals, False)

    plt.figure(figsize=(10, 3))
    plt.xticks([0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335], labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.xlabel("Birthday")
    plt.ylabel(f"Total {stat_total}")
    plt.title(f"Total {stat_dict[stat_total]} For Each Birthday")
    plt.plot(stat_totals)

    st.pyplot(plt.gcf())

    stat_totals_l_to_h = sorted(stat_totals)
    stat_totals_h_to_l = sorted(stat_totals, reverse=True)

    st.write(f"**Top 5 birthdays by total {stat_dict[stat_total]}:**")

    for i in range(0, 5):
        m, d = get_month_and_day(stat_totals.index(stat_totals_h_to_l[i]))
        st.text(f"{i+1}.  {month_names[m-1]} {d}    --    {f'{stat_totals_h_to_l[i]:.1f}'.rstrip('0').rstrip('.')}")
    
    st.text("\n")
    st.write(f"**Bottom 5 birthdays by total {stat_dict[stat_total]}:**")

    for i in range(0, 5):
        m, d = get_month_and_day(stat_totals.index(stat_totals_l_to_h[i]))
        st.text(f"{i+1}.  {month_names[m-1]} {d}    --    {f'{stat_totals_l_to_h[i]:.1f}'.rstrip('0').rstrip('.')}")

    # Averages

    stat_avg = st.selectbox("Statistic for Averages graph",
                        ("WAR", "Games Played (Batted)", "Games Played (Pitched)", "AB", "H", "HR", "RBI", "SB", "AVG", "OBP*", "SLG", "OPS*", "IP", "Pitching Wins", "Pitching Losses", "ERA", "ERA+", "WHIP", "Saves", "K"))
    st.write("\* Due to lack of a Plate Appearances stat in the data, aggregated OBP and OPS are estimated based on a rough calculation of PA as AB + BB. This excludes HBP, IBB, and sacrifices, but should be close enough to the correct numbers on a large scale.")

    stat_avgs = calculate_total_or_avg_stats(all_data, stat_dict[stat_avg], avgs, True)

    plt.figure(figsize=(10, 3))
    plt.xticks([0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335], labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.xlabel("Birthday")
    plt.ylabel(f"Average {stat_avg}")
    plt.title(f"Average {stat_dict[stat_avg]} For Each Birthday")
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


    for i in range(0, 5):
        m, d = get_month_and_day(stat_avgs.index(good[i]))
        st.text(f"{i+1}.  {month_names[m-1]} {d}    --    {good[i]:.3f}")
    
    st.text("\n")
    st.write(f"**Bottom 5 birthdays by average {stat_avg}:**")

    for i in range(0, 5):
        m, d = get_month_and_day(stat_avgs.index(bad[i]))
        st.text(f"{i+1}.  {month_names[m-1]} {d}    --    {bad[i]:.3f}")
