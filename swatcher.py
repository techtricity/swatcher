#!/usr/bin/python

import argparse
import time
import selenium
import datetime
import os

import swa
import configuration

DEFAULT_CONFIGURATION_FILE = "swatcher.ini"

class state(object):

	def __init__(self):
		self.errorCount = 0
		self.currentLowestFare = None 
		self.blockQuery = False
		self.firstQuery = True
		self.notificationHistory = ''


class swatcher(object):

	def __init__(self):
		self.state = []
		self.config = None
	
	def now(self):
		return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 

	def parseArguments(self):

		parser = argparse.ArgumentParser(description = "swatcher.py: Utility to monitor SWA for fare price changes")

		parser.add_argument('-f', '--file',
			dest = 'configurationFile',
			help = "Configuration file to use. If unspecified, will be '" + DEFAULT_CONFIGURATION_FILE + "'",
			default = DEFAULT_CONFIGURATION_FILE)

		args = parser.parse_args()

		return args

	def sendNotification(self, index, message):

		if(index is None):
			return

		subject = self.config.trips[index].description + ": " + message
		print(self.now() + ": SENDING NOTIFICATION!!! '" + subject + "'")

		if(not self.state[index].notificationHistory):
			tripDetails = os.linesep + "Trip Details:" 
			ignoreKeys = ['index', 'description']
			for key in self.config.trips[index].__dict__:
				if(any(x in key for x in ignoreKeys)):
					continue
				tripDetails += os.linesep + "   " + str(key) + ": " + str(self.config.trips[index].__dict__[key]) 
			self.state[index].notificationHistory = tripDetails


		self.state[index].notificationHistory = self.now() + ": " + message + os.linesep + self.state[index].notificationHistory 

		if(self.config.notification.type == 'smtp'):
			try:
					# importing this way keeps people who aren't interested in smtplib from installing it..
				smtplib = __import__('smtplib')
				if(self.config.notification.useAuth):
					server = smtplib.SMTP(self.config.notification.host, self.config.notification.port)
					server.ehlo()
					server.starttls()
					server.login(self.config.notification.username, self.config.notification.password)
				else:
					server = smtplib.SMTP(self.config.notification.host, self.config.notification.port)

				mailMessage = """From: %s\nTo: %s\nX-Priority: 2\nSubject: %s\n\n""" % (self.config.notification.sender, self.config.notification.recipient, subject)
				mailMessage += self.state[index].notificationHistory		
			
				server.sendmail(self.config.notification.sender, self.config.notification.recipient, mailMessage)
				server.quit()

			except Exception as e: 
				print(self.now() + ": UNABLE TO SEND NOTIFICATION DUE TO ERROR - " + str(e))
			return
		elif(self.config.notification.type == 'twilio'):
			try:
					# importing this way keeps people who aren't interested in Twilio from installing it..
				twilio = __import__('twilio.rest')

				client = twilio.rest.Client(self.config.notification.accountSid, self.config.notification.authToken)
				client.messages.create(to = self.config.notification.recipient, from_ = self.config.notification.sender, body = subject)
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

			if(lowestCurrentFare is None):
				lowestCurrentFare = flight['fare']
			elif(flight['fare'] < lowestCurrentFare):
				lowestCurrentFare = flight['fare']

		return lowestCurrentFare

	def processTrip(self, trip, driver):
		if(self.state[trip.index].blockQuery):
			return True;

		print(self.now() + ": Querying flight '" + trip.description + "'");

		try:
			segments = swa.scrape(
				driver = driver,
				originationAirportCode = trip.originationAirportCode,
				destinationAirportCode = trip.destinationAirportCode,
				departureDate = trip.departureDate,
				departureTimeOfDay = trip.departureTimeOfDay,
				returnDate = trip.returnDate,
				returnTimeOfDay = trip.returnTimeOfDay,
				tripType = trip.type,
				adultPassengersCount = trip.adultPassengersCount,
				debug = self.config.debug
			)
		except swa.scrapeValidation as e:
			print(e)
			print("\nValidation errors are not retryable, so swatcher is exiting")
			return False
		except swa.scrapeDatesNotOpen as e:
			if(self.state[trip.index].firstQuery):
				self.sendNotification(trip.index, "For '" + trip.description + "' dates do not appear open.")
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
				self.sendNotification(trip.index, "For '" + trip.description + "' ceasing queries due to frequent errors")
			return True
			
			# If here, successfully scraped, so reset errorCount
		self.state[trip.index].errorCount = 0

		lowestFare = None
		priceCount = 0
		for segment in segments:
			lowestSegmentFare = self.findLowestFareInSegment(trip, segment)
			if(lowestSegmentFare is None):
				break;
			lowestFare = lowestSegmentFare if (lowestFare is None) else lowestFare + lowestSegmentFare
			priceCount += 1
		
		if(((lowestFare is not None) and (trip.maxPrice > 0) and (lowestFare > trip.maxPrice)) or (priceCount != len(segments))):
			lowestFare = None

		if(self.state[trip.index].firstQuery):
			if(lowestFare is None):
				self.sendNotification(trip.index, "Fare that meets criteria is UNAVAILABLE")
			else:
				self.sendNotification(trip.index, "Initial fare $" + str(lowestFare))
			self.state[trip.index].currentLowestFare = lowestFare
			self.state[trip.index].firstQuery = False
		elif(self.state[trip.index].currentLowestFare is None):
			if(lowestFare is not None):
				self.sendNotification(trip.index, "Fare now $" + str(lowestFare))
				self.state[trip.index].currentLowestFare = lowestFare
		else:
			if(lowestFare is None):
				self.sendNotification(trip.index, "Fare that meets criteria is UNAVAILABLE")
				self.state[trip.index].currentLowestFare = None
			elif(lowestFare != self.state[trip.index].currentLowestFare):
				self.sendNotification(trip.index, "Lowest fares now $" + str(lowestFare))
				self.state[trip.index].currentLowestFare = lowestFare
					
		return True	


	def processTrips(self, driver):
		for trip in self.config.trips:
			if(not self.processTrip(trip, driver)):
				return False
		return True	

	def main(self):

		args = self.parseArguments();
		print(self.now() + ": Parsing configuration file '" + args.configurationFile +"'")

		try:
			self.config = configuration.configuration(args.configurationFile)
		except Exception as e:
			print("Error in processing configuration file: " + str(e))
			quit()

		self.state = [state() for i in xrange(len(self.config.trips))]	

		if(self.config.browser.type == 'chrome'): # Or Chromium
			options = selenium.webdriver.ChromeOptions()
			options.binary_location = self.config.browser.binaryLocation
			options.add_argument('headless')
			options.add_argument("log-level=" + str(self.config.browser.logLevel))
			driver = selenium.webdriver.Chrome(chrome_options=options)
		elif(self.config.browser.type == 'firefox'): # Or Iceweasel
			options = selenium.webdriver.firefox.options.Options()
			options.binary_location = self.config.browser.binaryLocation
			options.add_argument('--headless')
			driver = selenium.webdriver.Firefox(firefox_options = options)
		else:
			print("Unsupported web browser '" + browser.type + "' specified")
			quit()
			

		while True:
		
			if(not self.processTrips(driver)):
				break

			time.sleep(self.config.pollInterval * 60)

		return
	
if __name__ == "__main__":
	swatcher = swatcher()	

	swatcher.main()
