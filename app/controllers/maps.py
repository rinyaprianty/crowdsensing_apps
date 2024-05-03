from flask import render_template, redirect, session, url_for, flash, request, jsonify
from app.models.ScrapingData import *


import pandas as pd
import numpy as np
import json

def index():
	list_sensor = ScrapingData\
		.select('sensor')\
		.group_by('sensor').order_by('sensor', 'ASC').get().serialize()
	print(list_sensor)
	return render_template('pages/maps/index.html', list_sensor=list_sensor)


def getData():
	args = request.args

	sensors = args['sensors'].split(', ')

	data = ScrapingData.select('station_name','sensor','source', 'lat', 'lng').where_in('sensor', sensors).group_by('station_name', 'sensor', 'source').get().serialize()

	# print(data[0])
	for d in range(len(data)):
		# GET LAST OF VALUES
		addition_data = ScrapingData.where('station_name', data[d]['station_name'])\
			.where('sensor', data[d]['sensor'])\
			.where('source', data[d]['source'])\
			.order_by('created_at', 'DESC')\
			.select('sensor_value', 'date_data')\
			.limit(1).first().serialize()

		data[d]['lat'] = float(data[d]['lat'])
		data[d]['lng'] = float(data[d]['lng'])
		data[d]['sensor_value'] = addition_data['sensor_value']
		data[d]['date_data']    = addition_data['date_data'].strftime('%Y-%m-%d %H:%M:%S')
	
	# print(pd.DataFrame(data))

	return json.dumps(data)