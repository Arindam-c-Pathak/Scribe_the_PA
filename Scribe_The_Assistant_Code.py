import webbrowser
import os
import speech_recognition as sr
import subprocess
import pyttsx4
from googleapiclient.discovery import build
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+ required
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
import nltk
import winsound
from plyer import notification
import time
import threading
nltk.download('punkt')

'''..........///////// Important API keys and settings.......Do not edit or touch...\\\\\\\\..........'''
# Set up your API key and CSE ID
api_key = "Enter_your_api_key_here"
cse_id = "Enter_your_CSE_id_here"
service = build("customsearch", "v1", developerKey=api_key)

#speech settings
speech_engine = pyttsx4.init()
speech_engine.setProperty('rate', 190)  # Speed of speech
speech_engine.setProperty('volume', 1)  # Volume level (0.0 to 1.0)
voices = speech_engine.getProperty('voices')   #for setting the voice type
speech_engine.setProperty('voice', voices[0].id)
#hearing settings
recognizer = sr.Recognizer()
'''....End of settings and keys...'''
def beeping():
    winsound.Beep(400,200)
    
# Function to capture voice input and process it
def listen_for_commands():
    #for particular use
    with sr.Microphone() as source:
        print("Listening...")
        beeping()
        recognizer.adjust_for_ambient_noise(source, duration=2)#adjust for ambient noises, increasing the persistence duration
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)#adjust the time out as required, and change parsing wait time
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            respond_to_keyword(text)
        except sr.UnknownValueError:
            speak("Sorry,can you repeat that?")
            return listen_for_commands()#loop the code in case the voice isn't recognised
        except sr.WaitTimeoutError:
            return standby()#go on standby mode in case no command is given
        except Exception as e:
            print(f"An error occurred: {e}")
            speak("An error occurred, please try again.")#for any other errors
def listening():
    #for general use of mic input
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            words = nltk.word_tokenize(text.lower())#tokenize the words to make them easier to search through
            return words #return the word tokens to be searched through
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
            return listening() #loop
        except sr.WaitTimeoutError:
            standby() #no input condition
def speak(Statement):
    #to give outputs
    say=Statement
    print(Statement)
    speech_engine.say(say)
    speech_engine.runAndWait()

def set_timer(duration, reminder, message):
    def countdown():
        print(f"Timer set for {duration} seconds.")
        time.sleep(duration)
        speak(message)
        send_notification(reminder, message)
    #using a thread cause the code kept stopping when timer was started. this helps code run while timer is set
    timer_thread = threading.Thread(target=countdown)
    timer_thread.start()
    
def send_notification(title, message):
    #for sending notification after timer is needed
    notification.notify(
        title=title,
        message=message,
        app_name='Scribe', 
        timeout=10
    )

def Searching(query):
    '''Searching Algorithm that opens link of top result'''
    results = service.cse().list(q=query, cx=cse_id, num=3).execute()
    speak(f"Top results from Google for {query}")
    for item in results.get('items', []):
        speak(item['title'])
        print(item['link'])
    if 'items' in results and len(results['items']) > 0:
        i=0
        while i<len(results['items']):
            resul = results['items'][i]['title']  # Store title
            link = results['items'][i]['link']  # Store link
            speak(f"Opening {resul} in the browser")
            open_link(link)
            i=i+1
'''End of the Searching Algorithm'''

def greeting():
    #Responds according to the time of the day
    speak("Scribe Online.")
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        speak("Good morning. \nLet's start the day with a little energy. \nHere are your scheduled events")
        #Daily_events()
        speak("As for the weather:")
        get_weather("Tanakpur")
    elif 12 <= current_hour < 17:
        speak(f"Good afternoon. \nA late start to the day? Let me get the weather details first.")
        get_weather("Tanakpur")
        speak("As for your schedule")
        #Daily_events()
    elif 17 <= current_hour < 21:
        speak(f"Nice evening we're having.\nFinally sitting down to work, are we? Let me check through the calender")
        #Daily_events()
    else:
        speak(f"It's pretty late to start the day. What are the plans for the night?")
        
