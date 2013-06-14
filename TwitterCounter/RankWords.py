__author__ = "Jonas Geduldig"
__date__ = "December 7, 2012"
__license__ = "MIT"

# unicode printing for Windows 
import sys, codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)

import argparse
import operator
import Tokenizer
from TwitterAPI import TwitterAPI, TwitterOAuth, TwitterRestPager
import Words


def is_irrelevant_word(word):
	if word in Words.conj or word in Words.prep or word in Words.pron or word in Words.misc:
		return True
	else:
		return False


def process_tweet(text, count, n, list):
	tokens = Tokenizer.Tokenizer.plain_text(text)
	for tok in tokens:
		if not tok in list and not is_irrelevant_word(tok):
			if tok in count:
				count[tok] += 1
			else:
				count[tok] = 1
	count_list = sorted(count.iteritems(), key=operator.itemgetter(1), reverse=True)
	if len(count_list) > 0:
		print ' '.join('%s-%s' % i for i in count_list[:n])


def rank_old_words(api, list, n):
	words = ' OR '.join(list)
	count = {}
	while True:
		iter = TwitterRestPager(api, 'search/tweets', {'q': words}).get_iterator()
		for item in iter:
			if 'text' in item:
				process_tweet(item['text'], count, n, list)
			elif 'message' in item:
				if item['code'] == 131:
					continue # ignore internal server error
				elif item['code'] == 88:
					print>>sys.stderr, 'Suspend search until %s' % search.get_quota()['reset']
				raise Exception('Message from twiter: %s' % item['message'])


def rank_new_words(api, list, n):
	words = ','.join(list)
	count = {}
	while True:
		try:
			api.request('statuses/filter', {'track': words})
			iter = api.get_iterator()
			while True:
				for item in iter:
					if 'text' in item:
						process_tweet(item['text'], count, n, list)
					elif 'disconnect' in item:
						raise Exception('Disconnect: %s' % item['disconnect'].get('reason'))
		except Exception, e:
			print>>sys.stderr, '*** MUST RECONNECT', e


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Word ranker.')
	parser.add_argument('-n', metavar='N', type=int, default=3, help='number of most frequest words displayed')
	parser.add_argument('-oauth', metavar='FILENAME', type=str, help='read OAuth credentials from file')
	parser.add_argument('-past', action='store_true', help='search historic tweets')
	parser.add_argument('words', metavar='W', type=str, nargs='+', help='word(s) to track')
	args = parser.parse_args()	

	oauth = TwitterOAuth.read_file(args.oauth)
	api = TwitterAPI(oauth.consumer_key, oauth.consumer_secret, oauth.access_token_key, oauth.access_token_secret)
	
	try:
		if args.past:
			rank_old_words(api, args.words, args.n)
		else:
			rank_new_words(api, args.words, args.n)
	except KeyboardInterrupt:
		print>>sys.stderr, '\nTerminated by user'
	except Exception, e:
		print>>sys.stderr, '*** STOPPED', e