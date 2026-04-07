import json
import pandas as pd
import os
from datetime import datetime, timedelta
from configparser import ConfigParser
import random
import requests
import logging_manager as lm

ID_LENGTH = 8
DATA_COLUMNS = ["event", "description", "type", "start", "duration", "location"]
config = ConfigParser()
df_events: pd.DataFrame = None
df_prefab: pd.DataFrame = None
msg_of_the_day = ""


def get_timestamp(*, add=0):
    """
    return current timestamp
    :param add: minute offset from current time
    :return: current time as timestamp String
    """
    time = datetime.now() + timedelta(minutes=add)
    return time.strftime("%Y-%m-%d_%H:%M")

def to_timestamp(time):
    """
    convert datetime Object to timestamp String
    :param time: datetime Object to be converted
    :return: timestamp String
    """
    return time.strftime("%Y-%m-%d_%H:%M")

def from_timestamp(stamp):
    """
    convert timestamp string to datetime Object
    :param stamp: Timestamp String to be converted
    :return: datetime Object
    """
    date, time = stamp.split("_")
    year, month, day = date.split("-")
    hour, minute = time.split(":")
    return datetime(int(year), int(month), int(day), int(hour), int(minute))

def shift_timestamp(timestamp, minutes):
    """
    shift timestamp string by given number of minutes
    :param timestamp: timestamp String to be shifted
    :param minutes: amount of minutes to be shifted
    :return: timestamp String
    """
    dt = from_timestamp(timestamp)
    dt += timedelta(minutes=int(minutes))
    return to_timestamp(dt)


