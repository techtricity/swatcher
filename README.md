# swatcher
Southwest Airlines website scraper
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
* Allow monitoring prior to flights opening. Southwest typically starts their fares low, then raises them as seats fill. Many times the best fare can be gotten by waiting for new dates to open and booking immediately. Southwest sometimes posts when filghts will open, but many times will open sooner than expected. Now you can get notificed the moment fares open without having to frequently poll the site
* Add support for both SMTP notification, as well as Twilio

Tis utility has been written in Python, and targetted to 2.7, since going to 3 seemed unncecessary. Python requirments can be installed through pip and ```pip install -r requirements.txt```.

Due to the switch from static to dynamic pages, BeautifulSoup could no longer be used, instead Selenium was required. With the active content, a browser needs to be used to retrieve the content. I initially tried to use Selenium with PhantomJS, but was unsuccessful in getting it to run headless, so instead decided to test against Chrome and Firefox, since these are widely used and most likely already installed on the developers machine.

To understand how to properly use and configure swatcher, please refer to the configuration template "swatcher.ini". This file provides all the details needed to specifying all the trips you would like to monitor, setting up the notification method (SMTP or Twilio), and choosing which browser you would like to use for scraping. There appears to be tight correlation between what version of Selenium, WebDriver, and Browser are used - unexpected execptions, incorrect headless operation, and other issues were encountered, until I settled on software versions called out below.

#### Using with Google Chrome

Swatcher has been tested with Google Chrome 66.0.3359 and Chromium 57.0.2987. To use Selenium with Google Chrome, you will also need ChromeDriver, the WebDriver for Chrome can be downloaded at:

http://chromedriver.chromium.org/downloads

and installed by either adding the chromedriver directory to your path or copying chromedriver to an existing directory on your path. ChromeDriver 2.38 along with Selenium 3.3.0 has been tested and found to work as expected.

#### Using with Mozilla Firefox

Swatcher has been tested with Mozilla Firefox 66.0.1. To use Selenium with Mozilla Firefox, you will also need geckodriver, which can be downloaded at:

https://github.com/mozilla/geckodriver/releases

and installed by either adding the geckodriver directory to you path or copying geckodriver to an existing directory on your path. GeckoDriver 0.20.1 along with Selenium 3.12.0 has been tested and found to work as expected.

#### Twilio

I am not a fan of Twilio, instead I prefer SMTP. As such, I have not included Twilio in the requirements.txt, and swatcher does dynamic module import for Twilio, so if you do not intend on using it, you don't need to install it.

If you do need to install it, it can be done via pip:

```pip install twilio```

#### Environment

Swatcher has been tested and found to work on Ubuntu 16.04, 18.04 and Debian 8. I have yet to test under Windows or MacOS, but I do not see any reason why it shouldn't work

#### Modifications and Enhancements

I consider swatcher to be a work-in-progress, so if you have any modifications or suggestions, please feel free to discuss with me [farewatch (at) techtricity.com], and I may take you pull request or implement the change, if I have the cycles.

-john-
