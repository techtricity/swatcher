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
		self.currentLowestFare = None 
		self.blockQuery = False
		self.firstQuery = True


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
					# importing this way keeps people who aren't interested in smtplib from installing it..
				smtplib = __import__('smtplib')
				if(notification.useAuth):
					server = smtplib.SMTP(notification.host, notification.port)
					server.ehlo()
					server.starttls()
					server.login(notification.username, notification.password)
				else:
					server = smtplib.SMTP(notification.host, notification.port)

				mailMessage = """From: %s\nTo: %s\nX-Priority: 2\nSubject: %s\n\n """ % (notification.sender, notification.recipient, message)
				server.sendmail(notification.sender, notification.recipient, mailMessage)
				server.quit()

			except Exception as e: 
				print(self.now() + ": UNABLE TO SEND NOTIFICATION DUE TO ERROR - " + str(e))
			return
		elif(notification.type == 'twilio'):
			try:
					# importing this way keeps people who aren't interested in Twilio from installing it..
				twilio = __import__('twilio.rest')

				client = twilio.rest.Client(notification.accountSid, notification.authToken)
				client.messages.create(to = notification.recipient, from_ = notification.sender, body = message)
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

	def processTrip(self, trip, config):
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
		except swa.scrapeValidation as e:
			print(e)
			print("\nValidation errors are not retryable, so swatcher is exiting")
			return False
		except swa.scrapeDatesNotOpen as e:
			if(self.state[trip.index].firstQuery):
				self.sendNotification(config.notification, "For '" + trip.description + "' dates do not appear open.")
				self.state[trip.index].firstQuery = False
			return True
		except swa.scrapeTimeout as e:
				# This could be a few things - internet or SWA website is down. 
				# it could also mean my WebDriverWait conditional is incorrect/changed. Don't know
				# what to do about this, so for now, just print to screen and try again at next loop
			print(self.now() + ": Timeout waiting for results, will retry next loop")
			return True
		except Exception as e:
			print(e)
			self.state[trip.index].errorCount += 1
			if(self.state[trip.index].errorCount == 10):
				self.state[trip.index].blockQuery = True;
				self.sendNotification(config.notification, "For '" + trip.description + "' ceasing queries due to frequent errors")
			return True
			
			# If here, successfully scraped, so reset errorCount
		self.state[trip.index].errorCount = 0

		lowestFare = None
		for segment in segments:
			lowestSegmentFare = self.findLowestFareInSegment(trip, segment)
			if(lowestSegmentFare is None):
				break;
			lowestFare = lowestSegmentFare if (lowestFare is None) else lowestFare + lowestSegmentFare

		if(self.state[trip.index].firstQuery):
			if(lowestFare is None):
				self.sendNotification(config.notification, trip.description + ": Initial fare UNAVAILABLE")
			else:
				self.sendNotification(config.notification, trip.description + ": Initial fare $" + str(lowestFare))
				self.state[trip.index].currentLowestFare = lowestFare
			self.state[trip.index].firstQuery = False
		elif(self.state[trip.index].currentLowestFare is None):
			if(lowestFare is not None):
				self.sendNotification(config.notification, trip.description + ": Fare now $" + str(lowestFare))
				self.state[trip.index].currentLowestFare = lowestFare
		else:
			if(lowestFare is None):
				self.sendNotification(config.notification, trip.description + ": Fares now UNAVAILABLE")
				self.state[trip.index].currentLowestFare = None
			elif(lowestFare != self.state[trip.index].currentLowestFare):
				self.sendNotification(config.notification, trip.description + ": Lowest fares now $" + str(lowestFare))
				self.state[trip.index].currentLowestFare = lowestFare
					
		return True	


	def processTrips(self, config):
		for trip in config.trips:
			if(not self.processTrip(trip, config)):
				return False
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
