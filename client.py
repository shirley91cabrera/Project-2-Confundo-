#!/usr/bin/env python3

import argparse
import os
import sys

import confundo

parser = argparse.ArgumentParser("Parser")
parser.add_argument("host", help="Set Hostname")
parser.add_argument("port", help="Set Port Number", type=int)
parser.add_argument("file", help="Set File Directory")
args = parser.parse_args()


def validate_port(portNumber):
    try:
        if PortNumber < 1 or PortNumber > 65535:
            raise Exception()
        return PortNumber
    except Exception as error:
        sys.stderr.write("ERROR: This is NOT a valid port number.\n")
        sys.stderr.flush()
        sys.exit(1)

        
def sendFile(connection_socket, fileName: str):
    with open(fileName, "rb") as f:
        data = f.read(READ_BUFFER)
        while data:
            total_sent = 0
            while total_sent < len(data):
                sent = socket.send(data[total_sent:])
                total_sent += sent
            
            data = f.read(READ_BUFFER)


def start():
    try:
        with confundo.Socket() as socket:
            port = validate_port(args.port)
            socket.settimeout(GLOBAL_TIMEOUT)
            socket.connect((args.host, port))
            sendFile(socket, args.file)
                
    except Exception as error:
        sys.stderr.write(f"ERROR: {error}\n")
        sys.exit(1)


if __name__ == '__main__':
    start()
