import csv
from sys import argv




def main(program, year, day):

	with open('public/data/uploaded_surveys.csv', 'a') as csvfile:
	    writer = csv.writer(csvfile)
	    writer.writerow([])
	    writer.writerow([program, year, day])


if __name__ == '__main__':
	script, program, year, day = argv
	main(program, year, day)