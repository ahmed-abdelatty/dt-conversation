import os
import random
from datetime import datetime
import streamlit as st
 
from langchain.tools import tool
 
 
#decorator
def enable_chat_history(func):
    if os.environ.get("OPENAI_API_KEY"):
 
        # to clear chat history after swtching chatbot
        current_page = func.__qualname__
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = current_page
            
        if st.session_state["current_page"] != current_page:
            try:
                st.cache_resource.clear()
                del st.session_state["current_page"]
                del st.session_state["messages"]
            except:
                pass
 
        # to show chat history on ui
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
        for msg in st.session_state["messages"]:
            st.chat_message(msg["role"]).write(msg["content"])
 
    def execute(*args, **kwargs):
        func(*args, **kwargs)
    return execute
 
def display_msg(msg, author):
    """Method to display message on the UI
 
    Args:
        msg (str): message to display
        author (str): author of the message -user/assistant
    """
    st.session_state.messages.append({"role": author, "content": msg})
    st.chat_message(author).write(msg)
 
def configure_openai_api_key():
    openai_api_key= os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        st.session_state['OPENAI_API_KEY'] = openai_api_key
    else:
        st.error("Please add your OpenAI API key to continue.")
        st.info("Obtain your key from this link: https://platform.openai.com/account/api-keys")
        st.stop()
    return openai_api_key
 
 
