from aiohttp import web, WSMsgType
import os
import json
import data_management as dm
import logging_manager as lm

CLIENTS = {}
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
    loc = location_map.get(CLIENTS.get(ws))

    event, desc, _, _ = dm.get_current_event(loc)
    my_data = {"id": "event_name", "html": event}
    await ws.send_str(json.dumps(my_data))
    my_data = {"id": "event_desc", "html": desc}
    await ws.send_str(json.dumps(my_data))

    event, desc, start_str, _ = dm.get_next_event(loc)
    html = '<h3>'+event+'</h3>\n'
    html += '<p>Starting at: ' + start_str[-5:].replace("-", ":") + '</p>\n'
    my_data = {"id": "event_next", "html": html}
    await ws.send_str(json.dumps(my_data))

    my_data = {"id": "msg_of_the_day", "html": dm.msg_of_the_day}
    await ws.send_str(json.dumps(my_data))

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    screen_id = ""
    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            lm.log("adding screen:", msg.data, msg_type=lm.LogType.ScreenLogin)
            if msg.data == 'close':
                await ws.close()
            else:
                screen_id = msg.data
                CLIENTS[ws] = screen_id
                if screen_id != "null":
                    if location_map.get(screen_id) is None:
                        location_map[screen_id] = "default"
                    if layout_map.get(screen_id) is None:
                        layout_map[screen_id] = "default"
                html = layouts.get(layout_map.get(screen_id, "default"))
                my_data = {"id": "body", "html": html}
                await ws.send_str(json.dumps(my_data))
                await send_data(ws)
    if screen_id != "":
        lm.log('connection closed:', screen_id, msg_type=lm.LogType.ScreenLogin)
    try:
        del CLIENTS[ws]
    except KeyError:
        pass
    return ws
