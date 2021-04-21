# Based on https://github.com/psyciknz/OpenHAB-Scripts :
# Forked from https://github.com/tomgidden/rpi_bluemaestro_mqtt

# BlueMastro Tempo Disc Advertising packet decoder

DEBUG = False

# Called from driver used to persist or distribute events (e.g., bluemaestro_mqtt.py)
# This class has the specificis for decoding the advertising packets for the Blue Maestro Tempo Disc https://www.bluemaestro.com/product/tempo-disc-temperature/
# Unsure if there are any other Blue Maestro products that it would work with.
# David@andc.nz 15/12/2016

# BLE Scanner based on from JCS 06/07/14
# BLE scanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# BLE scanner, based on https://code.google.com/p/pybluez/source/browse/trunk/examples/advanced/inquiry-with-rssi.py

# https://github.com/pauloborges/bluez/blob/master/tools/hcitool.c for lescan
# https://kernel.googlesource.com/pub/scm/bluetooth/bluez/+/5.6/lib/hci.h for opcodes
# https://github.com/pauloborges/bluez/blob/master/lib/hci.c#L2782 for functions used by lescan

# performs a simple device inquiry, and returns a list of ble advertizements
# discovered device

# NOTE: Python's struct.pack() will add padding bytes unless you make the endianness explicit. Little endian
# should be used for BLE. Always start a struct.pack() format string with "<"

# NOTE: Prior versions of this code going back to psyciknz/OpenHAB-Scripts fail to account for negative values for temperature and dewpoint. 
# This version adds two's compliment logic to ensure both positive and negative temperature values are returned.
# Function twos_comp() and how it is called adapted from https://github.com/cosmorogers/OpenHAB-Scripts

import collections
import os
import sys
import struct
import bluetooth._bluetooth as bluez
import logging

logging.basicConfig(level=logging.DEBUG)

LE_META_EVENT = 0x3e
LE_PUBLIC_ADDRESS=0x00
LE_RANDOM_ADDRESS=0x01
LE_SET_SCAN_PARAMETERS_CP_SIZE=7
OGF_LE_CTL=0x08
OCF_LE_SET_SCAN_PARAMETERS=0x000B
OCF_LE_SET_SCAN_ENABLE=0x000C
OCF_LE_CREATE_CONN=0x000D

LE_ROLE_MASTER = 0x00
LE_ROLE_SLAVE = 0x01

# these are actually subevents of LE_META_EVENT
EVT_LE_CONN_COMPLETE=0x01
EVT_LE_ADVERTISING_REPORT=0x02
EVT_LE_CONN_UPDATE_COMPLETE=0x03
EVT_LE_READ_REMOTE_USED_FEATURES_COMPLETE=0x04

# Advertisment event types
ADV_IND=0x00
ADV_DIRECT_IND=0x01
ADV_SCAN_IND=0x02
ADV_NONCONN_IND=0x03
ADV_SCAN_RSP=0x04


def init():
    dev_id = 0
    sock = bluez.hci_open_dev(dev_id)
    hci_le_set_scan_parameters(sock)
    hci_enable_le_scan(sock)
    return sock

def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is

def returnnumberpacket(pkt):
    myInteger = 0
    multiple = 256
    for c in pkt:
        myInteger += c * multiple
        multiple = 1
    return myInteger

def returnstringpacket(pkt):
    myString = "";
    for c in pkt:
        myString += chr(c)
    return myString

def returnhexpacket(pkt):
    myString = "";
    for c in pkt:
        myString += "%02x" % c
    return myString

def printpacket(pkt):
    for c in pkt:
        sys.stdout.write("0x%02x, " % c)
    sys.stdout.write("\n")
    for c in pkt:
        sys.stdout.write("%d, " % c)
    sys.stdout.write("\n")

def get_packed_bdaddr(bdaddr_string):
    packable_addr = []
    addr = bdaddr_string.split(':')
    addr.reverse()
    for b in addr:
        packable_addr.append(int(b, 16))
    return struct.pack("<BBBBBB", *packable_addr)

def packed_bdaddr_to_string(bdaddr_packed):
    return ':'.join('%02x'%i for i in struct.unpack("<BBBBBB", bdaddr_packed[::-1]))

def hci_enable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x01)

def hci_disable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x00)

def hci_toggle_le_scan(sock, enable):
# hci_le_set_scan_enable(dd, 0x01, filter_dup, 1000);
# memset(&scan_cp, 0, sizeof(scan_cp));
 #uint8_t         enable;
 #       uint8_t         filter_dup;
