#! /usr/bin/python3
# Binh Nguyen, Feb 08, 2020
# run sensor in advance mode (wake up, read, sleep), and log data to CSV file

import os, time
import serial
import zh03b

def host_folder():
	"""designate a folder to save each month"""
	this_month_folder = time.strftime('%b%Y')
	basedir = os.path.abspath(os.path.dirname(__file__))
	all_dirs = [d for d in os.listdir(basedir) if os.path.isdir(d)]
	if len(all_dirs) == 0 or this_month_folder not in all_dirs:
		os.makedirs(this_month_folder)
		print('created: {}'.format(this_month_folder))
	return os.path.join(basedir, this_month_folder)


def data_record(output, logFile):
	'''record data into a csv file with the custom header'''
	logFile = os.path.join(host_folder(), logFile)
	with open(logFile, 'a+') as f:
		f.seek(0, 0)
		head_ = f.readline().lower()
		if not head_.startswith("time"):
			print(f'Head as {head_}')
			print(f'LogFile as {logFile}')
			headers = '''time,pm1,pm2.5,pm10\n'''
			f.write(headers)		
		else:
			'''log data to an existing file'''
			f.seek(0,2)
			f.write(output)
			f.write('\n')
	return None


if __name__ == '__main__':
	ser = serial.Serial(port='/dev/ttyUSB0')
	last_time = 0
	interval = 30 # seconds
	logfile = 'zh03b_demo2.csv'
	
	# set sensor to QA mode, send reques and get reading
	zh03b.send_cmd(ser, zh03b.get_cmd('set_qa'))
	try:
		while True:
			if time.time() - last_time > interval:
				# turn on the sensor the sensor
				output = zh03b.read_sensor_passive(ser)
				print(output)
				data_record(output, logfile)
				# push_MQTT(output)
				last_time = int(time.time())
			else:
				time.sleep(1)
	except KeyboardInterrupt:
		print('Ctr+C is pressed.  Exiting.')
		ser.close()
		raise SystemExit
