#!/usr/bin/python

import swa

def main():

	swa.scrape(
		originationAirportCode = 'MDW',
		destinationAirportCode = 'CUN',
		departureDate = '2018-10-07',
		returnDate = '2018-10-14',
		tripType = 'roundtrip'
	)
	
if __name__ == "__main__":
	main()
