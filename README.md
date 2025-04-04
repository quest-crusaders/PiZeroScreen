#PiZeroScreen

This Python3 Software is ment to control multiple Info-Screens.
Each Screen itself being plugged into a Raspberry PiZero2W with a browser as Frontend.

**Requirements:**
-
Needed:
- Python 3.13 or higher
- all Python-Modules as listed in requirements.txt

Recommended:
- A Reverse proxy like Caddy or Nginx for https

**Install and Run:**
-

- first clone or download the repository.
- enter the directory
  ```
  cd PiZeroScreen
  ```
- create and activate a new venv
  ```
  python -m venv ./venv
  source ./venv/bin/activate
  ```
- install the required Python-Modules
  ```
  python -m pip install requirements.txt
  ```
- run the Software to create the file
  ```
  python main.py
  ```
- stop the Software and edit the Config to your needs
  ```
  nano ./data/config.ini
  ```

After that you can start the Software with:
```
source ./venv/bin/activate
python main.py
```

**Configuration**
-
The Configfile is found in ```./data/config.ini``` and consists of following blocks:

**admin**
The Admin block hold only one Parameter, witch sets the Password for the Admin panel
```
[admin]
password = password123
```

**server**
The Server block holds the Hostname and Port for the http-Server.
```
[server]
host = 127.0.0.1
port = 8080
```

**post_api**
This Block is optional and used to post all Database changes to a Server.

The post data is a Json with 3 named elements:
- id: an identifier String read from the config used to handle multiple instances posting to one Server
- message: The Message of the Day String as set in the Admin-Control-panel
- data: a String containing the complete Timetable in CSV formating

The Config-Block can set the URL at witch to post, as well as the id-String to pass.
```
[post_api]
id = test
url = your url
```
