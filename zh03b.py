#!/usr/bin/python3
# Binh Nguyen, Feb 08, 2019

# datasheet: https://www.winsen-sensor.com/d/files/air-quality/zh03-series-laser-dust-module-v2_0.pdf
import time
import serial

def get_cmd(mode):
	'''
	commands available on ZH03B:
	instruct, instruct_return, set_qa, upload, enter_dormant, quit_dormant, successful, fail
	'''
	cmd = list()
	if mode == 'instruct':
		# user send instruction == reading data?
		cmd = [0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]
	elif mode == 'instruct_return':
		# expected return value
		cmd = [0xFF, 0x86, 0x00, 0x85, 0x00, 0x96, 0x00, 0x65, 0xFA]
	elif mode == 'set_qa':
		# set sensor to Q&A mode == passive mode
		cmd = [0xFF, 0x01, 0x78, 0x41, 0x00, 0x00, 0x00, 0x00, 0x46]
	elif mode == 'upload':
		# initiate upload mode == active mode (always report data, default mode)
		cmd = [0xFF, 0x01, 0x78, 0x40, 0x00, 0x00, 0x00, 0x00, 0x47]
	elif mode == 'enter_dormant':
		# enter domaint mode == turning off an and diode?
		cmd = [0xFF, 0x01, 0xA7, 0x01, 0x00, 0x00, 0x00, 0x00, 0x57]
	elif mode == 'quit_dormant':
		# quit dormant mode == turning on fan and diode?
		cmd = [0xFF, 0x01, 0xA7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x58]
	elif mode == 'successful':
		# expected return value after setting enter or quit dormant mode
		cmd = [0xFF, 0xA7, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x58]
	elif mode == 'fail':
		cmd = [0xFF, 0xA7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x59]
	return bytearray(cmd)
	


def read_serial(ser, flush=True):
	''' read and record with matched heads'''
	if flush:
		ser.reset_input_buffer()
		time.sleep(2)
	recv = b''
	inp = ser.read()
	if inp == b'\x42':
		recv += inp
		inp = ser.read()
		if inp == b'\x4d':
			recv += inp
			recv += ser.read(22)
			return recv
	return None


def convert_qa_pms(recv):
	'''convert bytearray to PMs concentration'''
	byte1 = int.from_bytes(b'\xff', byteorder='big')
	cmd_byte = int.from_bytes(b'\x86', byteorder='big')
	for i, byte_ in enumerate(recv):
		if byte_ == byte1 and recv[i+1] == cmd_byte:
			pm1 = recv[i+6]*256 + recv[i+7]
			pm2_5 = recv[i+2]*256 + recv[i+3]
			pm10 = recv[i+4]*256 + recv[i+5]
			return (pm1, pm2_5, pm10)
	return (0,0,0)


def check_cmd_status(recv):
	'''check command status'''
	byte1 = int.from_bytes(b'\xff', byteorder='big')
	cmd_byte = int.from_bytes(b'\xA7', byteorder='big')
	success = int.from_bytes(b'\x01', byteorder='big')
	fail = int.from_bytes(b'\x00', byteorder='big')
	for i, byte_ in enumerate(recv):
		if byte_ == byte1 and recv[i+1] == cmd_byte and recv[i+2] == success:
			# print('Successful execute command')
			return 1
		elif byte_ == byte1 and recv[i+1] == cmd_byte and recv[i+2] == fail:
			# print('Failed to execute command')
			return 0
	print('Cannot get status of command')
	return -1

def read_pms_upload(recv):
	'''convert bytearray to PMs concentration'''
	if check_sum(recv):
		# print(f'Frame length: {recv[2] + recv[3]}')
		pm1 = recv[10]*256 + recv[11]
		pm2_5 = recv[12]*256 + recv[13]
		pm10 = recv[14]*256 + recv[15]
		return (pm1, pm2_5, pm10)
	return (0,0,0)

def check_sum(recv):
	'''total return value == ckc value'''
	calc = 0
	ord_arr = []
	for c in bytearray(recv[:-2]):
		calc +=c
		ord_arr.append(c)
	sent = (recv[-2] << 8) | recv [-1]

	if sent != calc:
		print('Unmatched CHECKSUM')
		return -1
	return True

def p_print(binary_string):
	'''return a easy to read heximal string'''
	return ' '.join([f'{x:02X}' for x in binary_string.strip()])

def send_cmd(ser, cmd):
	'''send command to the sensor'''
	try:
		ser.reset_output_buffer()
		time.sleep(0.1)
		ser.write(cmd)
		time.sleep(0.1)
		ser.reset_output_buffer()
		#  print(f'{p_print(cmd)}')
	except Exception as e:
		print(f'Exp as {e}')
	return None

def read_raw_serial(ser, flush=True):
	if flush:
		ser.reset_input_buffer()
	time.sleep(2)
	byte_ = ser.in_waiting
	# print(f'Number of byte in buffer: {byte_}')
	inp = ser.read(byte_)
	return inp

def read_sensor_qa(ser):
	send_cmd(ser, get_cmd('instruct'))
	recv = read_raw_serial(ser, flush=False)
	a,b,c = convert_qa_pms(recv)
	output = f'{time.strftime("%x %X")},{a},{b},{c}'
	print(output)
	return output

def read_sensor_passive(ser):
	send_cmd(ser, get_cmd('quit_dormant'))
	# check status of cmd
	# status = check_cmd_status(read_raw_serial(ser, flush=False))
	# print(f'{status}')
	# wait 10 seconds before request a reading
	time.sleep(10)
	send_cmd(ser, get_cmd('instruct'))
	time.sleep(1)
	# convert the reading to the number
	a,b,c = convert_qa_pms(read_raw_serial(ser, flush=False))
	output = f'{time.strftime("%x %X")},{a},{b},{c}'
	print(output)
	time.sleep(1)
	send_cmd(ser, get_cmd('enter_dormant'))
	# status = check_cmd_status(read_raw_serial(ser, flush=False))
	# print(f'{status}')

	return output


if __name__ == "__main__":
	ser = serial.Serial(port='/dev/ttyUSB0')
	last_time = 0
	interval = 30 # seconds
	# set sensor to QA mode -- send a request and get a reading
	send_cmd(ser, get_cmd('set_qa'))
	try:
		while True:
			if time.time() - last_time > interval:
				# turn on the sensor the sensor
				output = read_sensor_passive(ser)
				last_time = int(time.time())
			else:
				time.sleep(1)
	except KeyboardInterrupt:
		print('Ctr+C is pressed.  Exiting.')
		ser.close()
		raise SystemExit

