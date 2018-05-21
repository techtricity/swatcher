# swatcher
### Southwest Airlines (SWA) website scraper

Prior to the April 2018 redesign of the Southwest booking pages from a more static model to dynamic, I had been using swa-dashboard (https://github.com/gilby125/swa-dashboard/commits/master) for scraping for price changes. It had some limitations, but since it generally worked, I overlooked the limitations.

With the redesign, the scraper stopped working and I decided it was time to author a fare scraper that more adequately meets my needs:
* Add the ability to monitor flights on a more granular basis than what the SWA REST API provides. This is done by querying flights as supported by the API, then do post-processing on the flights returned to restrict based on:
  * Specific flight numbers
  * Maximum number of stops
  * Maximum duration of segment
  * Maximum price
* Support having one instance of the price tracker watch multiple trips
* Have configuration fully driven by configuration file, instead of command line. This would allow setting up different templates as needed, and not having to remember command line syntax if you haven't used the program in a few months
* Monitor all price changes, not just price reductions. Also just send one notification for each change event - no need to get pinged repeatedly. Also by tracking all price changes, both increases and decreases, it makes it easier to spot trends
* Add support for both SMTP notification, as well as Twilio

This utility has been written in Python, and targetted to 2.7, since going to 3 seemed unncecessary. It has the following  
