# Python 3
from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import requests
import zipfile
import json
import io, os
import sys
import csv
import re

# Setting user Parameters
def main():
	try:
		apiToken = os.environ['X_API_TOKEN']
	except KeyError:
		print("set environment variable X_API_TOKEN")
		sys.exit(2) 


	survey_ids = {
		
		#'2018_DWN' : 'SV_d0Z3XrdLH1zxsNv',
		'2019_DWN' : 'SV_5BUk30cSPDBLijX'
	}

	for survey_name in survey_ids:

		surveyId = survey_ids[survey_name]
		fileFormat = "csv"
		dataCenter = "harvard.az1"

		# Setting static parameters
		requestCheckProgress = 0.0
		progressStatus = "inProgress"
		baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}/export-responses/".format(dataCenter, surveyId)
		headers = {
			"content-type": "application/json",
			"x-api-token": apiToken,
			}

		# Step 1: Creating Data Export
		downloadRequestUrl = baseUrl
		downloadRequestPayload = '{"format":"' + fileFormat + '","useLabels":"true"}'
		downloadRequestResponse = requests.request("POST", downloadRequestUrl, data=downloadRequestPayload, headers=headers)
		progressId = downloadRequestResponse.json()["result"]["progressId"]
		print(downloadRequestResponse.text)

		# Step 2: Checking on Data Export Progress and waiting until export is ready
		while progressStatus != "complete" and progressStatus != "failed":
			print ("progressStatus=", progressStatus)
			requestCheckUrl = baseUrl + progressId
			requestCheckResponse = requests.request("GET", requestCheckUrl, headers=headers)
			requestCheckProgress = requestCheckResponse.json()["result"]["percentComplete"]
			print("Download is " + str(requestCheckProgress) + " complete")
			progressStatus = requestCheckResponse.json()["result"]["status"]

		#step 2.1: Check for error
		if progressStatus is "failed":
			raise Exception("export failed")

		fileId = requestCheckResponse.json()["result"]["fileId"]

		# Step 3: Downloading file
		requestDownloadUrl = baseUrl + fileId + '/file'
		requestDownload = requests.request("GET", requestDownloadUrl, headers=headers, stream=True)

		# Step 4: Unzipping the file
		file = zipfile.ZipFile(io.BytesIO(requestDownload.content))
		file.extractall(survey_name)

		file_name = file.namelist()[0]
		csv_path = r'' + survey_name + '/' + file_name + ''

		# Step 5: put all values from CSV into a list so we can loop through for normalization
		values = []

		#replace test with csv_path when you're ready
		with open(csv_path, 'r', newline='') as raw_file:
			reader = csv.reader(raw_file)
			for row in reader:
				values.append(row)

		#print(values)

		survey_info = survey_name.split("_")
		
		year = survey_info[0]
		program = survey_info[1]
		day = ''
		if len(survey_info) == 2: 
			day = 'N/A'
		else: 
			day = survey_info[2]

		print(program + ' ' + year + ' ' + day)
		
		normalize_crosstab(values, program, year, day)

def historical():

	path_names = {

		#'2018_DWN' : 'DWN18 Data Wise Coach Network Impact Survey.csv'
		'2019_DWN' : 'DWN19 Data Wise Coach Network Survey.csv'

	}

	for path in path_names:
		print(path)

		values = []

		split = path.split("_")
		year = split[0]
		program = split[1]
		day = 'N/A'
		if len(split) == 3:
			day = split[2]


		#if path != '2018_DWI_Thursday':
		#	continue

		path_to_file = path + '/' + path_names[path] + ''

		with open(path_to_file, 'r', newline='',encoding='latin-1') as raw_file:
			reader = csv.reader(raw_file)
			for row in reader:
				values.append(row)

		normalize_crosstab(values, program, year, day)

