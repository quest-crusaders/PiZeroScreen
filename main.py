from aiohttp import web
import asyncio
import json
from time import sleep
from threading import Thread

import data_management as dm
import http_handler as hh
import admin_handler as ah

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
                web.get("/admin/screens", ah.get_screens),
                web.get("/admin", ah.get_login),
                web.get("/admin/time_table", ah.get_timetable),
                web.get("/admin/{file:.*}.html", ah.get_admin_page)
])

def data_update_loop():
    global LOOP
    loop_count = 0
    sleep(5)
    current_events = {}
    next_events = {}
    for L in dm.get_locations():
        current_events[L] = [dm.get_current_event(L)]
        next_events[L] = dm.get_next_event(L)
    while True:
        loop_count += 1
        sleep(10)
        if LOOP is None:
            continue
        for L in dm.get_locations():
            current_event = current_events.get(L)
            next_event = next_events.get(L)
            if current_event != dm.get_current_event(L):
                print("Update current event")
                current_event = dm.get_current_event(L)
                current_events[L] = current_event
                for ws in hh.CLIENTS:
                    if hh.location_map.get(hh.CLIENTS.get(ws)) != L:
                        continue
                    event, desc, _ = current_event
                    my_data = {"id": "event_name", "html": event}
                    asyncio.run_coroutine_threadsafe(ws.send_str(json.dumps(my_data)), LOOP)
                    my_data = {"id": "event_desc", "html": desc}
                    asyncio.run_coroutine_threadsafe(ws.send_str(json.dumps(my_data)), LOOP)
            if next_event != dm.get_next_event(L):
                print("Update next event")
                next_event = dm.get_next_event(L)
                next_events[L] = next_event
                for ws in hh.CLIENTS:
                    if hh.location_map.get(hh.CLIENTS.get(ws)) != L:
                        continue
                    event, desc, start_str = next_event
                    html = '<h3>' + event + '</h3>\n'
                    html += '<p>Starting at: ' + start_str[-5:].replace("-", ":") + '</p>\n'
                    my_data = {"id": "event_next", "html": html}
                    asyncio.run_coroutine_threadsafe(ws.send_str(json.dumps(my_data)), LOOP)


if __name__ == '__main__':
    print("STARTED AT:", dm.get_timestamp())
    update_thread = Thread(target=data_update_loop)
    update_thread.daemon = True
    update_thread.start()
    web.run_app(app, port=int(dm.config.get("server", "port")), host=dm.config.get("server", "host"))
