# CNT-4731 Project 2 (Confundo)

Template for for FIU CNT-4731 Fall 2021 Project 2

## Provided Files

`server.py` and `client.py` are the entry points for the server and client part of the project.

## Academic Integrity Note

You are encouraged to host your code in private repositories on [GitHub](https://github.com/), [GitLab](https://gitlab.com), or other places.  At the same time, you are PROHIBITED to make your code for the class project public during the class or any time after the class.  If you do so, you will be violating academic honestly policy that you have signed, as well as the student code of conduct and be subject to serious sanctions.

## Wireshark dissector

For debugging purposes, you can use the wireshark dissector from `confundo.lua`. The dissector requires
at least version 1.12.6 of Wireshark with LUA support enabled.

To enable the dissector for Wireshark session, use `-X` command line option, specifying the full
path to the `confundo.lua` script:

    wireshark -X lua_script:./confundo.lua

To dissect tcpdump-recorded file, you can use `-r <pcapfile>` option. For example:

    wireshark -X lua_script:./confundo.lua -r confundo.pcap
    
## Project Report

   * Shirley Cabrera, PID: 6119474
   * High Level Design: On the `send` method, within the while loop I keep dispatching new packets as the ACK's come in and the window increases instead of waiting for the previous window to be completely "used", for this I keep the outbuffer (only decreasing it with the ACK's) and use the modular difference between the `seqNum` and the `base` to know what data to send. Other than that I just followed provided esqueleton.
   * Did not run into any major problem, just initially struggled with making the concepts work for both client and server.
   * Aknwowledgements:
      * For sequence and ack numbers understanding used: https://packetlife.net/blog/2010/jun/7/understanding-tcp-sequence-acknowledgment-numbers/
      * For occasionally checking python api usage used: https://stackoverflow.com
