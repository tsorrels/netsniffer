import struct
import socket
from ctypes import *


class LlcHeader(Structure):
    _fields_ = [
        ("dsap", c_ubyte),
        ("ssap", c_ubyte),
        ("control", c_ubyte),        
        ("org_code", c_ubyte * 3),
        ("type_field", c_uint16)        
        ]
    
    def __new__(self, socket_buffer = None):
        return self.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer = None):
        self.length = 8
	self.packet_type = socket.ntohs(self.type_field)
