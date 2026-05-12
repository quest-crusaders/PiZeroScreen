import unittest
import os
import subprocess
from datetime import datetime, timedelta

import pandas as pd

import logging_manager as lm


class TestDMTyping(unittest.TestCase):

    def setUp(self):
        try:
            os.mkdir("./data")
        except FileExistsError:
            pass
        cmd = ["mv", "./data", "./data_bk"]
        subprocess.call(cmd)
        import data_management as dm
        dm.load_data()
        dm.load_data()
        lm.CONF = {"level": "none", "log_logins": "False", "timestamp": "True"}
        self.dm = dm

    def tearDown(self):
        cmd = ["rm", "-r", "./data"]
        subprocess.call(cmd)
        cmd = ["mv", "./data_bk", "./data"]
        subprocess.call(cmd)


    def test_get_timestamp(self):
        timestamp = self.dm.get_timestamp()
        self.assertEqual(str, type(timestamp))
        timestamp = self.dm.get_timestamp(add=15)
        self.assertEqual(str, type(timestamp))

    def test_to_timestamp(self):
        timestamp = self.dm.to_timestamp(datetime.now())
        self.assertEqual(str, type(timestamp))

    def test_from_timestamp(self):
        timestamp = self.dm.from_timestamp(self.dm.get_timestamp())
        self.assertEqual(datetime, type(timestamp))

    def test_shift_timestamp(self):
        timestamp = self.dm.shift_timestamp(self.dm.get_timestamp(), 15)
        self.assertEqual(str, type(timestamp))

    def test_check_login(self):
        self.assertEqual(bool, type(self.dm.check_login("password123")))
        self.assertEqual(bool, type(self.dm.check_login("abc")))

    def test_get_public_table(self):
        self.assertEqual(str, type(self.dm.get_event_table()))

    def test_get_current_event(self):
        ev, desc, start, dur = self.dm.get_current_event("[a]stage0")
        self.assertEqual(str, type(ev))
        self.assertEqual(str, type(desc))
        self.assertEqual(str, type(start))
        self.assertEqual(int, type(dur))

    def test_get_next_event(self):
        ev, desc, start, dur = self.dm.get_next_event("[a]stage0")
        self.assertEqual(str, type(ev))
        self.assertEqual(str, type(desc))
        self.assertEqual(str, type(start))
        self.assertEqual(int, type(dur))

    def test_get_locations(self):
        locs = self.dm.get_locations()
        self.assertEqual(list, type(locs))
        for L in locs:
            self.assertEqual(str, type(L))


