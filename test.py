import urllib
import time
import pandas as pd
import numpy as np

from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


station_data = [
	{
		'station' : 'GRAMSCI',
		'lat' : '',
		'lng' : '',
		'source_url' : [
			{
				'source' : 'aqicn.org',
				'url' : 'https://aqicn.org/city/italy/toscana/firenze/fi-gramsci/'
			},
			{
				'source' : 'aqi.in',
				'url' : 'https://www.aqi.in/dashboard/italy/tuscany/florence/gramsci'
			},
			{
				'source' : 'arpat.toscana.it',
				'url' : 'https://www.arpat.toscana.it/temi-ambientali/aria/qualita-aria/rete_monitoraggio/scheda_stazione/FI-GRAMSCI'
			}
		]
	}
]

def aqicnData(driver):
	# Wait until id loaded completely to get data
	wait_for_id = 'aqiwgtvalue'
	WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.ID, wait_for_id))
	)

	required_data = {
		"o3"    : 0,
		"pm10"  : 0,
		"pm25"  : 0,
		"no2"   : 0,
		'co'	: 0
	}

	# Process pm25
	try:
		_text_data = driver.find_element(By.ID, 'cur_pm25').text
		required_data['pm25'] = int(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get pm25 with error', e)
		pass

	# Process 03
	try:
		_text_data = driver.find_element(By.ID, 'cur_o3').text
		required_data['o3'] = float(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get o3 with error', e)
		pass

	# Process pm10
	try:
		_text_data = driver.find_element(By.ID, 'cur_pm10').text
		required_data['pm10'] = float(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get pm10 with error', e)
		pass

	# Proses no2
	try:
		_text_data = driver.find_element(By.ID, 'cur_no2').text
		required_data['no2'] = float(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get no2 with error', e)
		pass


	# Proses no2
	try:
		_text_data = driver.find_element(By.ID, 'cur_co').text
		required_data['co'] = float(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get co with error', e)
		pass

	# print(required_data)
	return required_data

def aqiinData(driver):
	# Wait until id loaded completely to get data
	wait_loaded = True
	while wait_loaded:
		wait_for_id = '//*[@id="aqi_val"]/h4[2]'
		total_score = WebDriverWait(driver, 20).until(
			EC.presence_of_element_located((By.XPATH, wait_for_id))
		)
		if total_score.text != '':
			wait_loaded = False # Mark as result already shown and continue
			print(total_score.text)
		else:
			time.sleep(2)
			print(total_score.text)

	required_data = {
		"o3"    : 0,
		"pm10"  : 0,
		"pm25"  : 0,
		"no2"   : 0,
		'co'	: 0
	}

	# Process pm25
	try:
		_text_data = driver.find_element(By.ID, 'pm25Val').text
		required_data['pm25'] = float(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get pm25 with error', e)
		pass

	# Process 03
	try:
		_text_data = driver.find_element(By.ID, 'o3Val').text
		required_data['o3'] = float(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get o3 with error', e)
		pass

	# Process pm10
	try:
		_text_data = driver.find_element(By.ID, 'pm10Val').text
		required_data['pm10'] = float(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get pm10 with error', e)
		pass

	# Proses no2
	try:
		_text_data = driver.find_element(By.ID, 'no2Val').text
		required_data['no2'] = float(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get no2 with error', e)
		pass


	# Proses no2
	try:
		_text_data = driver.find_element(By.ID, 'coVal').text
		required_data['co'] = float(_text_data)
	except Exception as e:
		# print('Error Exception : ')
		# print('Cannot get co with error', e)
		pass

	# print(required_data)
	return required_data

def arpatData(driver):

	wait_for_id = 'div_dati_ultima_ora'
	parent_h1 = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.ID, wait_for_id))
	)

	required_data = {
		"o3"    : 0,
		"pm10"   : 0,
		"pm25"  : 0,
		"no2"   : 0,
		'co'	: 0
	}

	time.sleep(5)
	list_child_h1 = parent_h1.find_elements(By.CLASS_NAME, 'panel-default')
	for child in list_child_h1:
		heading = child.find_element(By.CLASS_NAME, 'panel-heading').text
		body    = child.find_element(By.CLASS_NAME, 'panel-body').text.split()[0]

		if heading == "O3":
			required_data["o3"] = float(body)
		elif heading == "PM10":
			required_data["pm10"] = float(body)
		elif heading == "PM25":
			required_data["pm25"] = float(body)
		elif heading == "NO2":
			required_data['no2'] = float(body)
		elif heading == "CO":
			required_data['co'] = float(body)

	# print(required_data)
	return required_data

options = Options()
options.add_argument('--disable-gpu')
# options.add_argument('--headless')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),  options=options)

# Looping through station data

for data in station_data:
	print('Processing data station', data['station'])
	for src in data['source_url']:
		print('- Scrap from source', src['source'])
		driver.get(src['url'])
		$return_data = {}
		if src['source'] == 'aqicn.org':
			# continue
			return_data = aqicnData(driver)
		elif src['source'] == 'aqi.in':
			# continue
			return_data = aqiinData(driver)
		elif src['source'] == 'arpat.toscana.it':
			return_data = arpatData(driver)

