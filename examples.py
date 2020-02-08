#! /usr/bin/python3
# Binh Nguyen, Feb 08, 2020
# run one and get the PMs reading

import os, time
import serial
import zh03b

#initiate an instance
ser = serial.Serial(port='/dev/ttyUSB0')

# set sensor to upload mode  -- sensor outputs PMs reading
zh03b.send_cmd(ser, zh03b.get_cmd('upload'))

# read PMs from ZH03B sensor
pm1, pm2_5, pm10 = zh03b.read_pms_upload(zh03b.read_raw_serial(ser))
print(time.ctime())
print(f'PM1: {pm1}, PM2.5: {pm2_5}, PM10: {pm10} in ug/m3')
