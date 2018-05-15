import ConfigParser
import re

class configuration:

	def __init__(self, configurationFile):

		cp = ConfigParser.SafeConfigParser()
		cp.read(configurationFile)

		if(cp.has_section('global') == False):
			raise Exception("Configuration file does not contain 'global' section'")

		if(cp.has_option('global', 'pollInterval')):
			self.pollInterval = cp.getint('global', 'pollInterval')
		else:
			self.pollInterval = 30

		if(cp.has_option('global', 'debug')):
			self.debug = cp.getboolean('global', 'debug')
		else:
			self.debug = false

		if(cp.has_option('global', 'notificationMethod')):
			self.notificationMethod = cp.get('global', 'notificationMethod')
			if(self.notificationMethod != 'smtp'):
				raise Exception("Unrecognized notificationMethod '" + self.notificationMethod + "'")
		else:
			self.notificationMethod = 'smtp'

		if(self.notificationMethod == 'smtp'):
			if(cp.has_option('global', 'smtpHost')):
				self.smtpHost = cp.get('global', 'smtpHost')
			else:
				raise Exception("Configuration file missing required 'smtpHost' option")

			if(cp.has_option('global', 'smtpPort')):
				self.smtpPort = cp.getint('global', 'smtpPort')
			else:
				self.smtpPort = 25

			if(cp.has_option('global', 'smtpRecipient')):
				self.smtpRecipient = cp.get('global', 'smtpRecipient')
			else:
				raise Exception("Configuration file missing required 'smtpRecipient' option")

			if(cp.has_option('global', 'smtpSender')):
				self.smtpSender = cp.get('global', 'smtpSender')
			else:
				raise Exception("Configuration file missing required 'smtpSender' option")

			self.smtpUseAuth = False			
			if(cp.has_option('global', 'smtpUsername')):
				self.smtpUsername = cp.get('global', 'smtpUsername')
				self.smtpUseAuth = True
				if(cp.has_option('global', 'smtpPassword')):
					self.smtpPassword = cp.get('global', 'smtpPassword')
				else:
					raise Exception("Configuration file has smtpUsername specified, but not smtpPassword")

			self.trips = []
			pattern = re.compile("^trip-[0-9]+$")
			for section in cp.sections():
				if(not pattern.match(section)):
					continue

				trip = {}			
				if(cp.has_option(section, 'description')):
					trip['description'] = cp.get(section, 'description')

				if(cp.has_option(section, 'originationAirportCode')):
					trip['originationAirportCode'] = cp.get(section, 'originationAirportCode')
				else:
					raise Exception("For section '" + section + "', required option originationAirportCode is missing")

				if(cp.has_option(section, 'destinationAirportCode')):
					trip['destinationAirportCode'] = cp.get(section, 'destinationAirportCode')
				else:
					raise Exception("For section '" + section + "', required option destinationAirportCode is missing")

				if(cp.has_option(section, 'tripType')):
					trip['tripType'] = cp.get(section, 'tripType')
				else:
					raise Exception("For section '" + section + "', required option tripType is missing")

				if(cp.has_option(section, 'departureDate')):
					trip['departureDate'] = cp.get(section, 'departureDate')
				else:
					raise Exception("For section '" + section + "', required option departureDate is missing")

				if(cp.has_option(section, 'departureTimeOfDay')):
					trip['departureTimeOfDay'] = cp.get(section, 'departureTimeOfDay')
				else:
					trip['departureTimeOfDay'] = 'anytime'
					

				if(cp.has_option(section, 'returnDate')):
					trip['returnDate'] = cp.get(section, 'returnDate')
				else:
					trip['returnDate'] = ''

				if(cp.has_option(section, 'returnTimeOfDay')):
					trip['returnTimeOfDay'] = cp.get(section, 'returnTimeOfDay')
				else:
					trip['returnTimeOfDay'] = 'anytime'
					

				if(cp.has_option(section, 'adultPassengersCount')):
					trip['adultPassengersCount'] = cp.getint(section, 'adultPassengersCount')
				else:
					raise Exception("For section '" + section + "', required option adultPassengersCount is missing")

				if(cp.has_option(section, 'maxStops')):
					trip['maxStops'] = cp.getint(section, 'maxStops')
				else:
					trip['maxStops'] = 8 # Just a large value...

				if(cp.has_option(section, 'price')):
					trip['price'] = cp.getint(section, 'price')
				else:
					trip['price'] = 0

				if(cp.has_option(section, 'maxDuration')):
					trip['maxDuration'] = cp.getfloat(section, 'maxDuration')
				else:
					trip['maxDuration'] = 0.0

				self.trips.append(trip)

			if(len(self.trips) == 0):
				raise Exception("Configuration file must have at least one [trip-X] section")

			return
