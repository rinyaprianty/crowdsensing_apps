from flask import render_template, redirect, session, url_for, flash, request, jsonify
from app.models.Station import *
from app.models.Source import *
from app.models.StationSourceUrl import *
from app.models.StationSourceResult import *
from app.models.ScrapingData import *

import json
import urllib
import time
import pandas as pd
import numpy as np
import requests
import urllib.request
import os

from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import http.client
import urllib.parse
import time

def index():
	return render_template('pages/scraping/index.html')

def getDataNew():
	try:
		args = request.args
		#** Datatables Parameter
		draw         = int(args.get('draw'))
		start        = int(args.get('start'))
		length       = int(args.get('length'))
		search_value = args.get('search[value]', '')
		order_column = int(request.args.get('order[0][column]', 0))
		order_dir    = request.args.get('order[0][dir]', 'asc')

		#******************** START QUERY
		data = ScrapingData

		# ----- Start search condition below
		if search_value:
			data = data\
				.where('station_name', 'like', f"%{search_value}%")\
				.or_where('source', 'like', f"%{search_value}%")\
				.or_where('sensor', 'like', f"%{search_value}%")
		# ----- End search condition below

		# ----- Start order by coumn
		# {"data": "no"},
		# {"data": "station_name"},
		# {"data": "lat", "orderable": "false"},
		# {"data": "sensor"},
		# {"data": "sensor_value"},
		# {"data": "source"},
		# {"data": "created_at"},
		order_column_mapping = {
			0: '',
			1: 'station_name',
			2: 'lat',
			3: 'sensor',
			4: 'sensor_value',
			5: 'source',
			6: 'created_at',
			7: 'date_data'
		}

		column_to_order = order_column_mapping.get(order_column)
		if column_to_order != "":
			data = data.order_by(column_to_order, order_dir)
		else:
			data = data.order_by(order_column_mapping.get(6), 'desc')
		# ----- End order by coumn
		recordsTotal = data.count()
		data = data.offset(start).limit(length)
		data = data.get().serialize()
		#******************** END QUERY

		return_data = [{
				"no" 			: (start)+(i+1),
				"station_name"  : d['station_name'],
				"lat" 			: d['lat']+', '+d['lng'],
				"sensor" 		: d['sensor'],
				"sensor_value"	: d['sensor_value'],
				"source"		: d['source'],
				"created_at"	: datetime.strptime(d['created_at'], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S"),
				"date_data"	   	: d['date_data']
			} for i, d in enumerate(data)
		]

		response = {
			'draw': draw,
			'recordsTotal': recordsTotal,
			'recordsFiltered': recordsTotal,
			'data': return_data,
		}

		return jsonify(response)
	except Exception as e:
		return jsonify(e)



# ========================== START SCRAPING FUNCTION V0.0.2
def doScrapNew():
	args = request.args

	start_date = args['start_date']
	end_date = args['end_date']
	# print(start_date)
	lambordia = lombardiaData(start_date, end_date)
	# arpae     = arpaeData()
	# arpat     = arpat2Data()
	return "Ok"

def lombardiaData(start_date="", end_date=""):
	print('************* PROCESSING LAMORDIA')
	source     = 'dati.lombardia.it'
	start_date = start_date.replace(' ', 'T') # Format date from 2023-01-10 01:00:00 to 2023-01-10T01:00:00
	end_date   = end_date.replace(' ', 'T')

	# sensor_date_start = "2023-01-10T01:00:00"
	# sensor_date_end   = "2023-01-10T23:00:00"

	sensor_date_start = start_date
	sensor_date_end   = end_date

	# Build query API for lombardia
	url_sensor_data = "https://www.dati.lombardia.it/resource/g2hp-ar79.json?$query=" # Link query API
	query = """ SELECT `idsensore`, `data`, `valore`, `stato`, `idoperatore`
		WHERE
		  (`data`
		     BETWEEN "{sensor_date_start}" :: floating_timestamp
		     AND "{sensor_date_end}" :: floating_timestamp)
		LIMIT 10000""" # Set limit to max get data 10K data for query

	formatted_query = query.format(sensor_date_start=sensor_date_start, sensor_date_end=sensor_date_end) # Format inside query data
	encoded_query   = urllib.parse.quote(formatted_query)
	full_url        = url_sensor_data + encoded_query

	response = requests.request("GET", full_url, verify=False)
	station_values = json.loads(response.text)

	df_station_values  = pd.DataFrame(station_values)
	# print(df_station_values)

	# Get STATION REGISTRY DATA
	url_station_registri = "https://www.dati.lombardia.it/resource/ib47-atvt.json?$query="
	query = """SELECT
	  `idsensore`,
	  `nometiposensore`,
	  `unitamisura`,
	  `idstazione`,
	  `nomestazione`,
	  `quota`,
	  `provincia`,
	  `comune`,
	  `storico`,
	  `datastart`,
	  `datastop`,
	  `utm_nord`,
	  `utm_est`,
	  `lat`,
	  `lng`,
	  `location`,
	  `:@computed_region_6hky_swhk`,
	  `:@computed_region_ttgh_9sm5`
	WHERE
	  caseless_one_of(
	    `nometiposensore`,
	    "PM10 (SM2005)",
	    "Biossido di Azoto",
	    "PM10"
	  )
	ORDER BY `idsensore` ASC NULL LAST""" # There's where here for filter, you can remove where query to get all data

	formatted_query = query.format()
	encoded_query   = urllib.parse.quote(formatted_query)
	full_url        = url_station_registri + encoded_query

	response = requests.request("GET", full_url, verify=False)

	# After get Data Stations now loop to get value data
	station_registri = json.loads(response.text)

	# print(station_registri)
	for s in range(len(station_registri)):
		# time.sleep(1) # Sleep for half second to prevent blocking data
		sensor_id    = station_registri[s]['idsensore']
		station_name = station_registri[s]['nomestazione']
		sensor_name  = station_registri[s]['nometiposensore']

		lat = station_registri[s]['lat']
		lng = station_registri[s]['lng']

		# Search value data
		data_station = df_station_values.loc[df_station_values['idsensore'] == sensor_id]
		if len(data_station) > 0:
			for i, r in data_station.iterrows():
				date_str       = r['data']
				date_obj       = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
				formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
				sensor_value   = r['valore']


				scrapData              = ScrapingData()
				scrapData.station_name = station_name
				scrapData.lat          = lat
				scrapData.lng          = lng
				scrapData.sensor       = sensor_name
				scrapData.sensor_value = float(sensor_value)
				scrapData.source       = source
				scrapData.date_data	   = formatted_date
				scrapData.save()

		# url_sensor_data = "https://www.dati.lombardia.it/resource/g2hp-ar79.json?$query="
		# query = """ SELECT `idsensore`, `data`, `valore`, `stato`, `idoperatore`
		# 	WHERE
		# 	  (`data`
		# 	     BETWEEN "{sensor_date_start}" :: floating_timestamp
		# 	     AND "{sensor_date_end}" :: floating_timestamp)
		# 	  AND caseless_one_of(`idsensore`, "{sensor_id}")"""

		# formatted_query = query.format(sensor_date_start=sensor_date_start, sensor_date_end=sensor_date_end, sensor_id=sensor_id)
		# encoded_query   = urllib.parse.quote(formatted_query)
		# full_url        = url_sensor_data + encoded_query

		# response = requests.request("GET", full_url, verify=False)
		# station_values = json.loads(response.text)

		# if len(station_values) > 0:
		# 	# Save data to database
		# 	for sv in station_values:
		# 		date_str       = sv['data']
		# 		date_obj       = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
		# 		formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')


		# 		sensor_value = sv['valore']

		# 		scrapData              = ScrapingData()
		# 		scrapData.station_name = station_name
		# 		scrapData.lat          = lat
		# 		scrapData.lng          = lng
		# 		scrapData.sensor       = sensor_name
		# 		scrapData.sensor_value = float(sensor_value)
		# 		scrapData.source       = source
		# 		scrapData.date_data	   = formatted_date
		# 		scrapData.save()

		# print(station_values)
		# print(sensor_id, station_name, sensor_name)
	
	# url = "https://www.dati.lombardia.it/resource/ib47-atvt.json?$query=SELECT%0A%20%20%60idsensore%60%2C%0A%20%20%60nometiposensore%60%2C%0A%20%20%60unitamisura%60%2C%0A%20%20%60idstazione%60%2C%0A%20%20%60nomestazione%60%2C%0A%20%20%60quota%60%2C%0A%20%20%60provincia%60%2C%0A%20%20%60comune%60%2C%0A%20%20%60storico%60%2C%0A%20%20%60datastart%60%2C%0A%20%20%60datastop%60%2C%0A%20%20%60utm_nord%60%2C%0A%20%20%60utm_est%60%2C%0A%20%20%60lat%60%2C%0A%20%20%60lng%60%2C%0A%20%20%60location%60%2C%0A%20%20%60%3A%40computed_region_6hky_swhk%60%2C%0A%20%20%60%3A%40computed_region_ttgh_9sm5%60%0AWHERE%0A%20%20caseless_one_of(%0A%20%20%20%20%60nometiposensore%60%2C%0A%20%20%20%20%22PM10%20(SM2005)%22%2C%0A%20%20%20%20%22Biossido%20di%20Azoto%22%2C%0A%20%20%20%20%22PM10%22%0A%20%20)%0AORDER%20BY%20%60idsensore%60%20ASC%20NULL%20LAST"
	# decoded_url = urllib.parse.unquote(url)
	# print(decoded_url)
	
	return "Done"

def arpaeData():
	print('************* PROCESSING ARPAE')
	source   = 'dati.arpae.it'
	# Get air quality data
	arpaeCurl('https://dati.arpae.it/dataset/qualita-dell-aria-rete-di-monitoraggio/resource/4dc855a1-6298-4b71-a1ae-d80693d43dcb', 'quality.csv')
	# Get registered station
	arpaeCurl('https://dati.arpae.it/dataset/qualita-dell-aria-rete-di-monitoraggio/resource/21a9464d-c91a-4f17-b5c7-f3ee7560ff7e', 'station.csv')
	# Get parameter data
	arpaeCurl('https://dati.arpae.it/dataset/qualita-dell-aria-rete-di-monitoraggio/resource/65faaf03-f2fc-4f8a-b9cb-c771907644ce', 'parameter.csv')


	# LOAD EVERY DATA
	arpae_path = os.path.join('static', 'arpae')

	quality_path          = os.path.join(arpae_path, 'quality.csv')
	quality               = pd.read_csv(quality_path)
	quality['station_id'] = quality['station_id'].astype(str)

	station_path = os.path.join(arpae_path, 'station.csv')
	station      = pd.read_csv(station_path)

	parameter_path = os.path.join(arpae_path, 'parameter.csv')
	parameter      = pd.read_csv(parameter_path)
	parameter_data = parameter[['IdParametro', 'PARAMETRO']]

	# Proses station
	station_ids               = station.groupby('Cod_staz')[['Stazione','LAT_GEO', 'LON_GEO' ]].first().reset_index()
	station_ids['station_id'] = station_ids['Cod_staz'].str.replace('.', '')
	station_ids['station_id'] = station_ids['station_id'].astype(str)

	# print(pd.concat([quality.set_index('station_id'), station_ids.set_index('station_id')], axis=1, join='inner').reset_index())
	
	# merge = pd.concat([quality.set_index('station_id'), station_ids.set_index('station_id')], axis=1, join='inner')
	tmp_merge             = pd.merge(quality, station_ids, on='station_id', how='inner')
	full_merge            = pd.merge(tmp_merge, parameter_data, left_on='variable_id', right_on='IdParametro', how='inner')
	full_merge['reftime'] = pd.to_datetime(full_merge['reftime'], format="%Y-%m-%dT%H:%M:%S")

	more_than_date = str(datetime.now() - timedelta(days=2)) # Get data start from -x days ago
	final_data     = full_merge[full_merge['reftime'] >= more_than_date]
	# final_data['reftime'] = pd.to_datetime(final_data['reftime'])
	final_data           = final_data.sort_values(by='reftime', ascending=False).reset_index(drop=True)
	final_data['dttime'] = final_data['reftime'].dt.date
	final_data           = final_data.groupby([ 'dttime', 'station_id', 'variable_id']).first().reset_index()
	final_data           = final_data.sort_values(by='reftime', ascending=True).reset_index(drop=True)
	print('***********************************')
	print(final_data)
	print('***********************************')
	# final_data.to_csv('test.csv')
	# print(quality)

	# INSERT DATA
	for i, d in final_data.iterrows():
		scrapData              = ScrapingData()
		scrapData.station_name = d['Stazione']
		scrapData.lat          = d['LAT_GEO']
		scrapData.lng          = d['LON_GEO']
		scrapData.sensor       = d['PARAMETRO']
		scrapData.sensor_value = d['value'] if d['value'] != 'NULL' else 0
		scrapData.source       = source
		scrapData.date_data	   = d['reftime']
		scrapData.save()

	return "Done"

def arpaeCurl(url, name='file.cv'):
	url_quality  = url
	html_content = urllib.request.urlopen(url_quality).read()

	soup  = BeautifulSoup(html_content, 'html.parser')
	links = []
	for link in soup.find_all('a', class_='resource-url-analytics', href=True):
		links.append(link['href'])

	if len(links) > 1:
		urllib.request.urlretrieve(links[0], 'static/arpae/'+name)
	return True

def arpat2Data():
	print('************* PROCESSING ARPAT')
	source   = 'arpat.toscana.it'
	# Load arpat station latlong csv
	# Make sure if you want to change it the latest file have :
	#  1. the same name as the current file
	#  2. the same format value
	csv_file_name = "Arpat_station.csv"
	csv_file_path = os.path.join("static", csv_file_name)


	csv_data = pd.read_csv(csv_file_path)
	arpat_lat_lng = {}
	for i, r in csv_data.iterrows():
		tmp_lat_lng = {'lat' : r['Latitude'], 'lng' : r['Longitude']}
		arpat_lat_lng[r['Station']] = tmp_lat_lng
	# print(arpat_lat_lng)
	
	# START SCRAPING SELENIUM
	options = Options()
	options.add_argument('--disable-gpu')
	# options.add_argument('--headless')

	driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),  options=options)

	urls = [
		"https://www.arpat.toscana.it/temi-ambientali/aria/qualita-aria/grafici_bollettino/index/PM10", 
		"https://www.arpat.toscana.it/temi-ambientali/aria/qualita-aria/grafici_bollettino/index/PM2_5",
		"https://www.arpat.toscana.it/temi-ambientali/aria/qualita-aria/grafici_bollettino/index/NO2",
		"https://www.arpat.toscana.it/temi-ambientali/aria/qualita-aria/grafici_bollettino/index/O3",
		"https://www.arpat.toscana.it/temi-ambientali/aria/qualita-aria/grafici_bollettino/index/CO",
		"https://www.arpat.toscana.it/temi-ambientali/aria/qualita-aria/grafici_bollettino/index/SO2",
		# "https://www.arpat.toscana.it/temi-ambientali/aria/qualita-aria/grafici_bollettino/index/H2S",
		# "https://www.arpat.toscana.it/temi-ambientali/aria/qualita-aria/grafici_bollettino/index/C6H6"
	]
	for url in urls:
		sensor   = url.split('/')[-1]
		table_id = 'div_tabella_grafico_bollettino_'+sensor

		driver.get(url)

		max_retry   = 5 # Maximum of 1 second for searching the ID's
		total_retry = 0
		rows = []
		while total_retry <= max_retry:
			print('Retry ', total_retry)
			time.sleep(1)
			table = WebDriverWait(driver, 20).until(
				EC.presence_of_element_located((By.ID, table_id))
			)

			rows = table.find_elements(By.TAG_NAME, 'tr')
			if len(rows) > 0:
				print('Row Exist')
				total_retry = max_retry
			total_retry+=1
		
		if len(rows) > 0:
			first_row   = rows[0]
			first_cells = first_row.find_elements(By.TAG_NAME, 'th')

			date_data = ''
			list_station = []
			for c in range(len(first_cells)):
				if c > 0:
					list_station.append(first_cells[c].text)

			last_row    = rows[-1]
			last_cells  = last_row.find_elements(By.TAG_NAME, 'td')
			list_values = []

			for c in range(len(last_cells)):
				if c == 0:
					date_data = last_cells[c].text
				else:
					try:
						list_values.append(int(last_cells[c].text))
					except Exception as e:
						list_values.append(0)

			final_data = {
				'sensor' : sensor,
				'date_data' : date_data,
				'station' : []
			}

			for l in range(len(list_station)):
				final_data['station'].append({'name' : list_station[l], 'value' : list_values[l]})


			for fd in final_data['station']:
				station_name = fd['name']
				day, month, year = final_data['date_data'].split('-')

				# Use try except for error on lat long, if lat lng data not in the list
				try:
					scrapData              = ScrapingData()
					scrapData.station_name = station_name
					scrapData.lat          = arpat_lat_lng[station_name]['lat']
					scrapData.lng          = arpat_lat_lng[station_name]['lng']
					scrapData.sensor       = final_data['sensor']
					scrapData.sensor_value = fd['value']
					scrapData.source       = source
					scrapData.date_data	   = f"{year}-{month}-{day}"
					scrapData.save()
				except Exception as e:
					print(e)
	driver.quit()
	return "Done"
