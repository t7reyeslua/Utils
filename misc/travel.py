#!/usr/bin/python
from pprint import pprint as pp
import csv
import sys
from collections import defaultdict
from datetime import datetime

# Read passed argument
input_path = '/home/t7/Downloads/travel_2016_w2-5.csv'
if len(sys.argv) > 1:
    input_path = sys.argv[1]
    sys.argv = [sys.argv[0]]
    print('Working with: ' + input_path)

# Read CSV into list of dictionaries of transactions
transactions = [row for row in csv.DictReader(open(input_path), delimiter=';')]

# Divide the transactions by date and time of day
daily = defaultdict(list)
for d in transactions:
    try:
        check_time = datetime.strptime(d['Check-uit'], '%H:%M')
    except Exception:
        check_time = datetime.strptime(d['Check-in'], '%H:%M')

    datum = datetime.strftime(datetime.strptime(d['Datum'], '%d-%m-%Y').date(),
                              '%Y-%m-%d')
    if (check_time < datetime.strptime('12:00', '%H:%M')):
        daily[datum + ' 1.DELFT-AMS'].append(d)
    else:
        daily[datum + ' 2.AMS-DELFT'].append(d)

# Aggregate all travels of each day of each time of day
results = {}
total = 0
for d in daily:
    results[d] = sum([float(x['Bedrag'].replace(',', '.')) for x in daily[d]])
    total += results[d]

print("Travel Expenses==========================")
print("Total: " + str(total))
datums = []
costs = []
trips = []
for k, r in enumerate(sorted(results)):
    x = r.replace(' 1.', '|').replace(' 2.', '|')
    datum = datetime.strftime(datetime.strptime(x.split('|')[0],
                                                '%Y-%m-%d').date(),
                              '%d/%m/%Y')
    trip = x.split('|')[1]
    datums.append(datum)
    costs.append(results[r])
    trips.append(trip)
    print(str(k+1) + "\t" + datum + "\t" + str(results[r]) +
          "\tEUR\tPublic transport\t" + trip)

for k,v in enumerate(datums):
    print(v)
for k,v in enumerate(trips):
    print(v)
for k,v in enumerate(costs):
    print(str(v))
