#!/usr/bin/env python3

import sys
import argparse
import signal

import confundo

not_stopped = True

parser = argparse.ArgumentParser("Parser")
parser.add_argument("port", help="Set Port Number", type=int)
args = parser.parse_args()

def validate_port(portNumber):
    try:
        if portNumber < 1 or portNumber > 65535:
            raise Exception()
        return portNumber
    except Exception as error:
        sys.stderr.write("ERROR: This is NOT a valid port number.\n")
        sys.exit(1)

def signalHandlers(signum_, frame_):
    global not_stopped
    not_stopped = False
    exit(0)


def handleSignals():
    signal.signal(signal.SIGINT, signalHandlers)
    signal.signal(signal.SIGTERM, signalHandlers)
    signal.signal(signal.SIGQUIT, signalHandlers)


def processConnection(clientSocket):
    while True:
        try:
            message = clientSocket.recv(BUFFER_SIZE)
            clientSocket.settimeout(GLOBAL_TIMEOUT)
            if not message:
                break
        except Exception as error:
            sys.stderr.write("ERROR: Could not receive file")


def start():
    global not_stopped
    handleSignals()

    try:
        port = validate_port(args.port)
        with confundo.Socket() as server:
            server.bind(("0.0.0.0", port))

            while not_stopped:
                server.listen(10)
                with server.accept() as clientSocket:
                    processConnection(clientSocket)

    except RuntimeError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    start()
