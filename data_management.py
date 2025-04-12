import json
import pandas as pd
import os
from datetime import datetime, timedelta
from configparser import ConfigParser
import random
import requests

ID_LENGTH = 8
DATA_COLUMNS = ["event", "description", "type", "start", "duration", "location"]
config = ConfigParser()
df_events: pd.DataFrame = None
df_prefab: pd.DataFrame = None
msg_of_the_day = ""

def null_proof(data):
    if data is None:
        return ""
    elif str(data) == "nan":
        return ""
    else:
        return str(data)

def get_timestamp(*, add=0):
    time = datetime.now() + timedelta(minutes=add)
    return time.strftime("%Y-%m-%d_%H:%M")

def __create_id():
    key = "".join([random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(ID_LENGTH)])
    count = 0
    if df_prefab is not None:
        while [id for id in df_prefab["id"]].__contains__(key):
            key = "".join([random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(ID_LENGTH + (count//10))])
            count += 1
    return key

def load_data():
    global df_events, df_prefab
    config["admin"] = {"password": "password123", "trusted_ips": "127.0.0.1"}
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

    if os.path.exists("./data/events.csv"):
        df = pd.read_csv("./data/events.csv")
        for col in DATA_COLUMNS:
            if col not in df.columns:
                print('\033[91m', "Timetable is missing a Data: no", col, "Colum found!", '\033[0m')
                print('\033[91m', "Aborting Setup! Please fix or delete 'data/events.csv'!", '\033[0m')
                exit(1)
        if not "id" in df.columns:
            df["id"] = pd.Series([__create_id() for _ in range(len(df))], index=df.index)
        df = df[["id"] + DATA_COLUMNS]
        df.sort_values(by="start", inplace=True)
        df.reset_index(drop=True, inplace=True)
    else:
        sample_num = 50
        data = {
            "id": [__create_id() for _ in range(sample_num)],
            "event": ["Sample_"+str(i) for i in range(sample_num)],
            "description": ["Just an Example." for _ in range(sample_num)],
            "type": ["default" for _ in range(sample_num)],
            "start": [get_timestamp(add=10*i) for i in range(sample_num)],
            "duration": [30 for _ in range(sample_num)],
            "location": ["stage"+str(i%6) for i in range(sample_num)]
        }
        df = pd.DataFrame(data)
    df_events = df.copy()
    df_prefab = df.copy()

def post_update():
    global df_events
    if config.get("post_api", "url") == "":
        return
    csv = df_events[DATA_COLUMNS].to_csv(index=False)
    json_str = json.dumps({
        "event": config.get("post_api", "id"),
        "message": "TODO, just a string to display",
        "data": csv,
    })
    try:
        requests.post(config.get("post_api", "url"), json=json_str)
    except requests.exceptions.RequestException:
        print('\033[91m', "Failed to post event update too Website", '\033[0m')


def check_login(pw):
    return config.get("admin", "password") == pw

def reset_prefab():
    global df_prefab
    df_prefab = df_events.copy()

def update_table():
    global df_events
    df_events = df_prefab.copy()
    with open("./data/events.csv", "w") as file:
        df_events[DATA_COLUMNS].to_csv(file, index=False)
    post_update()


def get_time_table(*, prefab=False, location: None|str=None):
    if prefab:
        df = df_prefab.copy()
    else:
        df = df_events.copy()
    if location is not None:
        df = df[df["location"] == location]
    df.sort_values(by="start", inplace=True)
    return df.to_html(index=False)


def get_current_event(location, *, prefab=False):
    if prefab:
        df = df_prefab
    else:
        df = df_events
    df = df[df["location"] == location]
    df.reset_index(inplace=True)
    if len(df) == 0:
        return "", "", "", None
    index = 0
    tstamp = get_timestamp()
    while index < len(df) and df.iloc[index]["start"] < tstamp:
        index += 1
    index -= 1
    if index < 0:
        return "", "", "", None
    event = df.iloc[index]
    if event["start"] < get_timestamp(add=-int(event["duration"])):
        return "Break", "Pleas wait for the next Event to start", "", None
    return event["event"], event["description"], event["start"], event["duration"]

def get_next_event(location, *, prefab=False):
    if prefab:
        df = df_prefab
    else:
        df = df_events
    df = df[df["location"] == location]
    df.reset_index(inplace=True)
    if len(df) == 0:
        return "", "", "", None
    index = 0
    tstamp = get_timestamp()
    while index < len(df) and df.iloc[index]["start"] < tstamp:
        index += 1
    if index == len(df):
        return "", "", "", None
    event = df.iloc[index]
    return event["event"], event["description"], event["start"], event["duration"]

def get_locations():
    return df_events["location"].unique().tolist()

def edit_event(id, name, description, type, start, duration, location):
    index = df_prefab.loc[df_prefab["id"] == id].index[0]
    df_prefab.iloc[int(index)] = (id, name, description, type, start, duration, location)

def delete_event(id):
    try:
        index = df_prefab.loc[df_prefab["id"] == id].index[0]
        df_prefab.drop(index, inplace=True)
    except IndexError:
        pass

def add_event(name, description, type, start, duration, location):
    global df_prefab
    data = {
        "id": [__create_id()],
        "event": [name],
        "description": [description],
        "type": [type],
        "start": [start],
        "duration": [duration],
        "location": [location]
    }
    df_prefab = pd.concat([df_prefab, pd.DataFrame(data)])
    df_prefab.reindex()


load_data()