#'''......................WEATHER SEARCH CODE...................'''
weather_api_key = "Enter_your_api_for_weather_search_here"
def get_weather(city="Enter_Default_city"):
    base_url = "Enter_Base_Url_for_API_call"
    params = {
        'q': city,          
        'appid': weather_api_key, 
        'units': 'metric'
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        speak(f"Gathering the weather data for {city}")
        speak(f"Temperature is {temperature}°C\nand the Humidity is {humidity}% \nThe overall appearence of sky seems to be of {weather}")
    else:
        print(f"Error: Unable to get weather data for {city}. Status code: {response.status_code}")
#'''........WEATHER CODE END.......'''
        
'''........../////////CALENDER RELATED CODE.... DO NOT TOUCH\\\\\\\\........'''
#Booting up the api from files...
def create_service():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = r'path\to\the\credetials.json'#working file for the api
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    return service
def create_event(date, time, event_summary, duration_minutes=60, timezone_name='time\zone'):
#Function to Create an Event
    service = create_service()
    event_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    local_tz = ZoneInfo(timezone_name)
    event_start = event_start.replace(tzinfo=local_tz)  # Attach the time zone to the datetime
    event_end = event_start + timedelta(minutes=duration_minutes)
    event = {
        'summary': event_summary,
        'start': {
            'dateTime': event_start.isoformat(),
            'timeZone': timezone_name,
        },
        'end': {
            'dateTime': event_end.isoformat(),
            'timeZone': timezone_name,
        },
    }
    # Insert the event into the calendar
    event_result = service.events().insert(calendarId='primary', body=event).execute()
    speak(f"{event_summary} created on {date} from {time} hours for duration of {duration_minutes} minutes")
    print(f"Link to the event= {event_result.get('htmlLink')}")
    return event_result
def search_event_name(query, time_min=None, time_max=None, timezone_name='time/zone'):
#to search for events based on names
    service = create_service()
    if not time_min:
        local_tz = ZoneInfo(timezone_name)
        time_min = datetime.now(local_tz).isoformat()
    events_result = service.events().list(
        calendarId='primary', 
        q=query, 
        timeMin=time_min, 
        timeMax=time_max,
        maxResults=10, 
        singleEvents=True, 
        orderBy='startTime'
    ).execute()   
    events = events_result.get('items', [])
    if not events:
        speak(f'There are no events with keyword {query}')
        return
    speak(f"I found following events with the key word: {query}")
    i=1
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start_datetime = datetime.fromisoformat(start.replace('Z', '+00:00')).astimezone(ZoneInfo(timezone_name))
        event_date = start_datetime.date()
        event_time = start_datetime.time()
        speak(f"Number {i} is on {event_date} from {event_time}. The full Title is {event['summary']}.")
        i=i+1
    return events
def delete_event(event_id):
#Function to Delete an Event
    service = create_service()
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    speak(f"Event has been deleted.")    
def search_event_date(date, timezone_name='time/zone'):
#to search for event based on date
    service = create_service()
    local_tz = ZoneInfo(timezone_name)
    time_min = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=local_tz).isoformat()
    time_max = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).replace(tzinfo=local_tz).isoformat()
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=time_min, 
        timeMax=time_max,
        maxResults=10, 
        singleEvents=True, 
        orderBy='startTime'
    ).execute()  
    events = events_result.get('items', [])
    if not events:
        speak(f'{date}: No events scheduled.')
        return
    speak(f"I found the following events on {date}")
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start_datetime = datetime.fromisoformat(start.replace('Z', '+00:00')).astimezone(ZoneInfo(timezone_name))
        event_date = start_datetime.date()
        event_time = start_datetime.time()
        speak(f"{event['summary']} from {event_time}.")
    return events
def show_coming_events():
#Generate a list of dates for upcoming
    speak("Events in the next two days")
    today = datetime.now().date()   
    date_list = [today + timedelta(days=i) for i in range(3)]
    for i in range(1,3):
        date=date_list[i]
        date1=str(date)
        search_event_date(date1, timezone_name='time/zone')
def convert_date(input_date):
    try:
        #to convert spoken date into 'yyyy-mm-dd' format
        cleaned_date = re.sub(r'(st|nd|rd|th)', '', input_date).strip()
        input_format = "%B %d %Y"
        date_obj = datetime.strptime(cleaned_date, input_format)
        formatted_date = date_obj.strftime("%Y-%m-%d")    
        return formatted_date
    except:
        speak("Please state the date with month, date and year")
        input_date1=listening()
        return convert_date(input_date1)
