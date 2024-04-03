from __future__ import annotations
import os
import time
import socket
import atexit
from threading import Thread, Event
import signal

from modules import timer
from modules import initialize_util
from modules import initialize
from modules_forge.initialization import initialize_forge
from modules_forge import main_thread
from utils import application


from uvicorn import Config, Server
import asyncio


startup_timer = timer.startup_timer
startup_timer.record("launcher")

initialize_forge()
initialize.imports()
initialize.check_versions()
initialize.initialize()

shutdown_event = Event()

def create_api(app):
    from modules.api.api import Api
    from modules.call_queue import queue_lock

    api = Api(app, queue_lock)
    return api

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(starting_port):
    port = starting_port
    while is_port_in_use(port):
        print(f"Port {port} is in use, trying next one.")
        port += 1
    return port

async def api_only_worker(shutdown_event: Event):
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()

    app = FastAPI()
    initialize_util.setup_middleware(app)
    api = create_api(app)

    from modules import script_callbacks
    script_callbacks.before_ui_callback()
    script_callbacks.app_started_callback(None, app)

    print(f"Startup time: {startup_timer.summary()}.")

    starting_port = 7861
    port = find_available_port(starting_port)

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=port)

    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    config = uvicorn.Config(app=app, host="127.0.0.1", port={port}, log_level="info")
    server = uvicorn.Server(config=config)

    loop = asyncio.get_event_loop()
    loop.create_task(server.serve())
    
    application.start(f"http://127.0.0.1:{port}")

    shutdown_event.set()
    
    await os.kill(os.getpid(), signal.SIGTERM)

def api_only():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(api_only_worker(shutdown_event))

def on_exit():
    print("Cleaning up...")
    shutdown_event.set()

if __name__ == "__main__":
    atexit.register(on_exit)
    api_only()
    main_thread.loop()