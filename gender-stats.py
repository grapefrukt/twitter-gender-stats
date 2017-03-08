# -*- coding: utf-8 -*-

import ConfigParser
import csv
import re
import twitter
from unidecode import unidecode

# read config file with twitter auth stuff
config = ConfigParser.ConfigParser()
config.read('config.cfg')

# setup a regex to clean anything that's not letters
# this drops any thing outside ascii, but the dataset doesn't have that data anyway
alpharegex = re.compile('[^a-zA-Z]')
def remove_non_ascii(text):
    text = unidecode(text)
    return alpharegex.sub(' ', text)
    
# read in all the names and their probablilites from the csv file
# the default file comes from https://github.com/OpenGenderTracking/gender-api
namedata = {}
with open('usprocessed.csv') as csvfile:
    csvfile.seek(1)
    reader = csv.reader(csvfile)
    for row in reader:
        namedata[row[0].lower()] = row[6]
        
# connect to the twitter api, set up your own application like so:
# https://python-twitter.readthedocs.io/en/latest/getting_started.html
# paste in those four values in the config
api = twitter.Api(consumer_key=config.get('twitter', 'consumer_key'),
                  consumer_secret=config.get('twitter', 'consumer_secret'),
                  access_token_key=config.get('twitter', 'access_token'),
                  access_token_secret=config.get('twitter', 'access_token_secret'))

# by default we fetch the followers from whoever set up the twitter app we're using
users = api.GetFriends(include_user_entities=False)

# we can also fetch followers of a specific user
#users = api.GetFriends(screen_name='grapefrukt', include_user_entities=False)

# or assemble a list of "followers" to run the check on (useful for testing)
#users = [ api.GetUser(screen_name='grapefrukt', include_entities=False),  api.GetUser(screen_name='grapefrukt', include_entities=False),  ]

# set up counters
score = 0.0
count = 0

# iterate over all users we pulled down 
for user in users :
    
    # this value is a gender "probablility"
    # a value of zero means female
    # a value of one means male
    # we default to .5
    
    value = .5
    
    # this flag is set if we get the gender from the users bio
    biomatched = False
    
    # first, try to match on the bio
    if u'he/him' in user.description :
        value = 1
        biomatched = True
    elif u'she/her' in user.description :
        value = 0
        biomatched = True
    elif u'they/them' in user.description :
        value = .5
        biomatched = True
    # if no bio match is found, we go to work on their name
    else : 
        # first, strip any non ascii from the username
        # this gets rid of emojis and such
        # then we split on spaces, hoping there's a name in there somewhere
        names = remove_non_ascii(user.name).split(' ')
        
        # then, check all names split out against the dataset
        for name in names :
            if not name.lower() in namedata : 
                continue
            # if a match is found, we use the probablility from the dataset
            value = float(namedata[name.lower()])
            break
    
    # add the value of this user to the sum total
    # and increment the counter
    score += value
    count += 1
    print "{0:.2f} \t".format(value) + (' ', 'x')[biomatched] + '\t' + user.name.encode('utf-8')

# finally, we print the results
print ''
print '----------------------------------------'
print 'total score:   ' + str(score)
print 'names counted: ' + str(count)
print '----------------------------------------'
print "balance:       {0:.4f}".format(score/count)
print '----------------------------------------'
print ''
print 'a balance approaching 1 means all men.'
print 'a balance approaching 0 means all women.'