def timing_set():
    time=listening()
    #to change spoken time into time format
    if time in['morning','evening','night', 'afternoon']:
        if time=='morning':
            return '8:00'
        elif time=='afternoon':
            return '12:00'
        elif time=='evening':
            return '17:00'
        elif time=='night':
            return '20:00'
def add_events():
#to add an event into the calendar as needed
    speak("What is the date of the event?")
    d=listening()
    date= convert_date(d)
    speak("What is the timing?")
    time=timing_set()
    speak("What is the summary")
    event_summary=listening()
    create_event(date, time, event_summary, duration_minutes=60, timezone_name='time/zone')
def deleting_events():
#for deleting specific events
    speak("What is the date of the event?")
    d=listening()
    date= convert_date(d)
    speak("Give me a moment to search")
    events=search_event_date(date, timezone_name='time/zone')
    if not events:
        speak("No events found on that date.")
        return
    for event in events:
        event_start = event['start']['dateTime']
        event_summary = event['summary']
        start_date, start_time = event_start.split('T')
        start_time = start_time.split('+')[0]
        print(f"{event_summary} on {start_date} from {start_time}")
    speak("Which event do you want to delete here?")
    query=listening()
    matching_events = search_event_name(query, time_min=None, time_max=None, timezone_name='time/zone')
    if not matching_events:
        speak("No matching events found with that name.")
        return
    if event in matching_events:
        print(f"Deleting event: {event['summary']} (ID: {event['id']})")
        delete_event(event['id'])
    else:
        speak("No such event found.")
def searching_events():
    speak("Search by name or by date?")
    searchingevents=listening()
    if 'name' in searchingevents:
        speak("Give me a key word to search for")
        event_name=listening()
        print(event_name)
        search_event_name(event_name, time_min=None, time_max=None, timezone_name='time/zone')
    elif 'date' in searchingevents:
        speak("Which date am I searching for?")
        event_date=listening()
        date= convert_date(event_date)
        speak("Give me a moment to search")
        events=search_event_date(date, timezone_name='time/zone')
    else:
        speak("Sorry, I couldn't get you.")
        searching_events()       
def Daily_events():
    #Getting daily updates
    now = datetime.now()
    today_date = now.date()
    today_date1= str(today_date)
    today_day_of_week = now.strftime("%A")
    speak(f"Today's {today_day_of_week}, {today_date}")
    events = search_event_date(today_date1, timezone_name='time/zone')
    if events:
        speak("Seems like a busy day. Keep your eye on the clock.")
    else:
        speak("What are the plans for today then?")
'''....../////CALENDER CODE COMPLETE\\\\\\......'''
def open_link(link):
#for opening url that are implemented here
    url = link
    webbrowser.open(url)
def standby():
    speak("Going on standby")
    calling_scribe()
def ending():
    os._exit(0)
def open_program(program_name):    
#Helpful in opening programs needed as required
    program_paths = {
        "program1": r"path\to\program1.exe",
        "program2": r"path\to\program2.exe",
        "program3": r"path\to\program3.exe",
        "program4": r"path\to\program4.exe",
        "program5": r"path\to\program5.exe",
        "program6": r"path\to\program6.exe",
    }
    path = program_paths.get(program_name.lower())
    if path and os.path.exists(path):
        try:
            speak(f"Opening {program_name}")
            subprocess.Popen([path])
        except Exception as e:
            print(f"Failed to open {program_name}. Error: {e}")
    else:
        print(f"Program '{program_name}' not found in predefined paths or path is incorrect.")
def playing_games():
#when playing games
    speak("Which game do you want to play?")
    game=listening()
    if "program1" in game:
        open_program("program1")
    elif "program2" in game:
        open_program("program2")
    elif "program3" in game:
        open_program("program3")
    else:
        speak("I can't find that game on the computer. Try again.")
        playing_games()
    speak("Have fun. Scribe logging out.")
    ending()
