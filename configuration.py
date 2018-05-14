import ConfigParser

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

			for section in cp.sections():
				print "Section Found: " + section
