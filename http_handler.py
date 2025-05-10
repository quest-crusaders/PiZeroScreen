from aiohttp import web, WSMsgType
import os
import json
import data_management as dm
import logging_manager as lm
import re

CLIENTS = {}
preview_list = []
layout_map = {}
location_map = {}
layouts = {
    "default": ''
}
def __load_layouts():
    global layouts, layout_map, location_map
    files = [F[:-5] for F in os.listdir("layouts") if F.endswith(".html")]
    files.sort()
    for F in files:
        html = open("layouts/"+F+".html").read()
        layouts[F] = html
    try:
        location_map = json.load(open("./data/locations.json"))
        layout_map = json.load(open("./data/layouts.json"))
    except FileNotFoundError:
        pass
__load_layouts()


def index(request):
    return web.Response(text=open("base.html").read(), content_type='text/html')

def css(request):
    file = request.match_info.get('file', "custom")
    return web.Response(text=open("css/"+file+".css").read(), content_type='text/css')


async def send_data(ws):
    preview = ws in preview_list
    loc = location_map.get(CLIENTS.get(ws))
    loc_prefix = re.compile("^\\[.*]")
    lm.log("Sending Data to screen at", loc, preview)

    event, desc, start_str, duration = dm.get_current_event(loc, prefab=preview)
    my_data = {"id": "event_name", "html": event}
    await ws.send_str(json.dumps(my_data))
    my_data = {"id": "event_desc", "html": desc}
    await ws.send_str(json.dumps(my_data))
    my_data = {"id": "event_start", "html": start_str[-5:].replace("-", ":")}
    await ws.send_str(json.dumps(my_data))
    my_data = {"id": "event_len", "html": str(duration)}
    await ws.send_str(json.dumps(my_data))

    event, desc, start_str, duration = dm.get_next_event(loc, prefab=preview)
    my_data = {"id": "event_next_name", "html": event}
    await ws.send_str(json.dumps(my_data))
    my_data = {"id": "event_next_desc", "html": desc}
    await ws.send_str(json.dumps(my_data))
    my_data = {"id": "event_next_start", "html": start_str[-5:].replace("-", ":")}
    await ws.send_str(json.dumps(my_data))
    my_data = {"id": "event_next_len", "html": str(duration)}
    await ws.send_str(json.dumps(my_data))

    my_data = {"id": "msg_of_the_day", "html": dm.msg_of_the_day}
    await ws.send_str(json.dumps(my_data))
    my_data = {"id": "location", "html": loc_prefix.sub("", loc)}
    await ws.send_str(json.dumps(my_data))

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    screen_id = ""
    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            if msg.data in ["close", "", "null"]:
                await ws.close()
                return ws
            else:
                screen_id = msg.data
                if screen_id.endswith(":preview"):
                    screen_id = screen_id[:-8]
                    preview_list.append(ws)
                CLIENTS[ws] = screen_id
                if location_map.get(screen_id) is None:
                    location_map[screen_id] = "default"
                if layout_map.get(screen_id) is None:
                    layout_map[screen_id] = "default"
                lm.log("adding screen:", msg.data, msg_type=lm.LogType.ScreenLogin)
                html = layouts.get(layout_map.get(screen_id, "default"))
                my_data = {"id": "body", "html": html}
                await ws.send_str(json.dumps(my_data))
                await send_data(ws)
    if screen_id != "":
        lm.log('connection closed:', msg.data, msg_type=lm.LogType.ScreenLogin)
    try:
        del CLIENTS[ws]
    except KeyError:
        pass
    try:
        preview_list.remove(screen_id)
    except ValueError:
        pass
    return ws