def normalize_crosstab(values, program, year, day):

	##READ ME!!!!!##

	##Whenever you add a new survey, create the question lookups you want here. 
	##The most important step is to add any of the radio multi-select question
	##types to the list in line 204. This will format the output correctly

	question_search_dict = {
		
		'2019DWN': {re.compile('following activities'): ['Using DW', 'Please indicate your past engagement and future plans around the following engagement activities'],
				re.compile('following outreach activities'): ['Sharing DW', 'Please indicate your past engagement and future plans around the following outreach activities'],
				re.compile('opportunities to work with Data Wise Institutes'): ['Teaching DW', 'Please select the type(s) of programs that you are interested in working with'],
				re.compile('virtual learning opportunities'): ['Learning DW', 'Which of the following virtual learning opportunities do you plan to attend?'],
				re.compile('training outside of your own organization'): ['Other1', 'Did you provide Data Wise or Meeting Wise training outside of your own organization in the last year?'],
				re.compile('Data Wise Impact Workshop'): ['Other2', 'Are you planning on attending the Data Wise Impact Workshop September 29-30, 2020 in Cambridge?'],
				re.compile('to impact learning, teaching,'): ['Impact Story', 'In a few sentences, please tell us a story about a way in which you have used Data Wise or Meeting Wise to impact learning, teaching, and/or building equitable schools in the last year.'],
				re.compile('anything else you want'): ['Anything Else', 'Is there anything else you want us to know?'],
				re.compile('feedback on the DWN Vision'): ['Other Feedback', 'Please provide any feedback on the DWN Vision']
		},
		'2018DWN': {re.compile('in your own context'): ['Using DW', 'Using Data Wise or Meeting Wise in your own context'],
				re.compile('with a broader community'): ['Sharing DW', 'Sharing Data Wise or Meeting Wise with a broader community'],
				re.compile('learning opportunities'): ['Learning DW', 'Engaging in learning opportunities'],
				re.compile('formal paid work'): ['Teaching DW', 'Engaging in formal paid work with the Data Wise Project'],
				re.compile('other network opportunities'): ['Sharing DW', 'Enganging with other network opportunities'],
				re.compile('eligible to renew their membership'): ['Other1', 'Starting in 2020, do you think that coaches should have to say "yes" to some of the questions asked above in order to be eligible to renew their membership in DWN?'],
				re.compile('to impact learning, teaching,'): ['Impact Story', 'In a few sentences, please tell us a story about a way in which you have used Data Wise or Meeting Wise to impact learning, teaching, and/or building equitable schools in the last year.'],
				re.compile('anything else you want'): ['Anything Else', 'Is there anything else you want us to know?']
		},

	}

	firstDataCol, role_col, team_col = getDataRoleTeamCols(values)
	numDataCols = len(values[0]) - firstDataCol
	
	raw_headers = values[0]
	headers = values[1]

	overallRows = []
	sessionRows = []

	overallHeader = ['Start Date','End Date','Response Type','IP Address','Progress','Duration (in seconds)','Finished','Recorded Date','Response ID',
				'Recipient Last Name','Recipient First Name','Recipient Email','External Data Reference','Location Latitude','Location Longitude',
				'Distribution Channel','User Language']
  
	#Should we add a column for 'Question Category'
	#e.g. norms, equity, etc
	overallHeader.append('Full Name')
	overallHeader.append('Coach ID')
	overallHeader.append('Program')
	overallHeader.append('Year')
	overallHeader.append('Day')
	overallHeader.append('Question Number')
	overallHeader.append('Question Category')
	overallHeader.append('Question Text')
	overallHeader.append('Question Response Option')
	overallHeader.append('Response')
	overallRows.append(overallHeader)

	for i in range(3, len(values)):
		row = values[i]


		full_name = ''
		coach_id = ''


		for ind in range(len(headers)):
			if headers[ind].find('Please select your name') != -1:
				#remove ID to get full name
				full_name = row[ind].rsplit(' ', 1)[0]
				coach_id = row[ind].split(" ")[-1]


		for datacol in range(numDataCols):

			newRow = row[0:firstDataCol]
			question_number = raw_headers[firstDataCol + datacol]
			question_text = headers[firstDataCol + datacol].replace('\n','')
			response = row[firstDataCol + datacol]

			if type(response) is str and response.find('\n') != -1:
				response = response.replace('\n', ' ')
			
			for regex in question_search_dict[year+program]:

				m = regex.search(question_text)

				if m is not None:

					question_category = question_search_dict[year+program][regex][0]
					new_question_text = question_search_dict[year+program][regex][1]

					#Need to update question text if it's one of the multi-select question types
					#Add in question_response_option so we know what they option was even if they 
						#didn't select it
					question_response_option = ''
					if question_category in ['Using DW', 'Learning DW', 'Teaching DW', 'Sharing DW']:

						question_response_option = question_text.split("-")[-1].strip()
						#Bandaid solution for weird 2019 question
						if year == '2019' and question_category in ['Learning DW', 'Teaching DW']:
							new_question_text += ' - ' + question_text.split("-")[-1].strip()

						else:
							new_question_text += ' - ' + question_text.split("-")[-2].strip()

					#Skip other entries
					if new_question_text.find('Other') != -1 or question_number.find('TEXT') != -1:
						continue

					newRow.append(full_name)
					newRow.append(coach_id)
					newRow.append(program)
					newRow.append(year)
					newRow.append(day)
					newRow.append(question_number)
					newRow.append(question_category)
					newRow.append(new_question_text)
					newRow.append(question_response_option)
					newRow.append(response)
					overallRows.append(newRow)

		#break
	
	'''with open('test/sessions_output.csv', 'w') as outfile:
		writer = csv.writer(outfile)
		writer.writerows(sessionRows)'''

	with open('DWN_Surveys_All_Data.csv', 'a') as outfile:
		writer = csv.writer(outfile)
		#Don't add header since we've already created the file
		writer.writerows(overallRows[1:])


	#appendToSheets([], overallRows)


