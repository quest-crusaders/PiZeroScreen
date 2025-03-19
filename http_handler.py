from aiohttp import web, WSMsgType
import os
import json
import data_management as dm

CLIENTS = {}
layout_map = {}
location_map = {}
layouts = {
    "default": ''
}
def __load_layouts():
    files = [F[:-5] for F in os.listdir("layouts") if F.endswith(".html")]
    files.sort()
    for F in files:
        html = open("layouts/"+F+".html").read()
        layouts[F] = html
__load_layouts()


def index(request):
    return web.Response(text=open("base.html").read(), content_type='text/html')

def css(request):
    file = request.match_info.get('file', "custom")
    return web.Response(text=open("css/"+file+".css").read(), content_type='text/css')


async def send_data(ws):
    loc = location_map.get(CLIENTS.get(ws))

    event, desc, _ = dm.get_current_event(loc)
    my_data = {"id": "event_name", "html": event}
    await ws.send_str(json.dumps(my_data))
    my_data = {"id": "event_desc", "html": desc}
    await ws.send_str(json.dumps(my_data))

    event, desc, start_str = dm.get_next_event(loc)
    html = '<h3>'+event+'</h3>\n'
    html += '<p>Starting at: ' + start_str[-5:].replace("-", ":") + '</p>\n'
    my_data = {"id": "event_next", "html": html}
    await ws.send_str(json.dumps(my_data))

async def websocket_handler(request):
    print('Websocket connection starting')
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print('Websocket connection ready')

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            print("adding:", msg.data)
            CLIENTS[ws] = msg.data
            if msg.data == 'close':
                await ws.close()
            else:
                if msg.data != "null":
                    if location_map.get(msg.data) is None:
                        location_map[msg.data] = "default"
                    if layout_map.get(msg.data) is None:
                        layout_map[msg.data] = "default"
                        print("reset", msg.data)
                html = layouts.get(layout_map.get(msg.data, "default"))
                my_data = {"id": "body", "html": html}
                await ws.send_str(json.dumps(my_data))
                await send_data(ws)
    #CLIENTS.pop(ws)  # Throws a key error?
    print('Websocket connection closed')
    del CLIENTS[ws]
    return ws