def define_custom_tools():
    user_schedule = [
            {   
                "day": "31/01/2024",
                "fromClock": "3:00 PM",
                "toClock": "4:00 PM",
                "event": "work meeting"
            },
            {   
                "day":  "31/01/2024",
                "fromClock": "5:30 PM",
                "toClock": "7:00 PM",
                "event": "workout"
            }
    ]
    watch_later =  {
        "Movies": [
            {"Title": "Inception", "Status": "Watching", "PausedTime": None},
            {"Title": "The Matrix", "Status": "Not Started", "PausedTime": None}
        ],
        "Series": [
            {"Title": "Stranger Things", "Status": "Paused", "CurrentEpisode": 5, "Season": 2, "PausedTime": "20:54"},
            {"Title": "Breaking Bad", "Status": "Completed", "PausedTime": None}
        ]
    }
    
    exercises = ['gym', 'workout', 'play tennis table']
    
    
    @tool("put_media_on", return_direct=True)
    def put_media_on(title: str, current_episode: int = None, season: int = None) -> str:
        """
        Display the given media title and details.
        Turns on the TV if it is turned off
        """
        found = False
 
        def update_status(media_list, title, new_status, current_episode=None, season=None):
            for media in media_list:
                if media["Title"] == title:
                    media["Status"] = new_status
                    media["PausedTime"] = None if new_status == "Watching" else media["PausedTime"]
                    if "CurrentEpisode" in media and current_episode is not None:
                        media["CurrentEpisode"] = current_episode
                    if "Season" in media and season is not None:
                        media["Season"] = season
                    return True
            return False
 
        # Pause any other media that is currently being watched
        for category in watch_later:
            for media in watch_later[category]:
                if media["Status"] == "Watching" and media["Title"] != title:
                    media["Status"] = "Paused"
 
        # Check and update in Movies
        if update_status(watch_later["Movies"], title, "Watching"):
            found = True
 
        # Check and update in Series
        if not found and update_status(watch_later["Series"], title, "Watching", current_episode, season):
            found = True
 
        # If title not found, add it as a new entry in Movies or Series
        
        if not found:
            if current_episode is not None and season is not None:
                watch_later["Series"].append({"Title": title, "Status": "Watching", "CurrentEpisode": current_episode, "Season": season, "PausedTime": None})
            else:
                watch_later["Movies"].append({"Title": title, "Status": "Watching", "PausedTime": None})
 
        res = f"Movie with title {title} will be displayed on the TV"
        if current_episode is not None and season is not None:
            res = f"Series with title {title} with episode {current_episode} and season {season} will be displayed on the TV"
 
        return res
    
    @tool("get_watch_later", return_direct=False)
    def get_watch_later() -> str:
        """
        Get the watch_later for the user TV
        """
        print("watch_later: ", watch_later)
        res = ""
        for category in watch_later:
            res += f"{category}:\n"
            for item in watch_later[category]:
                status = item["Status"]
                title = item["Title"]
                paused_time = item.get("PausedTime", "N/A")
                current_episode = item.get("CurrentEpisode", "N/A")
                season = item.get("Season", "N/A")
                res += f"  - Title: {title}, Status: {status}, Paused Time: {paused_time}"
                if category == "Series":
                    res += f", Current Episode: {current_episode}, Season: {season}"
                res += "\n"
 
        return "The User's Watch Later List:\n" + res
 
    @tool("recommend_media", return_direct=False)
    def recommend_media() -> str:
        """
        Recommend a movie or series from the watch later list that are either paused or not started.
        """
        recommendations = []
        for category in watch_later:
            for item in watch_later[category]:
                if item["Status"] in ["Paused", "Not Started"]:
                    recommendations.append(f"{item['Title']} ({category[:-1]})")
 
        if recommendations:
            res = "Recommended to watch:\n" + "\n".join(recommendations)
        else:
            res = "No media to recommend at the moment."
 
        return res
  
    @tool("open_tv", return_direct=True)
    def control_tv(action:str) -> str:
        """Control the TV based on the action provided
            The action must only be on or off!
        """
        return "TV is now " + action
    
    @tool("control_light", return_direct=True)
    def control_light(action:str) -> str:
        """Control the light based on the action provided
           The action must only be on or off!
        """
        return "Light is now " + action
    
    @tool("control_ac", return_direct=True)
    def control_ac(action:str) -> str:
        """Control the AC based on the action provided
           The action must only be on or off!
        """
        return "AC is now " + action
    
    @tool("get_schedule", return_direct=False)
    def get_schedule() -> str:
        """
        Get user schedule
        """
        print("user schedule: ", user_schedule)
        res = ""
        for schedule in user_schedule:
            res += f"On {schedule['day']} from {schedule['fromClock']} to {schedule['toClock']}, there is an event: {schedule['event']}\n"
 
        return "The User's schedule is:\n" + res
    
    @tool("book_schedule_slot", return_direct=True)
    def book_schedule_slot(event: str, from_time: str, to_time: str, day: str = None) -> str:
        """Book a slot in the user schedule."""
        now = datetime.now()
 
        # Set the day to today if not specified
        if day is None:
            day = now.strftime("%d/%m/%Y")
 
        # Convert day and times to datetime objects for comparison
        datetime_format = "%d/%m/%Y %I:%M %p"
        from_datetime = datetime.strptime(f"{day} {from_time}", datetime_format)
        to_datetime = datetime.strptime(f"{day} {to_time}", datetime_format)
 
        # Check if the slot is in the past
        if from_datetime < now or to_datetime < now:
            return "Cannot book a slot in the past."
 
        # Check if the time slot is already booked
        for schedule in user_schedule:
            scheduled_from = datetime.strptime(f"{schedule['day']} {schedule['fromClock']}", datetime_format)
            scheduled_to = datetime.strptime(f"{schedule['day']} {schedule['toClock']}", datetime_format)
 
            if day == schedule['day'] and (scheduled_from < to_datetime and from_datetime < scheduled_to):
                return f"Slot from {from_time} to {to_time} on {day} is already booked for {schedule['event']}."
 
        # If the slot is available, book it
        user_schedule.append({
            "day": day,
            "fromClock": from_time,
            "toClock": to_time,
            "event": event
        })
 
        return f"You have booked a slot for {event} from {from_time} to {to_time} on {day}."
        
    @tool("recommend_exercise", return_direct=True)
    def recommend_exercise() -> str:
        """Recommend exercise to the user
        """        
        return "What about spending sometimes on " + random.choice(exercises)
 
    @tool("give_recommendation", return_direct=True)
    def give_recommendation(user_inquiry:str) -> str:
        """Provide recommendation for the user if the user asked for one.
           Also, if the user taked about his feeling or his day give recommendation"""
        if "sleep" in user_inquiry: return "How about closing the lights and tv"
        elif "tired" in user_inquiry: return "How about refreshing drink"
        elif "feel hot" in user_inquiry: return "How about turning on the AC"
        elif "empty schedule" in user_inquiry: return "How about doing some exercise"
        return "How about watching the TV"
    
    return [
        control_tv,control_light,
        give_recommendation,
        control_ac,
        recommend_exercise,
        book_schedule_slot,
        get_schedule,
        put_media_on,
        recommend_media,
        get_watch_later
    ]