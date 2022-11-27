from .common import *

MOD = (MAX_SEQNO + 1)

def format_line(command, pkt, cwnd, ssthresh):
    s = f"{command} {pkt.seqNum} {pkt.ackNum} {pkt.connId} {int(cwnd)} {ssthresh}"
    if pkt.isAck: s = s + " ACK"
    if pkt.isSyn: s = s + " SYN"
    if pkt.isFin: s = s + " FIN"
    if pkt.isDup: s = s + " DUP"
    return s


def increaseSeqNumber(seqNumber, bytes):
    return (seqNumber + bytes) % MOD


def modSubtract(a, b):
    return (MOD + (a - b)) % MOD
