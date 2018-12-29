import csv
from sys import argv


def main(sid):

	with open('public/data/uploaded_surveys.csv', 'r') as csvfile:
	    reader = csv.DictReader(csvfile)
	    for row in reader:
	    	if row['ID'] == sid:
	    		print('MATCH')
	    		return

	print('NO MATCH')
	return


if __name__ == '__main__':
	script, sid = argv
	main(sid)