def getDataRoleTeamCols(values):
	#get data cols
	firstDataCol = 0
	#regex = re.compile('Q[0-9]')
	for i in range(len(values[0])):
		column = values[0][i]
		m = column.find('UserLanguage')
		if m != -1:
			firstDataCol = i + 1
			break

	role_col = 0
	#regex2 = re.compile('What is your role')
	for i in range(len(values[0])):
		column = values[1][i]
		m = column.find('What is your role')
		if m != -1:
			role_col = i
			break

	team_col = 0
	#regex3 = re.compile('team do you work with')
	for i in range(len(values[0])):
		column = values[1][i]
		m = column.find('kind of team')
		if m != -1:
			team_col = i
			break


	return firstDataCol, role_col, team_col


def appendToSheets(sessionRows, overallRows):

	SCOPES = 'https://www.googleapis.com/auth/spreadsheets'

	store = file.Storage('token.json')
	creds = store.get()
	if not creds or creds.invalid:
		flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
		creds = tools.run_flow(flow, store)
	service = build('sheets', 'v4', http=creds.authorize(Http()))

	# Call the Sheets API
	session_sheet_ID = '1NJogP8QxFWCiyHemt35EFeKNv02nNrBLTeAUiPCNCCM'
	
	body = {
		'values': sessionRows[1:]
	}
	result = service.spreadsheets().values().append(
		spreadsheetId=session_sheet_ID, range="A:AA",
		valueInputOption='USER_ENTERED', body=body).execute()

	print('{0} cells appended to sessions data sheet.'.format(result \
										   .get('updates') \
										   .get('updatedCells')))

	overall_sheet_ID = '1iG09yvrF112PiJkrT1-r24S5lHEDCWl5iy-NgeNLCcA'
	
	body = {
		'values': overallRows[1:]
	}
	result = service.spreadsheets().values().append(
		spreadsheetId=overall_sheet_ID, range="A:Z",
		valueInputOption='USER_ENTERED', body=body).execute()

	print('{0} cells appended to overall data sheet.'.format(result \
										   .get('updates') \
										   .get('updatedCells')))

if __name__ == '__main__':
	#main()
	historical()






