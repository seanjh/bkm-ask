#!/usr/bin/env python3

import json
from datetime import datetime

SNIPPETS_FILENAME = 'secret_snippet_data.json'

# TODO:
# * messages/snippet
# * number of objects
# * messages/object


def convert_datetime(date_str):
    if date_str:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return None


def convert_date(date_str):
    if date_str:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            # Work around some "date_added" fields that include datetime,
            # which throws a ValueError
            return convert_datetime(date_str)
    return None

# Excludes "date" fields that include only a year value (i.e., object_date,
# object_date_begin, object_date_end)
DATE_FIELDS = {
    'created_at': convert_datetime,
    'updated_at': convert_datetime,
    'accession_date': convert_datetime,
    'date_added': convert_date,
    'load_date': convert_date,
}


def parse_dates(item):
    if isinstance(item, dict):
        for field in [f for f in DATE_FIELDS if f in item]:
            convert_func = DATE_FIELDS[field]
            item[field] = convert_func(item[field])
        [parse_dates(item[key]) for key in item]
    elif isinstance(item, list):
        [parse_dates(val) for val in item]


def parse_date_hook(dct):
    parse_dates(dct)
    return dct


def load_snippets():
    with open(SNIPPETS_FILENAME) as infile:
        raw_data = json.load(infile)
        parse_dates(raw_data)
        return raw_data['data']


def show_hierarchy(sample, pad='.'):
    if isinstance(sample, dict):
        for key in sample.keys():
            print('%s%s' % (pad, key))
            show_hierarchy(sample[key], pad + '.')
    elif isinstance(sample, list):
        try:
            show_hierarchy(sample[0], pad)
        except IndexError:
            pass


def groupby_created(data):
    results = dict()
    for item in data:
        date = item.get('created_at').date()
        results[date] = results.setdefault(date, 0) + 1
    return results


def groupby_artist(data):
    results = dict()
    for item in data:
        if type(item.get('ocobjects')) == type([]):
            for art in item.get('ocobjects'):
                for artist in art.get('artists'):
                    artist_works = results.setdefault(artist["name"], dict())
                    artist_work = artist_works.get(art.get("title"))
                    if artist_work:
                        artist_work["mentions"] = artist_work["mentions"] + 1
                    else:
                        artist_work = dict()
                        artist_work["begin"] = art.get('object_date_begin')
                        artist_work["end"] = art.get('object_date_end')
                        artist_work["mentions"] = 1
                        artist_works[art["title"]] = artist_work

    return results


def groupby_art_year(data):
    pass
