import json
import time

from aiohttp import web
import random
from datetime import datetime
import os

import data_management as dm
import http_handler as hh
import logging_manager as lm

SESSION_KEY_LENGTH = 64

sessions = []
sus_ips = {}


def __create_session_key():
    key = "".join([random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(SESSION_KEY_LENGTH)])
    while sessions.__contains__(key):
        key = "".join([random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(SESSION_KEY_LENGTH)])
    return key

def check_auth(request):
    ip = ""
    try:
        ip = request.headers["X-Forwarded-For"]
    except KeyError:
        ip = request.remote
    ip_is_trusted = False
    if ip == "127.0.0.1":
        ip_is_trusted = True
    else:
        for t_ip in dm.config.get("admin", "trusted_ips").split(","):
            if ip.startswith(t_ip):
                ip_is_trusted = True
                break
    if not ip_is_trusted:
        return False
    if request.cookies.get("session") is None:
        return False
    if sessions.__contains__(request.cookies.get("session")):
        return True
    return False

def raise_404(file="File"):
    raise web.HTTPNotFound(reason=file + " Not Found!", text=open("404.html", "r").read(), content_type="text/html")

async def get_timetable(request):
    if not check_auth(request):
        raise_404(request.path)
    prefab = request.rel_url.query.get('prefab') == "true"
    loc = request.rel_url.query.get('loc')
    if loc == "":
        loc = None
    html = '<!DOCTYPE html>\n<link rel="stylesheet" href="/ui.css">\n' + dm.get_time_table(prefab=prefab, location=loc)
    if True:
        html += """
        <script>
            function edit(id, name, desc, type, start, duration, loc) {
                parent.document.getElementById("id").value = id;
                parent.document.getElementById("event").value = name;
                parent.document.getElementById("desc").value = desc;
                parent.document.getElementById("type").value = type;
                parent.document.getElementById("start").value = start.replaceAll("_", "T");
                parent.document.getElementById("duration").value = duration;
                parent.document.getElementById("loc").value = loc;
            }
            
            var first = true;
            for (const row of document.getElementsByTagName("tr")) {
                if (first) {
                    first = false;
                    continue;
                }
                data = [];
                for (const col of row.children) {
                    data.push(col.innerText);
                }
                let str = "";
                for (const col of data) {
                    str += '"' + col + '",'
                }
                str = str.substring(0, str.length - 1);
                row.children[0].innerHTML = "<button onclick='edit("+str+");'>EDIT</button>";
            }
        </script>
        """
    return web.Response(text=html, content_type='text/html')

