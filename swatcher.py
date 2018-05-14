#!/usr/bin/python

import argparse

import swa
import configuration


DEFAULT_CONFIGURATION_FILE = "swatcher.ini"

def parseArguments():

	parser = argparse.ArgumentParser(description = "swatcher.py: Utility to monitor SWA for fare price changes")

	parser.add_argument('-f', '--file',
		dest = 'configurationFile',
		help = "Configuration file to use. If unspecified, will be '" + DEFAULT_CONFIGURATION_FILE + "'",
		default = DEFAULT_CONFIGURATION_FILE)

	args = parser.parse_args()

	return args


def main():

	args = parseArguments();

	print("Parsing configuration file '" + args.configurationFile +"'")

	try:
		config = configuration.configuration(args.configurationFile)
	except Exception as e:
		print("Error in processing configuration file: " + str(e))
		quit()

	print(str(config.__dict__))

	try:
		print swa.scrape(
			originationAirportCode = 'MDW',
			destinationAirportCode = 'DEN',
			departureDate = '2018-05-15',
			returnDate = '2018-05-17',
			tripType = 'roundtrip'
		)
	except swa.scrapeValidationError as e:
		print(e)
		print("\nValidation errors are not retryable, so swatcher is exiting")
		quit()
	
if __name__ == "__main__":
	main()
