#!/usr/bin/python

import argparse
import time
import smtplib
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
	
	def now(self):
		return datetime.now().strftime('%Y-%m-%d %H:%M:%S') 

	def parseArguments(self):

		parser = argparse.ArgumentParser(description = "swatcher.py: Utility to monitor SWA for fare price changes")

		parser.add_argument('-f', '--file',
			dest = 'configurationFile',
			help = "Configuration file to use. If unspecified, will be '" + DEFAULT_CONFIGURATION_FILE + "'",
			default = DEFAULT_CONFIGURATION_FILE)

		args = parser.parse_args()

		return args

	def sendNotification(self, notification, message):

		print(self.now() + ": SENDING NOTIFICATION!!! '" + message + "'")

		if(notification.type == 'smtp'):
			try:
				server = smtplib.SMTP(notification.host, notification.port)

				if(notification.useAuth):
					server.login(notification.username, notification.password)

				mailMessage = """From: %s\nTo: %s\nX-Priority: 2\nSubject: %s\n\n """ % (notification.sender, notification.recipient, message)
				print mailMessage
				server.sendmail(notification.sender, notification.recipient, mailMessage)
				server.quit()

			except Exception as e: 
				print(self.now() + ": UNABLE TO SEND NOTIFICATION DUE TO ERROR - " + str(e))
			return
 	
 
	def findLowestFareInSegment(self,trip, segment):

		lowestCurrentFare = None

		specificFlights = []
		if(trip.specificFlights):
			specificFlights = [x.strip() for x in trip.specificFlights.split(',')]
	
		for flight in segment:

				# If flight is sold-out or otherwise unavailable, no reason to process further
			if(flight['fare'] is None):
				continue

				# Now, see if looking for specificFlights - if this is set, all other rules do not matter...
			if(len(specificFlights) and (flight['flight'] not in specificFlights)):
				continue
				
			if(trip.maxStops < flight['stops']):
				continue

			if((trip.maxDuration > 0.0) and (trip.maxDuration < flight['duration'])):
				continue

			if((trip.maxPrice > 0) and (trip.maxPrice < flight['fare'])):
				continue

			if(lowestCurrentFare is None):
				lowestCurrentFare = flight['fare']
			elif(flight['fare'] < lowestCurrentFare):
				lowestCurrentFare = flight['fare']

		return lowestCurrentFare


	def processTrips(self, config):
		for trip in config.trips:

			if(self.state[trip.index].blockQuery):
				return True;

			print(self.now() + ": Querying flight '" + trip.description + "'");

			try:
				segments = swa.scrape(
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
			for segment in segments:
				lowestFare = self.findLowestFareInSegment(trip, segment)
				
				self.sendNotification(config.notification, "Lowest segment fare: " + str(lowestFare))
				
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
