import requests
from aiohttp import web
import asyncio
import json
from time import sleep
from threading import Thread

import data_management as dm
import http_handler as hh
import admin_handler as ah
import logging_manager as lm

import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)


async def loop_graper(request):
    global LOOP
    LOOP = asyncio.get_running_loop()
    return hh.index(request)


LOOP = None
app = web.Application()
app.add_routes([
                web.get('/', loop_graper),
                web.get('/{file}.css', hh.css),
                web.static('/fonts/', './fonts/'),
                web.static('/static/', './static/'),
                web.get('/ws', hh.websocket_handler),

                web.post("/login", ah.login),
                web.post("/admin/add_event", ah.post_add_entry),
                web.post("/admin/edit_event", ah.post_edit_entry),
                web.post("/admin/delete_event", ah.post_delete_entry),
                web.post("/admin/reset_table", ah.post_reset_table),
                web.post("/admin/submit_table", ah.post_submit_table),
                web.post("/admin/screens", ah.post_screen_layout),
                web.post("/admin/warning", ah.post_warning),
                web.post("/admin/msg_of_the_day", ah.post_msg_of_the_day),
                web.post("/admin/purge_screens", ah.post_purge_screens),
                web.get("/admin/logs", ah.get_logs),
                web.get("/admin/screens", ah.get_screens),
                web.get("/admin", ah.get_login),
                web.get("/admin/logout", ah.logout),
                web.get("/admin/time_table", ah.get_timetable),
                web.get("/admin/{file:.*}.html", ah.get_admin_page)
])

def data_update_loop():
    global LOOP
    loop_count = 0
    sleep(5)
    current_events = {}
    next_events = {}
    msg_of_the_day = dm.msg_of_the_day
    for L in dm.get_locations():
        current_events[L] = [dm.get_current_event(L)]
        next_events[L] = dm.get_next_event(L)
    while True:
        loop_count += 1
        sleep(1)
        if LOOP is None:
            requests.get("http://" + dm.config.get("server", "host") + ":" + dm.config.get("server", "port"))
            continue
        if msg_of_the_day != dm.msg_of_the_day:
            lm.log("Updating Screens Message", msg_type=lm.LogType.ScreenInfoUpdated)
            msg_of_the_day = dm.msg_of_the_day
            my_data = {"id": "msg_of_the_day", "html": msg_of_the_day}
            for ws in hh.CLIENTS:
                asyncio.run_coroutine_threadsafe(ws.send_str(json.dumps(my_data)), LOOP)
        for L in dm.get_locations():
            current_event = current_events.get(L)
            next_event = next_events.get(L)
            update = []
            if current_event != dm.get_current_event(L):
                current_event = dm.get_current_event(L)
                current_events[L] = current_event
                for ws in hh.CLIENTS:
                    if hh.location_map.get(hh.CLIENTS.get(ws)) != L:
                        continue
                    if not update.__contains__(ws):
                        update.append(ws)
            if next_event != dm.get_next_event(L):
                next_event = dm.get_next_event(L)
                next_events[L] = next_event
                for ws in hh.CLIENTS:
                    if hh.location_map.get(hh.CLIENTS.get(ws)) != L:
                        continue
                    if not update.__contains__(ws):
                        update.append(ws)
            if len(update) > 0:
                lm.log("Updating Screens at", L, msg_type=lm.LogType.ScreenInfoUpdated)
            for ws in update:
                asyncio.run_coroutine_threadsafe(hh.send_data(ws), LOOP)


if __name__ == '__main__':
    admin_url = "http://" + dm.config.get("server", "host") + ":" + dm.config.get("server", "port") + "/admin"
    lm.log("STARTED AT:", dm.get_timestamp(), msg_type=lm.LogType.SystemInfo)
    lm.log("Visit Admin Panel at:", admin_url, msg_type=lm.LogType.SystemInfo)
    update_thread = Thread(target=data_update_loop)
    update_thread.daemon = True
    update_thread.start()
    web.run_app(app, port=int(dm.config.get("server", "port")), host=dm.config.get("server", "host"))
