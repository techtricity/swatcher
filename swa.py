import time
import requests
import collections

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

URL = "https://www.southwest.com/air/booking/select.html"

# Preload a dictionary. These are values that are supported by the SWA REST API, but currently unconfigurable
# Some of these can be omitted, but for completeness, I'm including them with default values.
payload = {
	'returnAirportCode':'',
	'seniorPassengersCount':'0',
	'fareType':'USD',
	'passengerType':'ADULT',
	'promoCode':'',
	'reset':'true',
	'redirectToVision':'true',
	'int':'HOMEQBOMAIR',
	'leapfrogRequest':'true'
}


def validateAirportCode(airportCode):
	return

def validateDate(date):
	return

def validateTripType(tripType):
	return

def validateTimeOfDay(timeOfDay):
	return

def validatePassengersCount(passengersCount):
	return


def scrape(
	originationAirportCode, # 3 letter airport code (eg: MDW - for Midway, Chicago, Illinois)
	destinationAirportCode, # 3 letter airport code (eg: MCO - for Orlando, Florida) 
	departureDate, # Flight departure date in YYYY-MM-DD format
	returnDate, # Flight return date in YYYY-MM-DD format (for roundtip, otherwise ignored)
	tripType = 'roundtrip', # Can be either 'roundtrip' or 'oneway'
	departureTimeOfDay = 'ALL_DAY', # Can be either 'ALL_DAY', 'BEFORE_NOON', 'NOON_TO_SIX', or 'AFTER_SIX' (CASE SENSITIVE)
	returnTimeOfDay = 'ALL_DAY', # Can be either 'ALL_DAY', 'BEFORE_NOON', 'NOON_TO_SIX', or 'AFTER_SIX' (CASE SENSITIVE) 
	adultPassengersCount = 1 # Can be a value of between 1 and 8
	):

		# Validate all the parameters to ensure nothing is blatently erroneous
	validateAirportCode(originationAirportCode)
	validateAirportCode(destinationAirportCode)
	validateTripType(tripType)
	validateDate(departureDate)
	validateTimeOfDay(departureTimeOfDay)
	if (tripType == 'roundtrip'):
		validateDate(returnDate)
		validateTimeOfDay(returnTimeOfDay)
	validatePassengersCount(adultPassengersCount)

	payload['originationAirportCode'] = originationAirportCode
	payload['destinationAirportCode'] = destinationAirportCode
	payload['departureDate'] = departureDate
	payload['departureTimeOfDay'] = departureTimeOfDay
	if (tripType == 'roundtrip'):
		payload['returnDate'] = returnDate
		payload['returnTimeOfDay'] = returnTimeOfDay
	else:
		payload['returnDate'] = '' # SWA REST requires presence of this parameter, even on a 'oneway'
	payload['tripType'] = tripType
	payload['adultPassengersCount'] = adultPassengersCount

	query =  '&'.join(['%s=%s' % (key, value) for (key, value) in payload.items()])

	fullUrl = URL + '?' + query

	options = webdriver.ChromeOptions()
	options.binary_location = '/usr/bin/google-chrome'
	options.add_argument('headless')
	driver = webdriver.Chrome(chrome_options=options)

	driver.get(fullUrl)

	try:
		element = WebDriverWait(driver, 20).until( EC.element_to_be_clickable((By.CSS_SELECTOR,".search-results--container, .page-error--message")))

	except TimeoutException:
		print "Took Too Long!!!"
		open("dump.html", "w").write(u''.join((driver.page_source)).encode('utf-8').strip())
		quit()
	except Exception as ex:
		template = "An exception of type {0} occurred. Arguments:\n{1!r}"
		message = template.format(type(ex).__name__, ex.args)
		print message
		open("dump.html", "w").write(u''.join((driver.page_source)).encode('utf-8').strip())
		quit()

	print "ID: '" + element.get_attribute("id") + "' CLASS: '" + element.get_attribute("class") + "'"
	
	if element.get_attribute("class").find("page-error--message") >= 0:
		print element.text
		quit()

	# If here, we should have results, so  parse out...
	priceMatrixes = element.find_elements_by_class_name("air-booking-select-price-matrix")

	if (payload['tripType'] == 'roundtrip'):
		if (len(priceMatrixes) != 2):
			print "Only one set of prices returned for round-trip travel"
			quit()
		outboundFlights = priceMatrixes[0].find_elements_by_class_name("air-booking-select-detail")
		returnFlights = priceMatrixes[1].find_elements_by_class_name("air-booking-select-detail")
		print "Outbound: " + str(len(outboundFlights)) + " Return: " + str(len(returnFlights))
	else:
		outboundFlights = priceMatrixes[0].find_elements_by_class_name("air-booking-select-detail")
		print "Outbound: " + str(len(outboundFlights))

	open("dump.html", "w").write(u''.join((driver.page_source)).encode('utf-8').strip())
	print "Successful"


	#outbound_fares = driver.find_elements_by_tag_name("ul")[2]
	#outbound_prices = outbound_fares.find_elements_by_class_name("currency_dollars")

	#print outbound_fares
	#print outbound_prices