async def post_edit_entry(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    data = await request.post()
    if data["id"] != "":
        start = data['start'].replace("T", "_")
        duration = int(data['duration'])
        dm.edit_event(data['id'], data['event'], data['description'], data['type'], start, duration, data['location'])
    ret = "/admin/index.html"
    if data["filter"] != "":
        ret += "?filter=" + data["filter"]
    return web.HTTPFound(ret)

async def post_add_entry(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    data = await request.post()
    if data["event"] != "":
        start = data['start'].replace("T", "_")
        duration = int(data['duration'])
        dm.add_event(data['event'], data['description'], data['type'], start, duration, data['location'])
    ret = "/admin/index.html"
    if data["filter"] != "":
        ret += "?filter=" + data["filter"]
    return web.HTTPFound(ret)

async def post_delete_entry(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    data = await request.post()
    dm.delete_event(data['id'])
    ret = "/admin/index.html"
    if data["filter"] != "":
        ret += "?filter=" + data["filter"]
    return web.HTTPFound(ret)

async def post_reset_table(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    dm.reset_prefab()
    return web.HTTPFound("/admin/index.html")

async def post_submit_table(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    dm.update_table()
    return web.HTTPFound("/admin/index.html")

async def get_screens(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    layouts = [l for l in hh.layouts.keys()]
    locations = dm.get_locations()
    screens = [s for s in hh.layout_map.keys()]

    def make_layout_opt(selected):
        map = {selected: " selected='selected'"}
        return "\n".join(["<option"+map.get(L, "")+" value='"+L+"'>"+L+"</option>" for L in layouts])
    def make_location_opt(selected):
        map = {selected: " selected='selected'"}
        return "\n".join(["<option"+map.get(L, "")+" value='"+L+"'>"+L+"</option>" for L in locations])

    html = '<!DOCTYPE html>\n<link rel="stylesheet" href="/ui.css">\n<form action="/admin/screens" method="post"><table>\n'
    for S in screens:
        html += "<tr><td>" + S + "</td>"
        html += "<td><select name='"+S+"_layout' value='"+hh.layout_map.get(S)+"'>"+make_layout_opt(hh.layout_map.get(S))+"</select></td>"
        html += "<td><select name='"+S+"_location' value='"+hh.location_map.get(S)+"'>"+make_location_opt(hh.location_map.get(S))+"</select></td>"
        html += "<td><a class='preview' href='/?mac="+S+"&preview=true' target='_blank'>preview "+S+"</a></td>"
        html += "</tr>\n"
    html += "</table>\n<label>force Update </label><input type='checkbox' name='force'><br><input type='submit' value='commit changes'></form>\n"
    html += "<form action='/admin/purge_screens' method='post'><input type='submit' value='remove disconnected'></form>\n"
    return web.Response(text=html, content_type='text/html')

async def post_purge_screens(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    lm.log("Removing disconnected screens", msg_type=lm.LogType.DataUpdated)
    _ = await request.post()
    all_screens = list(hh.layout_map.keys())
    active_screens = [s for s in hh.layout_map.keys() if hh.layout_map.get(s) in hh.CLIENTS]
    for S in all_screens:
        if S not in active_screens:
            hh.layout_map.pop(S)
            hh.location_map.pop(S)
    with open("./data/layouts.json", "w+") as f:
        f.write(json.dumps(hh.layout_map))
    with open("./data/locations.json", "w+") as f:
        f.write(json.dumps(hh.location_map))
    return web.HTTPFound("/admin/screens")

async def post_screen_layout(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    lm.log("Updating Screen Layouts", msg_type=lm.LogType.ScreenInfoUpdated)
    data = await request.post()
    screens = [s for s in hh.layout_map.keys()]
    update = []
    for S in screens:
        if data[S+"_layout"] != hh.layout_map.get(S) or data.get("force") == "on":
            hh.layout_map[S] = data[S+"_layout"]
            html = hh.layouts.get(hh.layout_map.get(S, "default"))
            my_data = {"id": "body", "html": html}
            for ws in [ws for ws in hh.CLIENTS.keys() if hh.CLIENTS.get(ws) == S]:
                await ws.send_str(json.dumps(my_data))
                if not update.__contains__(ws):
                    update.append(ws)
        if data[S+"_location"] != hh.location_map.get(S):
            hh.location_map[S] = data[S+"_location"]
            for ws in [ws for ws in hh.CLIENTS.keys() if hh.CLIENTS.get(ws) == S]:
                 if not update.__contains__(ws):
                     update.append(ws)
        for ws in update:
            await hh.send_data(ws)
    with open("./data/layouts.json", "w+") as f:
        f.write(json.dumps(hh.layout_map))
    with open("./data/locations.json", "w+") as f:
        f.write(json.dumps(hh.location_map))
    return web.HTTPFound("/admin/screens")

async def post_msg_of_the_day(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    data = await request.post()
    dm.msg_of_the_day = data["msg"]
    return web.HTTPFound("/admin/messages.html")

async def post_warning(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    data = await request.post()
    lm.log("Showing Warning:", data["msg"], msg_type=lm.LogType.SystemInfo)
    html = open("Warning.html").read().replace("[MSG]", data["msg"])
    my_data = {"id": "body", "html": html}
    for ws in hh.CLIENTS.keys():
        await ws.send_str(json.dumps(my_data))
    return web.HTTPFound("/admin/messages.html")

async def get_logs(request):
    if not check_auth(request):
        return web.Response(text="Unauthorized", status=401, content_type="text/html")
    logs = lm.MESSAGE_LOG.copy()
    html = '<!DOCTYPE html><html lang="en">\n<head>\n<meta charset="UTF-8">\n<link rel="stylesheet" href="/ui.css"></head>\n<body>\n'
    html += """
    <script>
    function filter(mclass) {
        elems = document.getElementsByClassName(mclass);
        for (var i = 0; i < elems.length; i++) {
            if (elems[i].tagName == "DIV"){
                if (document.getElementById(mclass).checked) {
                    elems[i].classList.remove("inv");
                }else {
                    elems[i].classList.add("inv");
                }
            }
        }
    }
    </script>
    """
    for mtype in lm.LogType:
        mclass = str(mtype)[8:]
        checked = ""
        if mtype in lm.LOGGING_LEVELS.get("admin_panel"):
            checked = " checked"
        html += f"<label class='log {mclass}'>{mclass}<input type='checkbox' id='{mclass}'{checked} onchange='filter(\"{mclass}\");'></label>\n"
    html += "<br><br>"
    html += "\n".join(["<div class='log "+str(mtype)[8:]+"'>"+t+" <div class='log_msg'>"+msg.replace("\n", "<br>")+"</div></div>" for t, msg, mtype in logs])
    html += "<script>\n"
    for mtype in lm.LogType:
        mclass = str(mtype)[8:]
        html += f"filter('{mclass}');\n"
    html += "</script>"
    html += "</body></html>"
    return web.Response(text=html, content_type='text/html')

async def login(request):
    query = await request.post()
    pw = query.get("pw")
    ret = "/admin/index.html"

    ip = ""
    try:
        ip = request.headers["X-Forwarded-For"]
    except KeyError:
        ip = request.remote
    ip_is_trusted = False
    if ip == "127.0.0.1":
        ip_is_trusted = True
    else:
        for t_ip in dm.config.get("admin", "trusted_ips").split(","):
            if ip.startswith(t_ip):
                ip_is_trusted = True
                break
    if not ip_is_trusted:
        lm.log("IP blocked (not in Whitelist) login from", ip, msg_type=lm.LogType.Login)
        resp = web.Response(text="IP address is not trusted!", status=401, content_type="text/html")
        resp.cookies["session"] = ""
        return resp
    if sus_ips.get(ip) is not None:
        count, tstamp = sus_ips.get(ip)
        t = min((3**max(0, count-2))-1, 60) - (datetime.now().timestamp() - tstamp)
        if t > 0:
            lm.log("IP blocked (too many trys) login from", ip, msg_type=lm.LogType.Login)
            resp = web.Response(text="To many login requests, try later", status=429, content_type="text/html")
            resp.cookies["session"] = ""
            return resp
        else:
            sus_ips[ip] = (count+1, datetime.now().timestamp())
    else:
        sus_ips[ip] = (1, datetime.now().timestamp())

    if dm.check_login(pw):
        sus_ips.pop(ip)
        resp = web.HTTPFound(ret)
        cookie = __create_session_key()
        resp.cookies["session"] = cookie
        sessions.append(cookie)
        lm.log("Successfull login from", ip, msg_type=lm.LogType.Login)
        return resp
    else:
        lm.log("Failed login from", ip, msg_type=lm.LogType.Login)
        resp = web.Response(text="Wrong Password!", status=401, content_type="text/html")
        resp.cookies["session"] = ""
        return resp

async def logout(request):
    resp = web.HTTPFound("/admin")
    cookie = request.cookies.get("session")
    resp.cookies["session"] = ""
    try:
        sessions.remove(cookie)
    except ValueError:
        pass
    return resp

def get_login(request):
    if check_auth(request):
        raise web.HTTPFound("/admin/index.html")
    return web.Response(text=open("login.html", "r").read(), content_type='text/html')

async def get_admin_page(request: web.Request):
    if not check_auth(request):
        raise_404(request.path)
    file = request.match_info.get('file', "index")
    if not os.path.exists("./admin/"+file+".html"):
        raise_404(file)
    return web.Response(text=open("./admin/"+file+".html").read(), content_type='text/html')
