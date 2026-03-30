from aiohttp import web, WSMsgType
import os
import json
import data_management as dm
import logging_manager as lm
import re


class LayoutConfig(object):

    current_event: bool
    next_event: bool
    locations: int
    msg_otd: bool

    def __init__(self, current_event= True, next_event=True, locations=1, msg_otd=True):
        if locations <= 0:
            raise ValueError("location Count must be positive!")
        self.current_event = current_event
        self.next_event = next_event
        self.locations = locations
        self.msg_otd = msg_otd

def layout_conf_reader(line: str) -> LayoutConfig:
    if not (line.startswith("<!-- LayoutConfig: ") and line.endswith(" -->")):
        return LayoutConfig()
    line = line[19:-4]
    parameter = line.split(";")
    conf = LayoutConfig()

    # check bool parameter
    conf.current_event = "current_event" in parameter
    conf.next_event = "next_event" in parameter
    conf.msg_otd = "msg_otd" in parameter

    # check other parameter
    for P in parameter:
        if P.startswith("locations="):
            conf.locations = int(P[10:])

    return conf

CLIENTS = {}
preview_list = []
layout_map = {}
location_map = {}
layouts = {
    "default": ''
}
layout_conf = {
    "default": LayoutConfig()
}
def __load_layouts():
    global layouts, layout_map, location_map, layout_conf
    files = [F[:-5] for F in os.listdir("layouts") if F.endswith(".html")]
    files.sort()
    for F in files:
        html = open("layouts/"+F+".html").read()
        layouts[F] = html
        layout_conf[F] = layout_conf_reader(html.split("\n")[0])
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


def get_table(request):
    file_type = request.path.split(".")[-1]
    query = request.rel_url.query
    time_filter = query.get("time")
    if time_filter not in ["no_past", "future_only"]:
        time_filter = None
    location_filter = query.get("location")
    table_getter = {
        "html": (dm.get_public_table_html, 'text/html'),
        "csv": (dm.get_public_table_csv, 'text/csv'),
    }
    table = table_getter.get(file_type, None)
    if table is None:
        raise web.HTTPNotFound()
    else :
        return web.Response(text=table[0](time_filter=time_filter, location_filter=location_filter), content_type=table[1])

async def send_data(ws):
    preview = ws in preview_list
    loc_prefix = re.compile("^\\[.*]")
    layout = layout_map.get(CLIENTS.get(ws), "default")
    conf = layout_conf.get(layout)
    for li in range(conf.locations):
        loc = location_map.get(CLIENTS.get(ws))[li]
        lm.log("Sending Data to screen at", loc, preview)
        suffix = ""
        if li > 0:
            suffix = "_" + str(li)

        if conf.current_event:
            event, desc, start_str, duration = dm.get_current_event(loc, prefab=preview)
            if duration is not None:
                my_data = {"id": "event_name"+suffix, "html": event}
                await ws.send_str(json.dumps(my_data))
                my_data = {"id": "event_desc"+suffix, "html": desc}
                await ws.send_str(json.dumps(my_data))
                my_data = {"id": "event_start"+suffix, "html": start_str[-5:].replace("-", ":")}
                await ws.send_str(json.dumps(my_data))
                my_data = {"id": "event_end"+suffix, "html": dm.shift_timestamp(start_str, duration)[-5:].replace("-", ":")}
                await ws.send_str(json.dumps(my_data))
                my_data = {"id": "event_len"+suffix, "html": str(duration)}
                await ws.send_str(json.dumps(my_data))
        if conf.next_event:
            event, desc, start_str, duration = dm.get_next_event(loc, prefab=preview)
            if duration is not None:
                my_data = {"id": "event_next_name"+suffix, "html": event}
                await ws.send_str(json.dumps(my_data))
                my_data = {"id": "event_next_desc"+suffix, "html": desc}
                await ws.send_str(json.dumps(my_data))
                my_data = {"id": "event_next_start"+suffix, "html": start_str[-5:].replace("-", ":")}
                await ws.send_str(json.dumps(my_data))
                my_data = {"id": "event_next_end"+suffix, "html": dm.shift_timestamp(start_str, int(duration))[-5:].replace("-", ":")}
                await ws.send_str(json.dumps(my_data))
                my_data = {"id": "event_next_len"+suffix, "html": str(duration)}
                await ws.send_str(json.dumps(my_data))
        my_data = {"id": "location"+suffix, "html": loc_prefix.sub("", loc)}
        await ws.send_str(json.dumps(my_data))
    if conf.msg_otd:
        my_data = {"id": "msg_of_the_day", "html": dm.msg_of_the_day}
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
                    location_map[screen_id] = ["default"]
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
