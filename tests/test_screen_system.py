import unittest
import os
import subprocess
import time
import configparser
import requests

import data_management as dm
from tests.testbench import TestBench, TestScreen


def prep_tstamp(tstamp):
    return tstamp[-5:].replace("-", ":")


class TestScreenSystem(unittest.TestCase):

    def setUp(self):
        try:
            os.mkdir("./data")
        except FileExistsError:
            pass
        cmd = ["mv", "./data", "./data_bk"]
        subprocess.call(cmd)
        dm.load_data()
        self.bench = TestBench()

    def tearDown(self):
        cmd = ["rm", "-r", "./data"]
        subprocess.call(cmd)
        cmd = ["mv", "./data_bk", "./data"]
        subprocess.call(cmd)
        self.bench.cleanup()


    def test_get_resources(self):
        self.bench.run()
        time.sleep(3)

        resp = requests.get("http://127.0.0.1:8080/?mac=unittest")
        self.assertEqual(200, resp.status_code)
        with open("./base.html", "br") as f:
            self.assertEqual(f.read(), resp.content)

        for css_file in [f for f in os.listdir("./css/") if f.endswith(".css")]:
            resp = requests.get("http://127.0.0.1:8080/" + css_file)
            self.assertEqual(200, resp.status_code)
            with open("./css/" + css_file, "br") as f:
                self.assertEqual(f.read(), resp.content)

        for font_file in os.listdir("./fonts/"):
            resp = requests.get("http://127.0.0.1:8080/fonts/" + font_file)
            self.assertEqual(200, resp.status_code)
            with open("./fonts/" + font_file, "br") as f:
                self.assertEqual(f.read(), resp.content)

        for js_file in os.listdir("./js/"):
            resp = requests.get("http://127.0.0.1:8080/js/" + js_file)
            self.assertEqual(200, resp.status_code)
            with open("./js/" + js_file, "br") as f:
                self.assertEqual(f.read(), resp.content)

        for file in os.listdir("./static/"):
            resp = requests.get("http://127.0.0.1:8080/static/" + file)
            self.assertEqual(200, resp.status_code)
            with open("./static/" + file, "br") as f:
                self.assertEqual(f.read(), resp.content)

    def test_screen_system(self):
        with open("./data/config.ini") as cf:
            conf = configparser.ConfigParser()
            conf.read_file(cf)
            conf["logging"] = {"level": "none", "log_logins": "False", "timestamp": "False"}
            with open("./data/config.ini", "w") as f:
                conf.write(f)
        screen = TestScreen("ws://127.0.0.1:8080/ws", "example")
        should = {}
        with open("./layouts/example.html", "r") as f:
            should = {
                'body': f.read(),
                'event_name': 'Sample_0',
                'event_desc': 'Just an Example.',
                'event_start': prep_tstamp(dm.get_timestamp(add=-5)),
                'event_len': '30',
                'event_end': prep_tstamp(dm.get_timestamp(add=25)),
                'event_next_name': 'Sample_6',
                'event_next_desc': 'Just an Example.',
                'event_next_start': prep_tstamp(dm.get_timestamp(add=55)),
                'event_next_len': '30',
                'event_next_end': prep_tstamp(dm.get_timestamp(add=85)),
                'event_name_1': 'Break',
                'event_desc_1': 'Pleas wait for the next Event to start',
                'event_start_1': prep_tstamp(dm.get_timestamp()[:-5]+"00:00"),
                'event_len_1': str(int((dm.from_timestamp(dm.get_timestamp(add=5)) - dm.from_timestamp(dm.get_timestamp()[:-5]+"00:00")).total_seconds()//60)),
                'event_end_1': prep_tstamp(dm.get_timestamp(add=5)),
                'event_next_name_1': 'Sample_1',
                'event_next_desc_1': 'Just an Example.',
                'event_next_start_1': prep_tstamp(dm.get_timestamp(add=5)),
                'event_next_len_1': '30',
                'event_next_end_1': prep_tstamp(dm.get_timestamp(add=35)),
                'location': 'stage0',
                'location_1': 'stage1',
                'msg_of_the_day': ''
            }
        self.bench.run()
        time.sleep(3)
        screen.run()
        time.sleep(3)
        screen.close()
        self.assertEqual(len(should), len(screen.data))
        for k, v in should.items():
            self.assertEqual({k: v}, {k: screen.data[k]})

    def test_screen_autoupdate(self):
        with open("./data/config.ini") as cf:
            conf = configparser.ConfigParser()
            conf.read_file(cf)
            conf["logging"] = {"level": "none", "log_logins": "False", "timestamp": "False"}
            with open("./data/config.ini", "w") as f:
                conf.write(f)
        screen = TestScreen("ws://127.0.0.1:8080/ws", "example")
        should = {}
        with open("./layouts/example.html", "r") as f:
            should = {
                'body': f.read(),
                'event_name': 'Sample_0',
                'event_desc': 'Just an Example.',
                'event_start': prep_tstamp(dm.get_timestamp(add=-5)),
                'event_len': '30',
                'event_end': prep_tstamp(dm.get_timestamp(add=25)),
                'event_next_name': 'Sample_6',
                'event_next_desc': 'Just an Example.',
                'event_next_start': prep_tstamp(dm.get_timestamp(add=55)),
                'event_next_len': '30',
                'event_next_end': prep_tstamp(dm.get_timestamp(add=85)),
                'event_name_1': 'Sample_1',
                'event_desc_1': 'Just an Example.',
                'event_start_1': prep_tstamp(dm.get_timestamp(add=5)),
                'event_len_1': '30',
                'event_end_1': prep_tstamp(dm.get_timestamp(add=35)),
                'event_next_name_1': 'Sample_7',
                'event_next_desc_1': 'Just an Example.',
                'event_next_start_1': prep_tstamp(dm.get_timestamp(add=65)),
                'event_next_len_1': '30',
                'event_next_end_1': prep_tstamp(dm.get_timestamp(add=95)),
                'location': 'stage0',
                'location_1': 'stage1',
                'msg_of_the_day': ''
            }
        self.bench.run()
        time.sleep(3)
        screen.run()
        time.sleep(305)
        screen.close()
        self.assertEqual(len(should), len(screen.data))
        for k, v in should.items():
            self.assertEqual({k: v}, {k: screen.data[k]})