#        scan_cp.enable = enable;
#        scan_cp.filter_dup = filter_dup;
#
#        memset(&rq, 0, sizeof(rq));
#        rq.ogf = OGF_LE_CTL;
#        rq.ocf = OCF_LE_SET_SCAN_ENABLE;
#        rq.cparam = &scan_cp;
#        rq.clen = LE_SET_SCAN_ENABLE_CP_SIZE;
#        rq.rparam = &status;
#        rq.rlen = 1;

#        if (hci_send_req(dd, &rq, to) < 0)
#                return -1;
    cmd_pkt = struct.pack("<BB", enable, 0x00)
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)


def hci_le_set_scan_parameters(sock):
    old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)

    SCAN_RANDOM = 0x01
    OWN_TYPE = SCAN_RANDOM
    SCAN_TYPE = 0x01

def parse_events(sock, loop_count=100):
    old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)

    # perform a device inquiry on bluetooth device #0
    # The inquiry should last 8 * 1.28 = 10.24 seconds
    # before the inquiry is performed, bluez should flush its cache of
    # previously discovered devices
    flt = bluez.hci_filter_new()
    bluez.hci_filter_all_events(flt)
    bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
    sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, flt )
    done = False
    results = []
    ret = {}

    for i in range(0, loop_count):
        logging.debug("parse_events main loop, i=%s" % i)
        pkt = sock.recv(255)
        ptype, event, plen = struct.unpack("BBB", pkt[:3])

        if event == bluez.EVT_INQUIRY_RESULT_WITH_RSSI:
            i = 0

        elif event == bluez.EVT_NUM_COMP_PKTS:
            i = 0

        elif event == bluez.EVT_DISCONN_COMPLETE:
            i = 0

        elif event == LE_META_EVENT:
            subevent, = struct.unpack("B", pkt[3:4])
            pkt = pkt[4:]

            if subevent == EVT_LE_CONN_COMPLETE:
                le_handle_connection_complete(pkt)

            elif subevent == EVT_LE_ADVERTISING_REPORT:
                num_reports = struct.unpack("B", pkt[0:1])[0]
                report_pkt_offset = 0
                mac=returnhexpacket(pkt[report_pkt_offset + 3: report_pkt_offset + 9])
                logging.debug("parse_events adv subevent mac=%s" % mac)

                for i in range(0, num_reports):
                    logging.debug("parse_events inner loop, i=%s" % i)
                    company = returnhexpacket(pkt[report_pkt_offset + 15: report_pkt_offset + 17])

                    if (DEBUG == True):
                        printpacket(pkt)

                    nm = returnstringpacket(pkt[report_pkt_offset+33:report_pkt_offset+33+8])

                    if (company == "3301" or nm=='C481AF21' or nm=='C2E4EB1B'):

                        logging.debug("Name = %s" % nm)
                        logging.debug("Company 3301")

                        nameLength = int(pkt[report_pkt_offset + 32])
                        name = returnstringpacket(pkt[report_pkt_offset + 33:report_pkt_offset + (33+nameLength-1)])

                        ret['make'] = company
                        ret['model'] = pkt[report_pkt_offset+17]
                        ret['name'] = name

                        ret["udid"] = returnhexpacket(pkt[report_pkt_offset + 22: report_pkt_offset - 6])
                        ret["mac"] = returnhexpacket(pkt[report_pkt_offset + 3: report_pkt_offset + 9])

                        if (ret['model'] == 27 ): # Purple
                            ret["temperature"] = float(twos_comp(int(returnhexpacket(pkt[report_pkt_offset + 23:report_pkt_offset + 25]), 16), 16 ))/10
                            ret["humidity"] = float(returnnumberpacket(pkt[report_pkt_offset + 25:report_pkt_offset + 27]))/10
                            ret["pressure"] = float(returnnumberpacket(pkt[report_pkt_offset + 27:report_pkt_offset + 29]))/10

                        else: #if (ret['model'] == 23 ): # Blue
                            ret["temperature"] = float(twos_comp(int(returnhexpacket(pkt[report_pkt_offset + 23:report_pkt_offset + 25]), 16), 16 ))/10
                            ret["humidity"] = float(returnnumberpacket(pkt[report_pkt_offset + 25:report_pkt_offset + 27]))/10
                            ret["dewpoint"] = float(twos_comp(int(returnhexpacket(pkt[report_pkt_offset + 27:report_pkt_offset + 29]), 16), 16 ))/10


                        ret["battery"] = float(float(returnnumberpacket(pkt[report_pkt_offset + 18:report_pkt_offset + 19]) / float(25500) ) * 100)
                        ret["data"] = pkt

                        logging.debug("data to return")

                        results.append( ret )

    sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, old_filter )
    return results
