import asyncio
import subprocess
import aiohttp
import json
from threading import Thread


class TestScreen(object):

    def __init__(self, socket_url, mac):
        self.socket_url = socket_url
        self.mac = mac
        self.data = {}
        self.ws = None
        self.loop = None
        self.thread = None

    def run_thread(self):
        async def loop():
            session = aiohttp.ClientSession()
            async with session.ws_connect(self.socket_url) as ws:
                self.ws = ws
                await ws.send_str(self.mac)
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        json_msg = json.loads(msg.data)
                        self.data[json_msg["id"]] = json_msg["html"]
            self.ws = None
            await session.close()

        self.loop = asyncio.EventLoop()
        self.loop.run_until_complete(loop())
        self.loop.close()
        self.loop = None

    def run(self):
        self.thread = Thread(target=self.run_thread)
        self.thread.daemon = True
        self.thread.start()

    def close(self):
        if self.ws is not None:
            asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)
        if self.thread is not None:
            self.thread.join()



class TestBench(object):

    def __init__(self):
        self.cmd = ["python", "./main.py"]
        self.bench_proc = None

    def run(self):
        self.bench_proc = subprocess.Popen(self.cmd)

    def check(self, timeout):
        try:
            return self.bench_proc.wait(timeout)
        except subprocess.TimeoutExpired:
            return None

    def cleanup(self):
        if self.bench_proc is not None:
            self.bench_proc.terminate()
            self.bench_proc.wait()