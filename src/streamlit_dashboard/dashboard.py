import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.add_vertical_space import add_vertical_space

score_icon = '<i class="fa fa-star" style="padding-top: 10px;color: red;"></i>'
user_icon = '<i class="fa fa-user" style="padding-top: 10px;margin-left: 10px;"></i>'
clock_icon = '<i class="fa fa-clock" style="padding-top: 10px;margin-left: 10px;"></i>'
link_icon = '<i class="fa fa-external-link" style="padding-top: 10px;margin-left: 10px;"></i>'

def show_dashboard(df):
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    """, unsafe_allow_html=True)

    # Main container for displaying news items
    for index, row in df.iterrows():
        with stylable_container(
            key="container_with_border",
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    background-color: aliceblue;
                    padding: calc(1em - 1px)
                }
                """,
            ):
            # Create a link for the title
            st.markdown(f'### [{row["TITLE"]}]({row["URL"]})', unsafe_allow_html=True)
            st.write(row["SUMMARY"])
            score = row.get("SCORE", "")
            time = format_time(row.get("POSTED_TIME", ""))
            published_by = row.get("PUBLISHBY", "")
            hacker_news_link = f'<a href="{row.get("HN_LINK")}" target="_blank">{link_icon} Hacker News</a>'
            st.markdown(f"{score_icon} {score} points {user_icon} {published_by} {clock_icon} {time} {hacker_news_link}", unsafe_allow_html=True)
                    
def format_time(date_string):  
    # Convert the date string to a datetime object
    date_timestamp = pd.Timestamp(date_string)
    # Calculate the current date and time for comparison
    current_time_now = datetime.now()

    # Calculate the difference in time
    time_difference_now = current_time_now - date_timestamp.to_pydatetime()

    # Convert difference to hours and minutes
    hours_difference_now = int(time_difference_now.total_seconds() // 3600)
    minutes_difference_now = int(time_difference_now.total_seconds() % 3600 // 60)
    if hours_difference_now < 1.0:
        return str(minutes_difference_now) + " min ago"
    return str(hours_difference_now) + " hours ago"