class TestDMFunction(unittest.TestCase):

    def setUp(self):
        try:
            os.mkdir("./data")
        except FileExistsError:
            pass
        cmd = ["mv", "./data", "./data_bk"]
        subprocess.call(cmd)
        import data_management as dm
        dm.load_data(table_gen_len=100, table_gen_loc_count=10)
        dm.load_data(table_gen_len=100, table_gen_loc_count=10)
        lm.CONF = {"level": "none", "log_logins": "False", "timestamp": "True"}
        self.dm = dm

    def tearDown(self):
        cmd = ["rm", "-r", "./data"]
        subprocess.call(cmd)
        cmd = ["mv", "./data_bk", "./data"]
        subprocess.call(cmd)


    def test_timestamp(self):
        ts1 = self.dm.get_timestamp()
        ts2 = self.dm.to_timestamp(datetime.now())
        self.assertTrue(ts1 == ts2)

        ts3 = self.dm.get_timestamp(add=15)
        ts4 = self.dm.shift_timestamp(ts1, 15)
        self.assertTrue(ts3 == ts4)

        dt_op1 = datetime.now()
        dt_op2 = self.dm.from_timestamp(self.dm.get_timestamp())
        self.assertTrue(dt_op1-dt_op2 <= timedelta(minutes=1))


    def test_load_data(self):
        # check correct num of locations generated
        self.assertEqual(10, len(self.dm.get_locations()))
        # check correct num of events generated
        self.assertEqual(100, len(self.dm.df_events))
        # check all event ids are unique
        self.assertEqual(100, len(self.dm.df_events["id"].unique().tolist()))

    def test_get_current_event(self):
        ev, desc, strt, dur = self.dm.get_current_event("[a]stage0")
        print(strt, dur)
        end = self.dm.shift_timestamp(strt, dur)
        # check not empty
        self.assertTrue(ev != "")
        self.assertTrue(desc != "")
        self.assertTrue(strt != "")
        self.assertTrue(dur != 0)
        # check time
        self.assertTrue(strt <= self.dm.get_timestamp())
        self.assertTrue(end >= self.dm.get_timestamp())

    def test_get_next_event(self):
        ev, desc, strt, dur = self.dm.get_next_event("[a]stage0")
        end = self.dm.shift_timestamp(strt, dur)
        # check not empty
        self.assertTrue(ev != "")
        self.assertTrue(desc != "")
        self.assertTrue(strt != "")
        self.assertTrue(dur != 0)
        # check time
        self.assertTrue(strt >= self.dm.get_timestamp())

    def test_edit_event(self):
        id = self.dm.df_events["id"].unique().tolist()[0]
        self.dm.edit_event(id, "TEST_NAME", "TEST_DESCRIPTION", "TEST_TYPE", "TEST_START", 420, "TEST_LOCATION")
        df = self.dm.df_prefab
        # check has edited once
        self.assertTrue(len(df[df["event"] == "TEST_NAME"]) == 1)
        self.assertTrue(len(df[df["description"] == "TEST_DESCRIPTION"]) == 1)
        self.assertTrue(len(df[df["type"] == "TEST_TYPE"]) == 1)
        self.assertTrue(len(df[df["start"] == "TEST_START"]) == 1)
        self.assertTrue(len(df[df["duration"] == 420]) == 1)
        self.assertTrue(len(df[df["location"] == "TEST_LOCATION"]) == 1)
        # check has edited correct
        index = df.loc[df["id"] == id].index[0]
        _, name, desc, type, start, duration, location = df.iloc[int(index)]
        self.assertEqual("TEST_NAME", name)
        self.assertEqual("TEST_DESCRIPTION", desc)
        self.assertEqual("TEST_TYPE", type)
        self.assertEqual("TEST_START", start)
        self.assertEqual("TEST_LOCATION", location)
        self.assertEqual(420, duration)

    def test_delete_event(self):
        id = self.dm.df_events["id"].unique().tolist()[0]
        self.dm.delete_event(id)
        df = self.dm.df_prefab
        # check id deleted
        self.assertTrue(len(df[df["id"] == id]) == 0)
        # check length reduced by one
        self.assertTrue(len(self.dm.df_events)-1 == len(self.dm.df_prefab))

    def test_add_event(self):
        id = self.dm.add_event("TEST_NAME", "TEST_DESCRIPTION", "TEST_TYPE", "TEST_START", 420, "TEST_LOCATION")
        df = self.dm.df_prefab
        # check lenght extended by one
        self.assertTrue(len(self.dm.df_events)+1 == len(self.dm.df_prefab))
        # check id added and unique
        self.assertTrue(len(df[df["id"] == id]) == 1)

    def test_reset_prefab(self):
        id = self.dm.add_event("TEST_NAME", "TEST_DESCRIPTION", "TEST_TYPE", "TEST_START", 420, "TEST_LOCATION")
        self.dm.reset_prefab()

        self.assertTrue(self.dm.df_events.equals(self.dm.df_prefab))
        self.assertEqual(100, len(self.dm.df_prefab))

    def test_update_event(self):
        id = self.dm.add_event("TEST_NAME", "TEST_DESCRIPTION", "TEST_TYPE", "TEST_START", 420, "TEST_LOCATION")
        self.dm.update_table()

        self.assertTrue(self.dm.df_events.equals(self.dm.df_prefab))
        self.assertEqual(101, len(self.dm.df_events))



