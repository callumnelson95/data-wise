# Python 3
from __future__ import print_function
from sys import argv
from httplib2 import Http
from oauth2client import file, client, tools
from googleapiclient.discovery import build
import requests
import zipfile
import json
import io, os

import csv
import re

# Setting user Parameters
def main(survey, sid, api_key):
	try:
		apiToken = api_key
	except KeyError:
		print("set environment variable X_API_TOKEN")
		sys.exit(2) 


	survey_ids = {
		survey: sid
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
	#download historical files, loop through, normalize, and upload
	#Once this is done, then we only need to run main
	path_names = {

		'2018_DWI_Monday': 'DWI18 Monday Feedback Survey.csv',
		'2018_DWI_Tuesday': 'DWI18 Tuesday Feedback Survey.csv',
		'2018_DWI_Wednesday': 'DWI18 Wednesday Feedback Survey.csv',
		'2018_DWI_Thursday': 'DWI18 Thursday Feedback Survey.csv',
		'2018_DWI_Friday': 'DWI18 Friday Feedback Survey.csv',
		'2018_DWJ_Monday': 'DWJ18 Monday Feedback Survey.csv',
		'2018_DWJ_Tuesday': 'DWJ18 Tuesday Feedback Survey.csv',
		'2018_DWJ_Wednesday': 'DWJ18 Wednesday Feedback Survey.csv',
		'2018_DWJ_Thursday': 'DWJ18 Thursday Feedback Survey.csv',
		'2018_DWJ_Friday': 'DWJ18 Friday Feedback Survey.csv',
		'2016_DWA': 'DWA16 End Feedback Survey.csv',
		'2017_DWA': 'DWA17 End Feedback Survey.csv',
		'2018_DWO': 'DWO18 End Feedback Survey.csv'

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


		'''if program != 'DWO':
			continue'''

		path_to_file = r'Historical/' + path_names[path] + ''

		with open(path_to_file, 'r', newline='',encoding='utf-8') as raw_file:
			reader = csv.reader(raw_file)
			for row in reader:
				values.append(row)

		normalize_crosstab(values, program, year, day)
		
		



def normalize_crosstab(values, program, year, day):

	question_search_dict = {
		'DWH': {re.compile('rate the overall quality'): ['Quality', 'How would you rate the overall quality of this program?'],
				re.compile('intellectually challenging'): ['Challenge', "Today's class and activities were intellectually challenging"],
				re.compile('equity is central'): ['Equity1', "Today's sessions helped me articulate how and why equity is central to the work of school improvement"],
				re.compile('foster equitable practices'): ['Equity2',"Today's sessions helped me build skills to use Data Wise tools to foster equitable practices at each step of the improvement process"],
				re.compile('team.*norms'): ['Team Norms',"In the team that you came to Harvard with, how well are you and your colleagues following norms?"],
				re.compile('group.*norms'): ['Group Norms', "To what extent did your case group practice our Data Wise norms today?"],
				re.compile('professionally useful'): ['Useful', "To what extent did you find the Data Wise course professionally useful?"],
				re.compile('modify your professional practice'): ['Modify', "How much do you intend to modify your professional practice, based on your experience in the Data Wise course?"],
				re.compile("diversity of.*learning.*community"): ['Diversity', "How satisfied were you with the diversity of the course's learning community, inclusive of racial, ethnic, professional, personal, regional, institution type, and other perspectives and backgrounds?"],
				re.compile('scale of 0 to 10'): ['Recommend', 'On a scale of 0 to 10, how likely is it that you would recommend the Data Wise Leadership Institute to a friend or colleague?'],
				re.compile('testimonial'): ['Testimonial', 'Please use the space below to share your testimonial'],
				re.compile('support.*staff'): ['Support', 'Please indicate your satisfaction with the support from the program staff']
				},
		'DWJ': {re.compile('rate the overall quality'): ['Quality', 'How would you rate the overall quality of this program?'],
				re.compile('intellectually challenging'): ['Challenge', "Today's class and activities were intellectually challenging"],
				re.compile('equity is central'): ['Equity1', "Today's sessions helped me articulate how and why equity is central to the work of school improvement"],
				re.compile('service of equity'): ['Equity2',"Today's class and activities helped me reflect on how Data Wise tools could be used in the service of equity"],
				re.compile('team.*norms'): ['Team Norms',"In the team that you came to Harvard with, how well are you and your colleagues following norms?"],
				re.compile('group.*norms'): ['Group Norms', "To what extent did your case group practice our Data Wise norms today?"],
				re.compile('professionally useful'): ['Useful', "To what extent did you find the Data Wise course professionally useful?"],
				re.compile('modify your professional practice'): ['Modify', "How much do you intend to modify your professional practice, based on your experience in the Data Wise course?"],
				re.compile("diversity of.*learning.*community"): ['Diversity', "How satisfied were you with the diversity of the course's learning community, inclusive of racial, ethnic, professional, personal, regional, institution type, and other perspectives and backgrounds?"],
				re.compile('scale of 0 to 10'): ['Recommend', 'On a scale of 0 to 10, how likely is it that you would recommend the Data Wise Leadership Institute to a friend or colleague?'],
				re.compile('testimonial'): ['Testimonial', 'Please use the space below to share your testimonial'],
				re.compile('support.*staff'): ['Support', 'Please indicate your satisfaction with the support from the program staff']
				},
		'DWI': {re.compile('rate the overall quality'): ['Quality', 'How would you rate the overall quality of this program?'],
				re.compile('equity is central'): ['Equity1', "Today's sessions helped me articulate how and why equity is central to the work of school improvement"],
				re.compile('service of equity'): ['Equity2',"Today's class and activities helped me reflect on how Data Wise tools could be used in the service of equity"],
				re.compile('team.*norms'): ['Team Norms',"In the team that you came to Harvard with, how well are you and your colleagues following norms?"],
				re.compile('group.*norms'): ['Group Norms', "To what extent did your case group practice our Data Wise norms today?"],
				re.compile('professionally useful'): ['Useful', "To what extent did you find the Data Wise course professionally useful?"],
				re.compile('modify your professional practice'): ['Modify', "How much do you intend to modify your professional practice, based on your experience in the Data Wise course?"],
				re.compile("diversity of.*learning.*community"): ['Diversity', "How satisfied were you with the diversity of the course's learning community, inclusive of racial, ethnic, professional, personal, regional, institution type, and other perspectives and backgrounds?"],
				re.compile('scale of 0 to 10'): ['Recommend', 'On a scale of 0 to 10, how likely is it that you would recommend the Data Wise Leadership Institute to a friend or colleague?'],
				re.compile('testimonial'): ['Testimonial', 'Please use the space below to share your testimonial'],
				re.compile('support.*staff'): ['Support', 'Please indicate your satisfaction with the support from the program staff']
				},
				#For components, you'll also need to list the component -- split on "-"
		'DWO': {re.compile('components'): ['Components', 'Please rate the extent to which each of the following components helped you to prepare to launch the Data Wise Improvement Process at your site'],
				re.compile('rate the overall quality'): ['Quality', 'How would you rate the overall quality of this program?'],
				re.compile('professionally useful'): ['Useful', "To what extent did you find the Data Wise course professionally useful?"],
				re.compile('modify your professional practice'): ['Modify', "How much do you intend to modify your professional practice, based on your experience in the Data Wise course?"],
				re.compile('scale of 0 to 10'): ['Recommend', 'On a scale of 0 to 10, how likely is it that you would recommend the Data Wise Leadership Institute to a friend or colleague?'],
				re.compile('testimonial'): ['Testimonial', 'Please use the space below to share your testimonial'],
				re.compile('learning objectives'): ['Objectives', 'Please indicate to what extent these learning objectives were effectively covered during the course'],
				re.compile('support.*staff'): ['Support', 'Please indicate your satisfaction with the support from the program staff']
				},
		'DWA': {re.compile('components'): ['Components', 'Please rate the extent to which each of the following components helped you to prepare to launch the Data Wise Improvement Process at your site'],
				re.compile('rate the overall quality'): ['Quality', 'How would you rate the overall quality of this program?'],
				re.compile('professionally useful'): ['Useful', "To what extent did you find the Data Wise course professionally useful?"],
				re.compile('modify your professional practice'): ['Modify', "How much do you intend to modify your professional practice, based on your experience in the Data Wise course?"],
				re.compile('scale of 0 to 10'): ['Recommend', 'On a scale of 0 to 10, how likely is it that you would recommend the Data Wise Leadership Institute to a friend or colleague?'],
				re.compile('testimonial'): ['Testimonial', 'Please use the space below to share your testimonial'],
				re.compile('learning objectives'): ['Objectives', 'Please indicate to what extent these learning objectives were effectively covered during the course'],
				re.compile('support.*staff'): ['Support', 'Please indicate your satisfaction with the support from the program staff']
				},
		'DWAU': {re.compile('rate the overall quality'): ['Quality', 'How would you rate the overall quality of this program?'],
				re.compile('equity is central'): ['Equity1', "Today's sessions helped me articulate how and why equity is central to the work of school improvement"],
				re.compile('service of equity'): ['Equity2',"Today's class and activities helped me reflect on how Data Wise tools could be used in the service of equity"],
				re.compile('team.*norms'): ['Team Norms',"In the team that you came to Harvard with, how well are you and your colleagues following norms?"],
				re.compile('group.*norms'): ['Group Norms', "To what extent did your case group practice our Data Wise norms today?"],
				re.compile('professionally useful'): ['Useful', "To what extent did you find the Data Wise course professionally useful?"],
				re.compile('modify your professional practice'): ['Modify', "How much do you intend to modify your professional practice, based on your experience in the Data Wise course?"],
				re.compile("diversity of.*learning.*community"): ['Diversity', "How satisfied were you with the diversity of the course's learning community, inclusive of racial, ethnic, professional, personal, regional, institution type, and other perspectives and backgrounds?"],
				re.compile('scale of 0 to 10'): ['Recommend', 'On a scale of 0 to 10, how likely is it that you would recommend the Data Wise Leadership Institute to a friend or colleague?'],
				re.compile('testimonial'): ['Testimonial', 'Please use the space below to share your testimonial'],
				re.compile('support.*staff'): ['Support', 'Please indicate your satisfaction with the support from the program staff']
				},
		'DWN': [],

	}

	firstDataCol, role_col, team_col = getDataRoleTeamCols(values)
	numDataCols = len(values[0]) - firstDataCol
	
	raw_headers = values[0]
	headers = values[1]

	overallRows = []
	sessionRows = []

	overallHeader = ['Start Date','End Date','Response Type','IP Address','Progress','Duration (in seconds)','Finished','Recorded Date','Response ID',
				'Recipient Last Name','Recipient First Name','Recipient Email','External Data Reference','Location Latitude','Location Longitude','Distribution Channel','User Language']

	sessionHeader = ['Start Date','End Date','Response Type','IP Address','Progress','Duration (in seconds)','Finished','Recorded Date','Response ID',
				'Recipient Last Name','Recipient First Name','Recipient Email','External Data Reference','Location Latitude','Location Longitude','Distribution Channel','User Language']
  
  	#Should we add a column for 'Question Category'
  	#e.g. norms, equity, etc
	overallHeader.append('Role')
	overallHeader.append('Team')
	overallHeader.append('Program')
	overallHeader.append('Year')
	overallHeader.append('Day')
	overallHeader.append('Question Number')
	overallHeader.append('Question Category')
	overallHeader.append('Question Text')
	overallHeader.append('Response')
	overallRows.append(overallHeader)

	sessionHeader.append('Role')
	sessionHeader.append('Team')
	sessionHeader.append('Program')
	sessionHeader.append('Year')
	sessionHeader.append('Day')
	sessionHeader.append('Session Type')
	sessionHeader.append('Session')
	sessionHeader.append('Session Leader')
	sessionHeader.append('Question')
	sessionHeader.append('Response')
	sessionHeader.append('Plus')
	sessionHeader.append('Delta')
	sessionRows.append(sessionHeader)

	for i in range(3, len(values)):
		row = values[i]

		#Don't want these responses to be collected in our data
		if row[2] == 'Survey Preview':
			continue

		role = ''
		team = ''
		if program == 'DWO' or program == 'DWA' or program == 'DWH':
			role = 'Practitioner'
			team = 'School Team'
		else:
			if role_col == 0:
				role = 'N/A'
			else:
				role = row[role_col]

			if team_col == 0:
				team = 'N/A'
			else:
				team = row[team_col]

		#These are the only programs with sessions, so they're the only ones
		#we want to look for sessions in
		if program == 'DWJ' or program == 'DWI' or program == 'DWAU' or program == 'DWH':

			current_type = ''
			current_session = ''
			current_leader = ''

			for datacol in range(numDataCols):
				newRow = row[0:firstDataCol]
				question_number = raw_headers[firstDataCol + datacol]
				question_text = headers[firstDataCol + datacol].replace('\n','')
				response = row[firstDataCol + datacol]

				if response == '' or response == ' ':
					continue

				if type(response) is str and response.find('\n') != -1:
					response = response.replace('\n', ' ')


				m = re.search('\[([^\s]+) Session\]', question_text)
				
				# CASE 1: A session has been found, deal with it appropriately
				# and append the results to the sessionOverall list of rows
				if m is not None:

					plus = ''
					delta = ''
					second_metric_found = False
					second_question = ''
					second_response = ''
					newRow1 = row[0:firstDataCol]

					#Organize first session
					split_string = re.split('[\[|\]|\(|\)|-]', question_text)
					split_string.pop(0)
					session_type = split_string[0].strip()
					session = split_string[1].strip()
					session_leader = split_string[2].strip()

					#Don't do everything over for the next column
					#We'll have duplicates and that's BAD
					if session == current_session:
						continue

					question = split_string[-1].strip()
					session_response = response.strip()
					if session_response == '' or session_response == ' ':
						session_response = 'Blank'

					#Find the second metric, plusses, and deltas in the adjacent three columns
					for j in range(datacol+1,datacol+4):
						next_question_text = headers[firstDataCol + j].replace('\n','')
						if re.search('\[([^\s]+) Session\]', next_question_text) is not None:
							second_metric_found = True
							second_split = re.split('[\[|\]|\(|\)|-]', next_question_text)
							second_split.pop(0)
							second_question = second_split[-1].strip()
							second_response = row[firstDataCol + j].replace('\n',' ').strip()
							if second_response == '' or second_response == ' ':
								second_response = 'Blank'
						elif re.search('What worked well.*about.*(session|case discussion)', next_question_text) is not None:
							#next_question = 'What worked well about this session?'
							plus = row[firstDataCol + j].replace('\n',' ')
							if plus == '' or plus == ' ':
								plus = 'Blank'
						elif re.search('What would you.*change.*about.*(session|case discussion)', next_question_text) is not None:
							#next_question = 'What would you have liked to change about this session?'
							delta = row[firstDataCol + j].replace('\n',' ')
							if delta == '' or delta == ' ':
								delta = 'Blank'

					split_string = re.split('[\[|\]|\(|\)|-]', question_text)
					split_string.pop(0)
					session_type = split_string[0].strip()
					session = split_string[1].strip()
					session_leader = split_string[2].strip()

					question = split_string[-1].strip()
					session_response = response.strip()

					#Add first row
					newRow.append(role)
					newRow.append(team)
					newRow.append(program)
					newRow.append(year)
					newRow.append(day)
					newRow.append(session_type)
					newRow.append(session)
					newRow.append(session_leader)
					newRow.append(question)
					newRow.append(session_response)
					newRow.append(plus)
					newRow.append(delta)
					sessionRows.append(newRow)
					#newRow = row[0:firstDataCol]

					if second_metric_found == True:
						newRow1.append(role)
						newRow1.append(team)
						newRow1.append(program)
						newRow1.append(year)
						newRow1.append(day)
						newRow1.append(session_type)
						newRow1.append(session)
						newRow1.append(session_leader)
						newRow1.append(second_question)
						newRow1.append(second_response)
						newRow1.append(plus)
						newRow1.append(delta)
						sessionRows.append(newRow1)

				
					current_type = session_type
					current_session = session
					current_leader = session_leader

					#Skip the next column so that we don't end up with duplicates

				#Depending on Program, look to see if question text is a different question that we care about
				#Add to overallRows if it is
				else:
					#print(question_text)
					for regex in question_search_dict[program]:

						m = regex.search(question_text)

						if m is not None:
							question_category = question_search_dict[program][regex][0]
							if question_category == 'Recommend':
								response = response.split(' ')[0]
							new_question_text = question_search_dict[program][regex][1]
							if question_category is 'Team Norms' or question_category is 'Group Norms' or question_category is 'Components' or question_category is 'Objectives' or question_category is 'Support':
								new_question_text = question_text.split("-")[-1].strip()
							newRow.append(role)
							newRow.append(team)
							newRow.append(program)
							newRow.append(year)
							newRow.append(day)
							newRow.append(question_number)
							newRow.append(question_category)
							newRow.append(new_question_text)
							newRow.append(response)
							overallRows.append(newRow)



		#Otherwise we're just looking for overall questions for programs
		else:

			for datacol in range(numDataCols):
				newRow = row[0:firstDataCol]
				question_number = raw_headers[firstDataCol + datacol]
				question_text = headers[firstDataCol + datacol].replace('\n','')
				response = row[firstDataCol + datacol]

				if response == '' or response == ' ':
					continue

				if type(response) is str and response.find('\n') != -1:
					response = response.replace('\n', ' ')
				
				for regex in question_search_dict[program]:

					m = regex.search(question_text)

					if m is not None:

						question_category = question_search_dict[program][regex][0]
						if question_category == 'Recommend':
							response = response.split(' ')[0]
						new_question_text = question_search_dict[program][regex][1]
						if question_category is 'Team Norms' or question_category is 'Group Norms' or question_category is 'Components' or question_category is 'Objectives' or question_category is 'Support':
							new_question_text = question_text.split("-")[-1].strip()

						newRow.append(role)
						newRow.append(team)
						newRow.append(program)
						newRow.append(year)
						newRow.append(day)
						newRow.append(question_number)
						newRow.append(question_category)
						newRow.append(new_question_text)
						newRow.append(response)
						overallRows.append(newRow)

		#break
	
	'''with open('test/output.csv', 'w') as outfile:
		writer = csv.writer(outfile)
		writer.writerows(sessionRows)'''


	appendToSheets(sessionRows, overallRows)


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
	script, survey, sid, api_key = argv
	main(survey, sid, api_key)
	