# Function to respond to keywords
def respond_to_keyword(text):
    # Tokenize the input text
    words = nltk.word_tokenize(text.lower())
    if "open" in words or "start" in words:
        if "open" in words:
            program_name = text.split("open", 1)[1].strip()
        else:
            program_name = text.split("start", 1)[1].strip()
        open_program(program_name)
    elif "hello" in words or "hey" in words or "hi" in words:
        speak("Hello! Scribe of the lost library at your service.\nJust call my name if you need my assistance")
        calling_scribe()
    elif "bye" in words or "goodbye" in words or "exit" in words or "close" in words or "shutdown" in words:
        speak("As you wish. \nSee you later.")
        ending()
    elif "standby" in words:
        standby()
    elif "calendar" in words or "schedule" in words or "events" in words or "event" in words:
        speak("Checking Calendar. Give me a moment")
        if "delete" in words:
            deleting_events()
        elif "create" in words or "book" in words:
            add_events()
        elif "search" in words or "find" in words:
            searching_events()
        else:
            show_coming_events()
    elif "work" in words or "project" in words or "code" in words or "working" in words or "coding" in words:
        speak("Preparing the workstation as you like it.")
        speak("Setting timer for an hour")
        set_timer(3600, 'Take a break', 'An hour has passed, take a break')
        open_program("program_name")
        open_program("program_name")
        open_link("Enter relevant link here")
        standby()
    elif "relax" in words or "music" in words or "song" in words or "songs" in words or "movie" in words or "movies" in words or "series" in words or "chill" in words:
        if "music" in words or "song" in words or "songs" in words:
            speak("Opening your playlist for music")
            open_link("enter link to song playlist here")
        elif "movie" in words or "movies" in words:
            speak("Opening the movie library")
            open_link("Enter link to the prefered movie streaming website")
        elif "series" in words:
            speak("Opening the movie library")
            open_link("Enter link to the prefered series streaming website")
        else:
            speak("Enter default response here")
            open_link("enter link to default response")
    elif "game" in words or "games" in words:
        playing_games()
    elif "read" in words or "books" in words or "book" in words:
        speak("Setting up the mood")
        open_link("link to book library")
        speak("Have fun reading")
        standby()        
    elif "timer" in words or "reminder" in words:
        if "hour" in words or "hours" in words:
            timer1 = text.split("for", 1)[1].strip()
            timer = [int(s) for s in timer1.split() if s.isdigit()][0]
            duration= timer*60*60
            set_timer(duration, 'Reminder', 'Time is up')
        elif "minute" in words or "minutes" in words:
            timer1 = text.split("for", 1)[1].strip()
            timer = [int(s) for s in timer1.split() if s.isdigit()][0]
            duration= timer*60
            set_timer(duration, 'Reminder', 'Time is up')
        else:
            speak("Can you repeat that?")
    elif "study" in words or "studies" in words or "studying" in words:
        speak("Alright. Setting timer for an hour")
        set_timer(3600, 'Take a break', 'An hour has passed, take a break')        
    elif "weather" in words:
        if "for" in text:
            city = text.split("for", 1)[1].strip()  # Extract city after "for"
        elif "in" in text:
            city = text.split("in", 1)[1].strip()  # Extract city after "for"
        else:
            city = ""  # No city provided
        if city:
            get_weather(city)
        else:
            get_weather()
    elif "search" in words or "what" in words or "how" in words or "when" in words or "who" in words or "where" in words or "why" in words:
        if "search" in words:
            search_query = text.split("for", 1)[1].strip()  # Get everything after "search"
        elif "what" in words:
            search_query = text.strip()
        elif "how" in words:
            search_query = text.strip()
        elif "when" in words:
            search_query = text.strip()
        elif "who" in words:
            search_query = text.strip()
        elif "where" in words:
            search_query = text.strip()
        elif "why" in words:
            search_query = text.strip()
        if search_query:
            Searching(search_query)
        else:
            speak("No results. Can you repeat the question?")
            listen_for_commands()
    else:
        speak("Sorry, I don't understand.")
        listen_for_commands()
        
def calling_scribe():
    """Function to listen for the keyword 'scribe'."""
    with sr.Microphone() as source:
        print("Listening for the keyword 'scribe'...")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        while True:
            try:
                audio = recognizer.listen(source, timeout=30, phrase_time_limit=2)
                text = recognizer.recognize_google(audio).lower()
                print(f"user said= {text}")
                # Check if the keyword 'scribe' is in the recognized text
                if "scribe" in text:
                    print("Keyword 'scribe' detected.")
                    #speak("Scribe here. What do you need?")
                    beeping()
                    listen_for_commands()                   
            except sr.UnknownValueError:
                # Handle cases where speech is not recognized
                calling_scribe()
            except sr.RequestError as e:
                # Handle API request errors
                print(f"Could not request results from Google Speech Recognition service; {e}")
'''................END OF THE CALLING CODE..............'''                
# Example loop to keep the bot running
greeting()
while True:
    calling_scribe()
    
