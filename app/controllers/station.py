from flask import render_template, redirect, session, url_for, flash, request, jsonify
from app.models.User import *
from app.models.Station import *
from app.models.Source import *
from app.models.StationSourceUrl import *

import os

def index():
	sources = Source.get().serialize()
	stations = Station.get().serialize()
	for s in range(len(stations)):
		tmp_sources = []
		for src in sources:
			# check if station exist in url
			sourceUrl = StationSourceUrl.where('source_id', src['id'])\
				.where('station_id', stations[s]['id']).first()
			if sourceUrl is not None:
				sourceUrl = sourceUrl.serialize()
				tmp_sources.append({'source':src['source'], 'url':sourceUrl['url'] })
			else:
				tmp_sources.append({'source':src['source'], 'url':'' })

		stations[s]['sources'] = tmp_sources
	
	return render_template('pages/station/index.html', data=stations)

def create():
	source = Source.get().serialize()
	# print()
	# print(source)
	return render_template('pages/station/create.html', source = source)

def store():
	form       = request.form
	sources    = form.getlist('source')
	sources_id = form.getlist('source_id')
	
	# Insert to station
	station = Station()
	station.station = form['station']
	station.lat     = form['lat']
	station.long    = form['long']
	station.save()

	station_id = station.id

	for sid in range(len(sources_id)):
		station_source_url = StationSourceUrl()
		station_source_url.station_id = station_id
		station_source_url.source_id  = sources_id[sid]
		station_source_url.url        = sources[sid]
		station_source_url.save()

	flash('Save success.!', 'success')
	return redirect(url_for('station_index'))


def edit(id):
	source  = Source.get().serialize()
	station = Station.find(id).serialize()

	for src in range(len(source)):
		# Check if url exist
		urlData = StationSourceUrl.where('station_id', station['id'])\
			.where('source_id', source[src]['id'])\
			.first()
		if urlData is not None:
			urlData = urlData.serialize()
			source[src]['urls'] = {'url':urlData['url'], 'url_id':urlData['id'] }
		else:
			source[src]['urls'] = {'url':'', 'url_id':''}

	return render_template('pages/station/edit.html', data=station, source=source)


def update(id):
	form       = request.form
	sources    = form.getlist('source')
	sources_id = form.getlist('source_id')
	url_id     = form.getlist('url_id')

	# Update station
	data = Station.find(id)
	data.station = form['station']
	data.lat     = form['lat']
	data.long    = form['long']
	data.save()

	station_id = id

	for sid in range(len(sources_id)):
		if len(url_id[sid]) > 0:
			station_source_url = StationSourceUrl.find(url_id[sid])
		else:
			station_source_url = StationSourceUrl()
		station_source_url.station_id = station_id
		station_source_url.source_id  = sources_id[sid]
		station_source_url.url        = sources[sid]
		station_source_url.save()

	flash('Update success.!', 'success')
	return redirect(url_for('station_index'))