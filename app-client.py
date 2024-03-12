# Date:         18 February 2024
# Assignment:   Microservices Client
# Description:  create a microservices test client for use with getMetar requests
#               this file is a modified from an example file from Real Python - not original work

#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback

import libclient

sel = selectors.DefaultSelector()


def create_request(action, airport, hoursBefore):
    """
    create request to be sent to server via json or bianry
    :param action:       (str)      - action to be taken by server
    :param airport:      (str)      - ICAO identifer for airport
    :param hoursBefore:  (int, opt) - number of hours before if not requesting the current metar
    :return: (dict)
    """
    # for this application, the only action recognized is "metar" request
    if action == "metar":
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, value1=airport, value2=hoursBefore),
        )
    # if a different action is requested, then a sample of the input is sent back as binary
    else:
        return dict(
            type="binary/custom-client-binary-type",
            encoding="binary",
            content=bytes(action + airport + hoursBefore, encoding="utf-8"),
        )


def start_connection(host, port, request):
    """
    function ot open connection to server and send request
    :param host:
    :param port:
    :param request:
    :return:
    """
    addr = (host, port)
    print(f"Starting connection to {addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = libclient.Message(sel, sock, addr, request)
    sel.register(sock, events, data=message)

# handle incorrect input format passed to the function via CLI and offer useful hint
if len(sys.argv) != 5 and len(sys.argv) != 6:
    print(f"Usage: {sys.argv[0]} <host> <port> <action> <value1> <value2(opt)>")
    sys.exit(1)

# define the host and port for the socket
host, port = sys.argv[1], int(sys.argv[2])

# handle values if one one input (no "hoursBefore" input)
if len(sys.argv) == 5:
    action, value1 = sys.argv[3], sys.argv[4]
    value2 = 0
# handle values if two inputs
else:
    action, value1, value2 = sys.argv[3], sys.argv[4], sys.argv[5]

# bundle the request in json format
request = create_request(action, value1, value2)
# send the request
start_connection(host, port, request)

# listen for a response
try:
    while True:
        events = sel.select(timeout=1)
        for key, mask in events:
            message = key.data
            try:
                message.process_events(mask)
            except Exception:
                print(
                    f"Main: Error: Exception for {message.addr}:\n"
                    f"{traceback.format_exc()}"
                )
                message.close()
        # Check for a socket being monitored to continue.
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()