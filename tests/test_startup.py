import unittest
import time
import subprocess
import os
import requests

import data_management as dm


class TestBench(object):

    def __init__(self):
        self.cmd = ["python", "./main.py"]

    def run(self):
        self.bench_proc = subprocess.Popen(self.cmd)

    def check(self, timeout):
        try:
            return self.bench_proc.wait(timeout)
        except subprocess.TimeoutExpired:
            return None

    def cleanup(self):
        self.bench_proc.terminate()
        self.bench_proc.wait()





class TestStartup(unittest.TestCase):

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


    def test_startup(self):
        self.bench.run()
        self.assertEqual(None, self.bench.check(10))

    def test_webserver_responds(self):
        self.bench.run()
        time.sleep(3)
        resp = requests.get("http://127.0.0.1:8080/").status_code
        self.assertEqual(200, resp)

    def test_webserver_auth_blocking(self):
        self.bench.run()
        time.sleep(3)
        resp = requests.get("http://127.0.0.1:8080/admin/time_table").status_code
        self.assertEqual(401, resp)



