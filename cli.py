import argparse, sys
from datetime import datetime
from collections import defaultdict
import itertools
import csv
import logging

from api import get_trip
import stops

log = logging.getLogger(__name__)

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
        log.error(f'{s} not in valid stop names')
        return None

def write_outfile(pairs, filename='output.csv'):
    # output huge spreadsheet with all possible stop combinations
    with open(filename, 'w') as out_file:
        fieldnames = list(stops.NAMES)
        fieldnames.insert(0, 'stop')
        pair_writer = csv.DictWriter(out_file, fieldnames=fieldnames)
        pair_writer.writeheader()
        for town in stops.NAMES:
            values = pairs[town]
            values['stop'] = town
            pair_writer.writerow(values)
    log.info('wrote '+filename)

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Get bus fares for NJ Transit')
    parser.add_argument('origin', help='TOWN', type=valid_town, nargs='?')
    parser.add_argument('destination', help='TOWN', type=valid_town, nargs='?')
    parser.add_argument('--load', help='route CSV')
    parser.add_argument('date', help='YYYY-MM-DD', type=valid_date)
    parser.add_argument('time', help='HH:MM', type=valid_time)
    parser.add_argument('--log', help='LEVEL', default='error')
    args = parser.parse_args()

    console_out = logging.StreamHandler(sys.stdout)
    console_out.setLevel(args.log.upper())
    log.addHandler(console_out)
    
    when = datetime.combine(args.date, args.time)

    if args.origin and args.destination:
        log.info(f'getting {args.origin} to {args.destination} at {when}')
        fare = get_trip(args.origin, args.destination, when)
        log.info(f'fare: {fare}')
    elif args.load:
        log.info(f'loading {args.load}')
        # file layout is route,also,towns (list)
        with open(args.load, 'r') as route_file:
            route_reader = csv.reader(route_file)
            fieldnames = route_reader.__next__()

            pairs = defaultdict(dict)
            try:
                for route in route_reader:
                    print('route '+route[0])
                    # each route contains a list of towns to check legs
                    # split field by comma, check for valid name, and filter out nones
                    towns = filter(None.__ne__, [valid_town(t) for t in route[2].split(',')])
                    # check each pair of towns without repeating
                    combinations = itertools.combinations(towns, 2)
                    for (orig,dest) in combinations:
                        log.info(f'{orig}-{dest}')
                        pairs[orig][dest] = get_trip(orig, dest, when)
                    write_outfile(pairs)
            except KeyboardInterrupt:
                print('quitter')
            finally:
                log.debug(pairs)
                write_outfile(pairs)