# ========================== OLD SCRAPING FUNCTION
def getData():
	try:
		args = request.args
		#** Datatables Parameter
		draw         = int(args.get('draw'))
		start        = int(args.get('start'))
		length       = int(args.get('length'))
		search_value = args.get('search[value]', '')
		order_column = int(request.args.get('order[0][column]', 0))
		order_dir    = request.args.get('order[0][dir]', 'asc')

		#******************** START QUERY
		data = StationSourceResult.join('sources', 'sources.id', '=', 'station_source_results.source_id')\
			.join('stations', 'stations.id', '=', 'station_source_results.station_id')\
			.select('station_source_results.*', 'stations.station','sources.source')\
		# ----- Start search condition below
		if search_value:
			data = data \
				.where('station', 'like', f"%{search_value}%")\
				.or_where('sources', 'like', f"%{search_value}%")
		# ----- End search condition below

		# ----- Start order by coumn
		order_column_mapping = {
			0: '',
			1: 'station',
			2: 'source',
			3: 'result_data',
			4: ''
		}

		column_to_order = order_column_mapping.get(order_column)
		if column_to_order != "":
			data = data.order_by(column_to_order, order_dir)
		# ----- End order by coumn
		recordsTotal = data.count()
		data = data.offset(start).limit(length)
		data = data.get().serialize()
		#******************** END QUERY
		
		return_data = [{
				"no" 			: (start)+(i+1),
				"station" 		: d['station'],
				"source" 		: d['source'],
				"result_data" 	: d['result_data'],
				"created_at"	: d['created_at']
			} for i, d in enumerate(data)
		]
		# print(return_data)

		response = {
			'draw': draw,
			'recordsTotal': recordsTotal,
			'recordsFiltered': recordsTotal,
			'data': return_data,
		}

		return jsonify(response)
	except Exception as e:
		return jsonify(e)


def dscrap():
	data = StationSourceUrl.join('sources', 'sources.id', '=', 'station_source_urls.source_id')\
		.join('stations', 'stations.id', '=', 'station_source_urls.station_id')\
		.where_null('stations.deleted_at')\
		.where_null('sources.deleted_at')\
		.select('station_source_urls.*', 'stations.station','sources.source')\
		.get().serialize()

	options = Options()
	options.add_argument('--disable-gpu')
	# options.add_argument('--headless')

	driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),  options=options)

	for d in range(len(data)):
		print('Processing data station', data[d]['station'])

		source    = data[d]['source']
		scrap_url = data[d]['url']
		driver.get(scrap_url)
		return_data = {}
		if source == 'aqicn.org':
			return_data = aqicnData(driver)
		elif source == 'aqi.in':
			return_data = aqiinData(driver)
		elif source == 'arpat.toscana.it':
			return_data = arpatData(driver)

		resultData = StationSourceResult()
		resultData.station_id  = data[d]['station_id']
		resultData.source_id   = data[d]['source_id']
		resultData.result_data = str(return_data)
		resultData.save()
	driver.quit()
	return "Ok"

# ========================== START SCRAPING NORMALIZATION DATA FROM EACH WEBSITES ==========================
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