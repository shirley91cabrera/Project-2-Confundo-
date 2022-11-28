# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

from enum import Enum
import socket
import sys
import time
# from random import randrange

from .common import *
from .packet import Packet
from .cwnd_control import CwndControl
from .util import *

class State(Enum):
    INVALID = 0
    SYN = 1
    OPEN = 3
    LISTEN = 4
    FIN = 10
    FIN_WAIT = 11
    CLOSED = 20
    ERROR = 21

# class TimeoutError:
#     pass

class Socket:
    '''Incomplete socket abstraction for Confundo protocol'''

    def __init__(self, connId=0, inSeq=None, synReceived=False, sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM), noClose=False):
        self.sock = sock
        self.connId = connId
        self.sock.settimeout(RETX_TIME)
        self.timeout = GLOBAL_TIMEOUT

        self.base = MAX_SEQNO # Last packet from this side that has been ACKå'd
        self.seqNum = self.base  # Self explanatory

        self.inSeq = inSeq # bytes received from other side / serves as a ACK to be sent

        self.lastAckTime = time.time() # last time ACK was sent / activity timer
        self.cc = CwndControl()
        self.outBuffer = b""
        self.inBuffer = b""
        self.state = State.INVALID
        self.nDupAcks = 0

        self.synReceived = synReceived
        self.finReceived = False

        self.remote = None
        self.noClose = noClose

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.state == State.OPEN:
            self.close()
        if self.noClose:
            return
        self.sock.close()

    def connect(self, endpoint):
        remote = socket.getaddrinfo(endpoint[0], endpoint[1], family=socket.AF_INET, type=socket.SOCK_DGRAM)
        (family, type, proto, canonname, sockaddr) = remote[0]

        return self._connect(sockaddr)

    def bind(self, endpoint):
        if self.state != State.INVALID:
            raise RuntimeError()

        remote = socket.getaddrinfo(endpoint[0], endpoint[1], family=socket.AF_INET, type=socket.SOCK_DGRAM)
        (family, type, proto, canonname, sockaddr) = remote[0]

        self.sock.bind(sockaddr)
        self.state = State.LISTEN

    def listen(self, queue):
        if self.state != State.LISTEN:
            raise RuntimeError("Cannot listen")
        pass

    def accept(self):
        if self.state != State.LISTEN:
            raise RuntimeError("Cannot accept")

        hadNewConnId = True
        while True:
            # just wait forever until a new connection arrives

            if hadNewConnId:
                self.connId += 1 # use it for counting incoming connections, no other uses really
                hadNewConnId = False
            pkt = self._recv()
            if pkt and pkt.isSyn:
                hadNewConnId = True
                clientSock = Socket(connId = self.connId, synReceived=True, sock=self.sock, inSeq=self.inSeq, noClose=True)
                # at this point, syn was received, ack for syn was sent, now need to send our SYN and wait for ACK
                clientSock._connect(self.lastFromAddr)
                return clientSock

    def settimeout(self, timeout):
        self.timeout = timeout

    def _send(self, packet):
        '''"Private" method to send packet out'''

        # delay = randrange(2)

        # if delay == 0:
        #     time.sleep(1)

        if self.remote:
            self.sock.sendto(packet.encode(), self.remote)
        else:
            self.sock.sendto(packet.encode(), self.lastFromAddr)
        print(format_line("SEND", packet, self.cc.cwnd, self.cc.ssthresh))

    def _recv(self):
        '''"Private" method to receive incoming packets'''

        try:
            (inPacket, self.lastFromAddr) = self.sock.recvfrom(MAX_PKT_SIZE)
        except socket.error as e:
            return None

        inPkt = Packet().decode(inPacket)
        print(format_line("RECV", inPkt, self.cc.cwnd, self.cc.ssthresh))


        outPkt = None
        if inPkt.isSyn: 
            self.inSeq = increaseSeqNumber(inPkt.seqNum, 1)
            if inPkt.connId != 0:
                self.connId = inPkt.connId
            self.synReceived = True
            outPkt = Packet(seqNum=self.seqNum, ackNum=self.inSeq, connId=self.connId, isAck=True)

        elif inPkt.isFin:
            if self.inSeq == inPkt.seqNum: # all previous packets has been received, so safe to advance
                self.inSeq = increaseSeqNumber(self.inSeq, 1)
                self.finReceived = True
            else:
                # don't advance, which means we will send a duplicate ACK
                pass

            outPkt = Packet(seqNum=self.seqNum, ackNum=self.inSeq, connId=self.connId, isAck=True)

        elif len(inPkt.payload) > 0:
            if not self.synReceived:
                raise RuntimeError("Receiving data before SYN received")

            if self.finReceived:
                raise RuntimeError("Received data after getting FIN (incoming connection closed)")

            if self.inSeq == inPkt.seqNum: # all previous packets has been received, so safe to advance
                self.inSeq = increaseSeqNumber(self.inSeq, len(inPkt.payload))
                self.inBuffer += inPkt.payload
            else:
                # don't advance, which means we will send a duplicate ACK
                pass

            outPkt = Packet(seqNum=self.seqNum, ackNum=self.inSeq, connId=self.connId, isAck=True)

        if outPkt:
            self._send(outPkt)
            
        return inPkt

    def _connect(self, remote):
        self.remote = remote

        if self.state != State.INVALID:
            raise RuntimeError("Trying to connect, but socket is already opened")

        self.sendSynPacket()
        self.state = State.SYN

        self.expectSynAck()

    def close(self):
        if self.state != State.OPEN:
            raise RuntimeError("Trying to send FIN, but socket is not in OPEN state")

        self.sendFinPacket()
        self.state = State.FIN

        self.expectFinAck()

    def sendSynPacket(self):
        synPkt = Packet(seqNum = self.seqNum, connId= self.connId, isSyn = True)
        self.seqNum = increaseSeqNumber(self.seqNum, 1)
        self._send(synPkt)

    def expectSynAck(self):
        startTime = time.time()        
        while True:
            pkt = self._recv()
            if pkt and pkt.isAck and pkt.ackNum == self.seqNum:
                self.base = self.seqNum
                self.state = State.OPEN
            if self.synReceived and self.state == State.OPEN:
                break
            if time.time() - startTime > GLOBAL_TIMEOUT:
                self.state = State.ERROR
                raise RuntimeError("timeout")

    def sendFinPacket(self):
        synPkt = Packet(seqNum=self.seqNum, connId=self.connId, isFin=True)
        self.seqNum = increaseSeqNumber(self.seqNum, 1)
        self._send(synPkt)

    def expectFinAck(self):
        startTime = time.time()
        finWaitTime = None
        while True:
            pkt = self._recv()
            if pkt and pkt.isAck and pkt.ackNum == self.seqNum:
                self.base = self.seqNum
                finWaitTime = time.time()

            if time.time() - startTime > GLOBAL_TIMEOUT:
                self.state = State.ERROR
                raise RuntimeError("timeout")

            if finWaitTime and time.time() - finWaitTime > FIN_WAIT_TIME:
                self.state = State.CLOSED
                return

    def recv(self, maxSize):
        startTime = time.time()
        while len(self.inBuffer) == 0:
            self._recv()
            if self.finReceived:
                return None
            if time.time() - startTime > GLOBAL_TIMEOUT:
                self.state = State.ERROR
                raise RuntimeError("timeout")

        if len(self.inBuffer) > 0:
            actualResponseSize = min(len(self.inBuffer), maxSize)
            response = self.inBuffer[:actualResponseSize]
            self.inBuffer = self.inBuffer[actualResponseSize:]

            return response

    def _bulkSend(self, retransmit):
        if retransmit:
            self.seqNum = self.base
        data_sent = modSubtract(self.seqNum, self.base)
        # print("DEBUG: data_sent: " + str(self.seqNum) + " - " + str(self.base) + " = " + str(data_sent))
        bytes_sent = 0
        while True: 
            toSend = self.outBuffer[data_sent: data_sent + MTU]
            if (self.cc.cwnd - data_sent) < len(toSend) or len(toSend) == 0:
                return bytes_sent
            pkt = Packet(seqNum=self.seqNum, connId=self.connId, payload=toSend, isDup=retransmit)
            self.seqNum = increaseSeqNumber(self.seqNum, len(pkt.payload))
            # print("DEBUG increaseSeqNumber : " + str(self.seqNum))
            self._send(pkt)
            data_sent += len(pkt.payload)
            bytes_sent += len(pkt.payload)

        return bytes_sent


    def send(self, data):
        '''
        This is one of the methods that require fixes.  Besides the marked place where you need
        to figure out proper updates (to make basic transfer work), this method is the place
        where you should initate congestion control operations. You can either directly update cwnd, ssthresh,
        and anything else you need or use CwndControl class, up to you. There isn't any skeleton code for the
        congestion control operations. You would need to update things here and in `format_msg` calls
        in this file to properly print values.
        '''

        if self.state != State.OPEN:
            raise RuntimeError("Trying to send data, but socket is not in OPEN state")

        self.outBuffer += data
        retransmit = False
        while len(self.outBuffer) > 0:
            # print("DEBUG start round : " + str(self.seqNum) + " " + str(retransmit))
            bytes_sent = self._bulkSend(retransmit)
            # print("DEBUG bytes_sent : " + str(bytes_sent))
            if bytes_sent > 0:
                retransmit = False
                startTime = time.time()

            pkt = self._recv()  
            if pkt and pkt.isAck:
                advanceAmount = pkt.ackNum - self.base
                if advanceAmount == 0:
                    self.nDupAcks += 1
                else:
                    self.cc.on_ack()
                    startTime = time.time()
                    self.nDupAcks = 0

                self.outBuffer = self.outBuffer[advanceAmount:]
                self.base = pkt.ackNum

            if time.time() - startTime > GLOBAL_TIMEOUT:
                self.state = State.ERROR
                raise RuntimeError("timeout")

            if time.time() - startTime > RETX_TIME: # if within RTO we didn't receive packets, things will be retransmitted
                self.cc.on_timeout()
                retransmit = True

        return len(data)
