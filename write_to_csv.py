import csv
from sys import argv




def main(program, year, day, survey_id):

	with open('public/data/uploaded_surveys.csv', 'a') as csvfile:
	    writer = csv.writer(csvfile)
	    writer.writerow([program, year, day, survey_id])


if __name__ == '__main__':
	script, program, year, day, survey_id = argv
	main(program, year, day, survey_id)