def __create_id():
    """
    create unique event id
    :return: id String
    """
    keyset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    key = "".join([random.choice(keyset) for _ in range(ID_LENGTH)])
    count = 0
    if df_prefab is not None:
        while [id for id in df_prefab["id"]].__contains__(key):
            key = "".join([random.choice(keyset) for _ in range(ID_LENGTH + (count//10))])
            count += 1
    return key

def load_data(table_gen_len=50, table_gen_loc_count=6):
    """
    load data from Files or generate new Files if missing
    :return:
    """
    global df_events, df_prefab
    config["admin"] = {"password": "password123", "trusted_ips": "127.0.0.1"}
    config["logging"] = {"level": "default", "log_logins": "True", "timestamp": "True"}
    config["server"] = {"host": "127.0.0.1", "port": "8080"}
    config["post_api"] = {"id": "test", "url": ""}

    if os.path.exists("./data/config.ini"):
        config.read("./data/config.ini")
    else:
        try:
            os.mkdir("./data")
        except FileExistsError:
            pass
        try:
            os.mkdir("./static")
        except FileExistsError:
            pass
        try:
            os.mkdir("./fonts")
        except FileExistsError:
            pass

        with open("./data/config.ini", "w") as f:
            config.write(f)
        return False
    lm.CONF = config["logging"]

    if os.path.exists("./data/events.csv"):
        df = pd.read_csv("./data/events.csv")
        for col in DATA_COLUMNS:
            if col not in df.columns:
                print('\033[91m', "Timetable is missing a Data: no", col, "Colum found!", '\033[0m')
                print('\033[91m', "Aborting Setup! Please fix or delete 'data/events.csv'!", '\033[0m')
                exit(2)
        if not "id" in df.columns:
            df["id"] = pd.Series([__create_id() for _ in range(len(df))], index=df.index)
        df = df[["id"] + DATA_COLUMNS]
        df.sort_values(by="start", inplace=True)
        df.reset_index(drop=True, inplace=True)
    else:
        sample_num = table_gen_len
        data = {
            "id": [__create_id() for _ in range(sample_num)],
            "event": ["Sample_"+str(i) for i in range(sample_num)],
            "description": ["Just an Example." for _ in range(sample_num)],
            "type": ["default" for _ in range(sample_num)],
            "start": [get_timestamp(add=(10*i)-5) for i in range(sample_num)],
            "duration": [30 for _ in range(sample_num)],
            "location": ["["+"abcdefghijklmnopqrstuvwxyz"[i%table_gen_loc_count]+"]stage"+str(i%table_gen_loc_count) for i in range(sample_num)]
        }
        df = pd.DataFrame(data)
    df_events = df.copy()
    df_prefab = df.copy()
    return True

def post_update():
    global df_events, msg_of_the_day
    if config.get("post_api", "url") == "":
        return
    csv = df_events[DATA_COLUMNS].to_csv(index=False)
    json_str = json.dumps({
        "event": config.get("post_api", "id"),
        "message": msg_of_the_day,
        "data": csv,
    })
    try:
        res = requests.post(config.get("post_api", "url"), json=json_str)
        if res.status_code != 200:
            lm.log("Failed to post event update too Website\n", res.text, msg_type=lm.LogType.Error)
    except requests.exceptions.RequestException:
        lm.log("Failed to post event update too Website", msg_type=lm.LogType.Error)


def check_login(pw):
    """
    check login credentials
    :param pw: password
    :return: Boolean: is login correct
    """
    return config.get("admin", "password") == pw

def reset_prefab():
    """
    reset prefab datatable
    :return:
    """
    global df_prefab
    df_prefab = df_events.copy()
    lm.log("Prefab reset", msg_type=lm.LogType.DataUpdated)

def update_table():
    """
    update datatable from prefab table
    :return:
    """
    global df_events
    df_events = df_prefab.copy()
    lm.log("Database Updated from prefab", msg_type=lm.LogType.DataUpdated)
    with open("./data/events.csv", "w") as file:
        df_events[DATA_COLUMNS].to_csv(file, index=False)
    post_update()


def get_public_table_csv(time_filter=None, location_filter=None):
    """
    get datatable as csv
    :param time_filter: "no_past"|"future_only"
    :param location_filter: str: location_name must contain
    :return: csv as str
    """
    df = df_events.copy()
    df.sort_values(by="start", inplace=True)
    if location_filter is not None:
        df = df[df["location"].str.contains(location_filter)]
    if time_filter is not None:
        if time_filter == "no_past":
            def filter(event):
                event["is_active"] = to_timestamp(from_timestamp(event["start"]) + timedelta(minutes=int(event["duration"]))) >= get_timestamp()
                return event
            df = df.apply(filter, axis=1)
            df = df[df["is_active"] == True]
        if time_filter == "future_only":
            df = df[df["start"] >= get_timestamp()]
    return df[DATA_COLUMNS].to_csv(index=False)

def get_public_table_html(time_filter=None, location_filter=None):
    """
    get datatable as html table
    :param time_filter: "no_past"|"future_only"
    :param location_filter: str: location_name must contain
    :return: html table as str
    """
    df = df_events.copy()
    df.sort_values(by="start", inplace=True)
    if location_filter is not None:
        df = df[df["location"].str.contains(location_filter)]
    if time_filter is not None:
        if time_filter == "no_past":
            def filter(event):
                event["is_active"] = to_timestamp(from_timestamp(event["start"]) + timedelta(minutes=int(event["duration"]))) >= get_timestamp()
                return event
            df = df.apply(filter, axis=1)
            df = df[df["is_active"] == True]
        if time_filter == "future_only":
            df = df[df["start"] >= get_timestamp()]
    return df[DATA_COLUMNS].to_html(index=False)


def get_time_table(*, prefab=False, location: None|str=None):
    def filter(event):
        event["filter"] = event["location"].lower().__contains__(location.lower())
        return event
    if prefab:
        df = df_prefab.copy()
    else:
        df = df_events.copy()
    if location is not None:
        df = df.apply(filter, axis=1)
        df = df[df["filter"] == True]
    df = df[["id"]+DATA_COLUMNS]
    df.sort_values(by="start", inplace=True)
    return df.to_html(index=False)


def get_current_event(location, *, prefab=False):
    """
    get current event data for location
    :param location: str: location of event
    :param prefab: bool: use prefab table
    :return: (str, str, str, int): (Name, Description, Start, Duration(minutes))
    """
    if prefab:
        df = df_prefab
    else:
        df = df_events
    df = df[df["location"] == location]
    df = df.sort_values(by="start")
    df.reset_index(inplace=True)
    if len(df) == 0:
        return "", "", "", 0
    index = 0
    tstamp = get_timestamp()
    while index < len(df) and df.iloc[index]["start"] <= tstamp:
        index += 1
    index -= 1
    if index < 0:
        return "", "", "", 0
    event = df.iloc[index]
    if event["start"] < get_timestamp(add=-int(event["duration"])):
        return "Break", "Pleas wait for the next Event to start", "", None
    return event["event"], event["description"], event["start"], int(event["duration"])

def get_next_event(location, *, prefab=False):
    """
    get data of next Event for location
    :param location: str: location of event
    :param prefab: bool: use prefab table
    :return: (str, str, str, int): (Name, Description, Start, Duration(minutes))
    """
    if prefab:
        df = df_prefab
    else:
        df = df_events
    df = df[df["location"] == location]
    df = df.sort_values(by="start")
    df.reset_index(inplace=True)
    if len(df) == 0:
        return "", "", "", 0
    index = 0
    tstamp = get_timestamp()
    while index < len(df) and df.iloc[index]["start"] <= tstamp:
        index += 1
    if index == len(df):
        return "", "", "", 0
    event = df.iloc[index]
    return event["event"], event["description"], event["start"], int(event["duration"])

def get_locations():
    """
    get all known locations
    :return: list[str]: list of locations
    """
    return df_events["location"].unique().tolist()

def edit_event(id, name, description, type, start, duration, location):
    """
    edit event data by id
    :param id: str: event id to edit
    :param name: str: new event name
    :param description: str: new event description
    :param type: str: new event type
    :param start: str: new event start should be timestamp
    :param duration: int: new event duration in minutes
    :param location: str: new event location
    :return:
    """
    if len(df_prefab.loc[df_prefab["id"] == id].index) == 0:
        lm.log("Event editing failed:", id, "not found!", msg_type=lm.LogType.DataUpdated)
        return
    index = df_prefab.loc[df_prefab["id"] == id].index[0]
    df_prefab.iloc[int(index)] = (id, name, description, type, start, duration, location)
    lm.log("Event edited:", id, name, description, type, start, duration, location, msg_type=lm.LogType.DataUpdated)

def delete_event(id):
    """
    delete event by id
    :param id: str: event id to delete
    :return:
    """
    try:
        index = df_prefab.loc[df_prefab["id"] == id].index[0]
        df_prefab.drop(index, inplace=True)
        lm.log("Event deleted:", id, msg_type=lm.LogType.DataUpdated)
    except IndexError:
        lm.log("Event deleting failed:", id, "not found!", msg_type=lm.LogType.DataUpdated)

def add_event(name, description, type, start, duration, location):
    """
    add new event
    :param name: str: event name
    :param description: str: event description
    :param type: str: event type
    :param start: str: event start should be timestamp
    :param duration: int: event duration in minutes
    :param location: str: event location
    :return: str: new event id
    """
    global df_prefab
    id = __create_id()
    data = {
        "id": [id],
        "event": [name],
        "description": [description],
        "type": [type],
        "start": [start],
        "duration": [duration],
        "location": [location]
    }
    df_prefab = pd.concat([df_prefab, pd.DataFrame(data)])
    df_prefab.reindex()
    lm.log("Event added:", id, name, description, type, start, duration, location, msg_type=lm.LogType.DataUpdated)
    return id


