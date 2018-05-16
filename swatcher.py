#!/usr/bin/python

import argparse
import time
from datetime import datetime

import swa
import configuration

DEFAULT_CONFIGURATION_FILE = "swatcher.ini"

class state(object):

	def __init__(self):
		self.errorCount = 0
		self.currentFare = 0
		self.blockQuery = False


class swatcher(object):

	def __init__(self):
		self.state = []
	
	@staticmethod
	def now():
		return datetime.now().strftime('%Y-%m-%d %H:%M:%S') 

	@staticmethod
	def parseArguments():

		parser = argparse.ArgumentParser(description = "swatcher.py: Utility to monitor SWA for fare price changes")

		parser.add_argument('-f', '--file',
			dest = 'configurationFile',
			help = "Configuration file to use. If unspecified, will be '" + DEFAULT_CONFIGURATION_FILE + "'",
			default = DEFAULT_CONFIGURATION_FILE)

		args = parser.parse_args()

		return args

	def sendNotification(notification, message):

		print(self.now() + ": SENDING NOTIFICATION!!! '" + message + "'");

	def findLowestiFareSpecificFlight(trip, flights, departure):

		if(departure and not trip.departureFlight):
			specificFlight = trip.departureFlight
		elif(not departure and not trip.returnFlight):
			specificFlight = trip.returnFlight
		else: 
			specificFlight = ''

		if(specificFlight):
			for flight in flights:
				if(flight['flight'] == specificFlight):
					return flight['fare']
			return 0
		return -1
	

	def findLowestFare(trip, flights, departure)

		fare = findLowestFareSpecificFlight(trip, flights, departure) 

		if
			return -1			


		return 0


	def processTrips(self, config):
		for trip in config.trips:

			if(self.state[trip.index].blockQuery):
				return True;

			print(self.now() + ": Querying flight '" + trip.description + "'");

			try:
				swa.scrape(
					browser = config.browser,
					originationAirportCode = trip.originationAirportCode,
					destinationAirportCode = trip.destinationAirportCode,
					departureDate = trip.departureDate,
					departureTimeOfDay = trip.departureTimeOfDay,
					returnDate = trip.returnDate,
					returnTimeOfDay = trip.returnTimeOfDay,
					tripType = trip.type,
					adultPassengersCount = trip.adultPassengersCount,
					debug = config.debug
				)
			except swa.scrapeValidationError as e:
				print(e)
				print("\nValidation errors are not retryable, so swatcher is exiting")
				return False
			except Exception as e:
				print(e)
				self.state[trip.index].errorCount += 1
				if(self.state[trip.index].errorCount == 10):
					self.state[trip.index].blockQuery = True;
				self.sendNotification(config.notification, "For trip '" + trip.description + "' ceasing queries due to frequent errors")

				# If here, successfully scraped, so reset errorCount
			self.state[trip.index].errorCount = 0

			
				
		return True	

	def main(self):

		args = self.parseArguments();
		print(self.now() + ": Parsing configuration file '" + args.configurationFile +"'")

		try:
			config = configuration.configuration(args.configurationFile)
		except Exception as e:
			print("Error in processing configuration file: " + str(e))
			quit()

		self.state = [state() for i in xrange(len(config.trips))]	

		while True:
		
			if(not self.processTrips(config)):
				break

			time.sleep(config.pollInterval * 60)

		return

	
if __name__ == "__main__":
	swatcher = swatcher()	

	swatcher.main()
