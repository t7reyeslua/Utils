#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: Antonio Reyes
# @Date:   2013-12-16 02:39:21
# @Last Modified time: 2014-01-17 19:41:40

# Usage: python dnssec_availability.py dnssec_domain_list.txt

"""
Checks the availavility of a list of domains. Verifies if the reason for its unavailability
is related to a failure in the name resolution.
"""

import requests
import re
import sys
import time
from multiprocessing import Pool

def main():
	global filename_details
	global count
	global unavailable
	global start_time
	start_time = time.time()
	count = 0
	unavailable = 0
	filename = sys.argv[1]
	filename_details = filename.split('.')[0] + '_details.txt'
	domain_list = open(filename).read().split()
	domain_list = set(domain_list)
	for domain in domain_list:
		dnssec_check(domain,0)

def dnssec_check(domain, retry):
	global count
	global unavailable
	global intent
	intent = retry
	domain = domain.rstrip('.')
	url = "http://" + domain
        
	try:
		r = requests.get(url)
		intent = 0
		html = r.text
		error_pattern = re.compile(r'ERR_NAME_RESOLUTION_FAILED')
		errors = error_pattern.findall(html)
		count += 1
		elapsed = time.time() - start_time 
		print '>> (%d-%d) Time elapsed: %2.2fs, Checking for %s' % (unavailable,count, elapsed, domain)
		with open(filename_details, 'a') as fp:
			msg = '(%d-%d) %s: OK\n' % (unavailable,count,domain)
			fp.write(msg)
	except Exception, e:
		intent += 1
		if intent<2:
			dnssec_check("www." + domain, intent)
		else:
			unavailable += 1
			count += 1
			elapsed = time.time() - start_time
			print '>> (%d-%d) Time elapsed: %2.2fs, Checking for %s: UNAVAILABLE' % (unavailable,count, elapsed, domain)
			with open(filename_details, 'a') as fp:
				msg = '(%d-%d) %s: UNAVAILABLE\n' % (unavailable,count,domain)
				fp.write(msg)
		return
        

if __name__ == "__main__":
    main()
