import pandas as pd
import os
from datetime import datetime, timedelta
from configparser import ConfigParser
import random


ID_LENGTH = 16
config = ConfigParser()
df_events: pd.DataFrame = None
df_prefab: pd.DataFrame = None
dc = False


def null_proof(data):
    if data is None:
        return ""
    elif str(data) == "nan":
        return ""
    else:
        return str(data)

def get_timestamp(*, add=0):
    time = datetime.now() + timedelta(minutes=add)
    return time.strftime("%Y-%m-%d_%H-%M")

def __create_id():
    key = "".join([random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(ID_LENGTH)])
    if df_prefab is not None:
        while [id for id in df_prefab["id"]].__contains__(key):
            key = "".join([random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(ID_LENGTH)])
    return key

def load_data():
    global df_events, df_prefab, dc
    config["admin"] = {"password": "password123"}
    config["server"] = {"host": "127.0.0.1", "port": "8080"}

    if os.path.exists("./data/config.ini"):
        config.read("./data/config.ini")
    else:
        with open("./data/config.ini", "w") as f:
            config.write(f)

    if os.path.exists("./data/events.csv"):
        df = pd.read_csv("./data/events.csv")
        df.sort_values(by="start", inplace=True)
        df.reset_index(drop=True, inplace=True)
    else:
        sample_num = 50
        data = {
            "id": [__create_id() for _ in range(sample_num)],
            "event": ["Sample_"+str(i) for i in range(sample_num)],
            "description": ["Just an Example." for _ in range(sample_num)],
            "start": [get_timestamp(add=10*i) for i in range(sample_num)],
            "location": ["stage"+str(i%6) for i in range(sample_num)]
        }
        df = pd.DataFrame(data)
    df_events = df.copy()
    df_prefab = df.copy()


def check_login(pw):
    return config["admin"]["password"] == pw

def reset_prefab():
    global df_prefab
    df_prefab = df_events.copy()

def update_table():
    global df_events
    df_events = df_prefab.copy()


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
        return "", "", ""
    index = 0
    tstamp = get_timestamp()
    while df.iloc[index]["start"] < tstamp:
        index += 1
    index -= 1
    if index < 0:
        return "", "", ""
    event = df.iloc[index]
    return null_proof(event["event"]), null_proof(event["description"]), null_proof(event["start"])

def get_next_event(location, *, prefab=False):
    if prefab:
        df = df_prefab
    else:
        df = df_events
    df = df[df["location"] == location]
    df.reset_index(inplace=True)
    if len(df) == 0:
        return "", "", ""
    index = 0
    tstamp = get_timestamp()
    while df.iloc[index]["start"] < tstamp:
        index += 1
    event = df.iloc[index]
    return null_proof(event["event"]), null_proof(event["description"]), null_proof(event["start"])

def get_locations():
    return df_events["location"].unique().tolist()

def edit_event(id, name, description, start, location):
    index = df_prefab.loc[df_prefab["id"] == id].index[0]
    df_prefab.iloc[int(index)] = (id, name, description, start, location)

def delete_event(id):
    index = df_prefab.loc[df_prefab["id"] == id].index[0]
    df_prefab.drop(index, inplace=True)

def add_event(name, description, start, location):
    global df_prefab
    data = {
        "id": [__create_id()],
        "event": [name],
        "description": [description],
        "start": [start],
        "location": [location]
    }
    df_prefab = pd.concat([df_prefab, pd.DataFrame(data)])
    df_prefab.reindex()


load_data()