import os
from datetime import datetime
import requests
from requests_html import HTMLSession
import logging

import stops
from pagecache import PageCache

session = HTMLSession()
raw_cache = PageCache('raw')
log = logging.getLogger(__name__)

class ParseError(Exception):
    pass

def parse_page(body):
    # gets trips from AccordionPanel, pulls out lowest Total Regular fare
    try:
        accordion = body.find('#Accordion1')[0]
    except IndexError:
        raise ParseError('unable to find trip in page body')

    trips = accordion.find('.AccordionPanel')
    lowest = 0
    for panel in trips:
        summary = panel.find('tr')[-3]
        total_str = summary.find('td')[1].text
        total = float(total_str.replace('$',''))
        if (total < lowest) or (lowest == 0):
            lowest = total
        
    if lowest:
        return lowest

def get_page(options):
    response = session.post(
        url='https://www.njtransit.com/sf/sf_servlet.srv',
        params={
            "hdnPageAction": "BusSchedulesP2PFrom",
        },
        data=options
    )
    if not response.ok:
        log.error(response.status_code)
        return False
        
    return response.html

def get_trip(start, end, when, cache=True):
    if start not in stops.NAMES:
        log.error(f'{start} not in valid stop names')
        return None
    if end not in stops.NAMES:
        log.error(f'{end} not in valid stop names')
        return None

    start_sel = stops.LOOKUP.get(start)
    end_sel = stops.LOOKUP.get(end)
    trip_options = {
        "rdoTownTrans": "Town",
        "selOrigin": start_sel,
        "OriginDescription": start,
        "selDestination": end_sel,
        "DestDescription": end,
        "datepicker": when.strftime('%m/%d/%Y'),
        "rdoArriveDepart": "D",
        "Time": when.strftime('%-I:%-M'),
        "Suffix": when.strftime('%p'),
        "Hour": when.strftime('%-I'),
        "Minute": when.strftime('%-M'),
    }


    # check filesystem cache for existing scraped html
    if cache:
        filename = f'{start}-{end}.html'
        cached_response = raw_cache.get(filename)
        if cached_response:
            response = cached_response
        else:
            response = get_page(trip_options)
            raw_cache.set(filename, response)
    else:
        response = get_page(trip_options)

    # parse response to get trip total fare
    try:
        parsed = parse_page(response)
        return parsed
    except ParseError:
        log.error(f'unable to find fare for {start}-{end}')
    

if __name__=="__main__":
    # simple test condition
    start = 'ORANGE'
    end = 'EAST ORANGE'
    when = datetime(year=2019, month=10, day=9, hour=9, minute=30)
    log.info(f'getting {start} to {end} at {when}')
    fare = get_trip(start, end, when)
    log.info(f'fare: {fare}')
