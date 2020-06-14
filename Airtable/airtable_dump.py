from airtable import Airtable 
from oauth2client import file, client, tools
from googleapiclient.discovery import build
from datetime import date
import pprint
import csv
from httplib2 import Http
import requests
import zipfile
import json
import io, os
import sys


def run():

	base_key = 'app0bcm2GEEGdlC7K'
	coaches_table_name = 'Coaches'
	events_table_name = 'Events'

	coaches_table = Airtable(base_key, coaches_table_name, api_key='keyiLfzA6XNxVuMw1')
	events_table = Airtable(base_key, events_table_name, api_key='keyiLfzA6XNxVuMw1')

	all_events = events_table.get_all()
	all_coaches = coaches_table.get_all()

	final_data = []

	print('Getting Headers')

	#Set headers dynamically so as columns are added the demographics update
	headers = sorted({key for coach in all_coaches for key in coach['fields'].keys()}) \
			+ ['Program','Event Type','Event Date', 'Duration','Event Role']
	
	#Get rid of event columns in coach table
	for column in ['Chair', 'Head TF', 'TF', 'Mentor', 'Presenter', 'Facilitator', 'Participant']:
		try:
			headers.remove(column)
		except:
			pass

	#Dynamically find the most recent survey column to compute on fire status later
	max_survey_column = sorted([h if h.find("DWN Survey")!=-1 else '' for h in headers])[-1]
	on_fire_index = headers.index('On Fire Status')

	final_data.append(headers)

	print('Starting to run through coaches')
	
	for coach_dict in all_coaches:
		#Create a container for coach rows while we calculate on fire status
		coach_new_rows = []
		coach = coach_dict['fields']

		#On fire status calculation
		#Calculate dynamically as you loop through
		on_fire_status = 0
		major_event_count = 0
		took_DWN_survey = False
		if max_survey_column in coach and coach[max_survey_column] == "Yes":
			took_DWN_survey = True
		
		#Set up demographics row
		demographics = [coach[field] if field in coach else ''\
							 for field in headers[:len(headers)-5]]

		#Gather all events in a dictionary to loop through
		coach_events = {}
		print('Current coach: {0} {1}'.format(coach['First'].encode(), \
												coach['Last'].encode()))

		#Use this to see if a coach hasn't been to any events. If that is the case
		#we need to add a row for them to all data anyway so that we can access their
		#info
		distinct_event_count = 0

		if 'Chair' in coach:
			coach_events['Chair'] = coach['Chair']
			distinct_event_count += 1
		if 'Head TF' in coach:
			coach_events['head_tf'] = coach['Head TF']
			distinct_event_count += 1
		if 'TF' in coach:
			coach_events['TF'] = coach['TF']
			distinct_event_count += 1
		if 'Mentor' in coach:
			coach_events['Mentor'] = coach['Mentor']
			distinct_event_count += 1
		if 'Presenter' in coach:
			coach_events['Presenter'] = coach['Presenter']
			distinct_event_count += 1
		if 'Facilitator' in coach:
			coach_events['Facilitator'] = coach['Facilitator']
			distinct_event_count += 1
		if 'Participant' in coach:
			coach_events['Participant'] = coach['Participant']
			distinct_event_count += 1

		#Coach hasn't been to any events. Add one row to final_data for them 
		#anyway so they are included in the data
		if distinct_event_count == 0:
			#Calculate on fire status, update airtable
			on_fire_status = 1 if took_DWN_survey else 0
			fields = {'On Fire Status': str(on_fire_status)}
			coaches_table.update(coach_dict['id'], fields)
			#and update demographics row
			new_row = demographics + ['', '', '', '', '']
			new_row[on_fire_index] = on_fire_status
			final_data.append(new_row)
			continue


		#Loop through events, get info about event from events table
		today = date.today()
		for event_role in coach_events:
			event_list = coach_events[event_role]
			for event_id in event_list:
				event_record = events_table.get(event_id)['fields']
				event_type = event_record['Event Type']
				event_date = event_record['Date']
				event_program = event_record['Program']
				
				#Check if the event and role count as a major event
				#Use the event date to compute whether it was in the last three years
				if event_program not in ["DWN", "DWCC"] and event_role != "Participant":
					date_split = event_date.split('-')
					event_date_object = date(int(date_split[0]),int(date_split[1]),int(date_split[2].split('T')[0]))
					date_diff = today - event_date_object
					if date_diff.days/365 <= 3.0:
						major_event_count += 1

				duration = compute_duration(event_program, event_type, event_role)

				#Only add independent columns to coach new rows until we have calculated On Fire
				new_row = [event_program, event_type, event_date,\
							duration, event_role]
				coach_new_rows.append(new_row)

		#Calculate on fire status, update airtable, update demos
		on_fire_status = compute_on_fire(took_DWN_survey, major_event_count)
		fields = {'On Fire Status': str(on_fire_status)}
		coaches_table.update(coach_dict['id'], fields)
		demographics[on_fire_index] = on_fire_status

		#When we're done with all one coach, add demographics and add all their rows
		final_data += [demographics + row for row in coach_new_rows]

		#Get rid of after testing
		#break

	appendToSheets(final_data)

	#Local solution
	'''with open('final_data.csv', 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerows(final_data)'''

def compute_on_fire(took_DWN_survey, major_event_count):
	
	if took_DWN_survey and major_event_count >= 2:
		return 4
	elif took_DWN_survey and major_event_count == 1:
		return 3
	elif not took_DWN_survey and major_event_count >= 1:
		return 2
	elif took_DWN_survey and major_event_count == 0:
		return 1
	else:
		return 0

def compute_duration(program, event_type, role):
	if event_type == "Program":
		if program in ["DWI", "DWJ", "DWO", "DWSB", "DWAU", "DWH"]:
			return 5 if role == "Presenter" else 40
		elif program == "DWA": 
			return 40
		elif program == "DWCC":
			return 40 if role == "Chair" else 20
	elif event_type == "Portfolio Review":
		return 2
	elif event_type == "Consultancy" or event_type == "Resource Sharing":
		return 1
	elif event_type == "Midsummer Check-In":
		return 1
	elif program == "DWL":
		return 40
	else:
		return 2

def appendToSheets(final_data):

	SCOPES = 'https://www.googleapis.com/auth/spreadsheets'

	store = file.Storage('token.json')
	creds = store.get()
	if not creds or creds.invalid:
		flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
		creds = tools.run_flow(flow, store)
	service = build('sheets', 'v4', http=creds.authorize(Http()))

	# Call the Sheets API

	data_sheet_id = '1zzNdAYvudf-TE7lx91oFFdOltX3SB_W9a8N6A5aXrlU'
	
	body = {
		'values': final_data
	}

	#Dynamically create data range based on number of columns in header
	num_cols = len(final_data[0])
	col, rem = divmod(num_cols, 26)
	letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
	data_range = 'A:' + letters[col-1] + letters[rem-1]

	#Paste the data. Automatically overwrites whatever was already there. 
	put_result = service.spreadsheets().values().update(
		spreadsheetId=data_sheet_id, range=data_range,
		valueInputOption='USER_ENTERED', body=body).execute()

	print('{0} cells added to overall data sheet.'.format(put_result \
										   .get('updatedCells')))


if __name__ == '__main__':
	run()