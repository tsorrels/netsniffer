#!/usr/bin/env python2

import importlib
import traceback
import signal
import threading
import os
import struct
import socket
import time
import curses
import getopt
import sys
from ip_connection import IPConnection
from ip_header import IP
from display_headers import *
from display_item import *
from logwriter import LogWriter
from ip_state import GlobalState
from ip_display import Display
from ip_controller import Controller
from ip_ethheader import EthHeader

display = Display()
        

def sniff(state):

    connections = state.all_connections
    lock = state.all_lock
    
    sniffer = socket.socket(socket.AF_PACKET, socket.SOCK_RAW,
                            socket.ntohs(0x0003))
    sniffer.bind((state.interface, 0))
    #sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    #if os.name == "nt":
    #    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    try:        
        while True:

            raw_buffer = sniffer.recvfrom(65565)[0]
            eth_header = EthHeader(raw_buffer[0:14])
            if len(raw_buffer) < 34 :
                # there is no ip header in this packet
                state.logwriter.write('error', 'processed non-ip packet\n')
                continue
            
            ip_header = IP(raw_buffer[14:34])

            #check if in permiscuous mode
            if not state.permiscuous:
                if not (ip_header.src_address == state.host_address or \
                        ip_header.dst_address == state.host_address):
                    #state.logwriter.write('error', state.host_address)
                    continue

            newConnection = True
            new_time = time.time()
            with lock:
                for connection in connections:
                    if ip_header.src == connection.src and \
                    ip_header.dst == connection.dst:
                        # update connection
                        connection.data += ip_header.length
                        connection.time_last = new_time
                        connection.RX = True
                        newConnection = False                        
                        break

            if newConnection:
            # append is thread safe
            # this is the only thread writing to this list
                connections.append(IPConnection(ip_header,
                                                eth_header,
                                                new_time,
                                                state.data_extensions))
                
                
    except Exception as e:
        state.logwriter.write('error', str(e) + '\n')
        exit(0)
        #traceback.print_exc(limit=None, file=file_handle)


def SIGINT_handler(signal, frame):
    curses.endwin()
    exit(0)            

def SIGWINCH_handler(signal, frame):
    #pass
    display.update_window()
    
    
def main():
    
    (optlist, args) = getopt.getopt(sys.argv[1:], 'pi:')

    state = GlobalState(optlist, args)
    display.state = state

    controller = Controller(display, state)
    display.controller = controller
    
    
    signal.signal(signal.SIGINT, SIGINT_handler)

    signal.signal(signal.SIGWINCH, SIGWINCH_handler)
    
    # TODO: support Windows
    #if os.name == "nt":
	#print 'OS is "nt"'
        #thread_win = threading.Thread(target = sniff,
        #                           args = (socket.IPPROTO_IP,))
        #while True:
        #    time.sleep(5)

        #return

    # else
    #thread_icmp = threading.Thread(target = sniff,
     #                              args = (socket.IPPROTO_ICMP, state))
    #thread_tcp = threading.Thread(target = sniff,
     #                              args = (socket.IPPROTO_TCP, state))
    #thread_udp = threading.Thread(target = sniff,
     #                              args = (socket.IPPROTO_UDP, state))

    sniffer = threading.Thread(target = sniff, args = (state,))
    sniffer.daemon = True
    sniffer.start()
    #thread_icmp.daemon = True
    #thread_tcp.daemon = True
    #thread_udp.daemon = True

    # start sniffer threads
    #thread_icmp.start()
    #thread_tcp.start()
    #thread_udp.start()

    # start extension threads
    for run in state.run_threads:
        thread = threading.Thread(target = run, args = (state, ))
        thread.daemon = True
        thread.start()

    # run UI on this thread
    while True:
        time.sleep(.1)
        display.run()
    

if __name__ == "__main__":
    main()
