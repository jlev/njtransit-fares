import argparse
from datetime import datetime
from collections import defaultdict
import itertools
import csv

from api import get_trip
import stops

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def valid_time(s):
    try:
        return datetime.strptime(s, "%H:%M").time()
    except ValueError:
        msg = "Not a valid time: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def valid_town(s):
    s = s.strip().replace("'",'').upper()
    if s in stops.NAMES:
        return s
    else:
        print(f'{s} not in valid stop names')
        return None

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Get bus fares for NJ Transit')
    parser.add_argument('origin', help='TOWN', type=valid_town, nargs='?')
    parser.add_argument('destination', help='TOWN', type=valid_town, nargs='?')
    parser.add_argument('--load', help='route CSV')
    parser.add_argument('date', help='YYYY-MM-DD', type=valid_date)
    parser.add_argument('time', help='HH:MM', type=valid_time)
    args = parser.parse_args()

    when = datetime.combine(args.date, args.time)

    if args.origin and args.destination:
        print(f'getting {args.origin} to {args.destination} at {when}')
        fare = get_trip(args.origin, args.destination, when)
        print(f'fare: {fare}')
    elif args.load:
        print(f'loading {args.load}')
        # file layout is route,also,towns (list)
        with open(args.load, 'r') as route_file:
            route_reader = csv.reader(route_file)
            fieldnames = route_reader.__next__()

            pairs = defaultdict(dict)
            for route in route_reader:
                # each route contains a list of towns to check legs
                # split field by comma, check for valid name, and filter out nones
                towns = filter(None.__ne__, [valid_town(t) for t in route[2].split(',')])
                # check each pair of towns without repeating
                combinations = itertools.combinations(towns, 2)
                for (orig,dest) in combinations:
                    print(f'{orig}-{dest}')
                    pairs[orig][dest] = get_trip(orig, dest, when)

            # output huge spreadsheet with all possible stop combinations
            print(pairs)
            with open('output.csv', 'w') as out_file:
                fieldnames = list(stops.NAMES)
                fieldnames.insert(0, 'stop')
                pair_writer = csv.DictWriter(out_file, fieldnames=fieldnames)
                pair_writer.writeheader()
                for row, values in pairs.items():
                    values['stop'] = row
                    pair_writer.writerow(values)
        