#!/usr/bin/env python

import json
import string
import six
import language
import calendar
from datetime import datetime

SNIPPETS_FILENAME = 'secret_snippet_data.json'


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


def get_snippet_artworks(snippet):
    if isinstance(snippet.get('ocobjects'), list):
        return [work for work in snippet.get('ocobjects')]
    return []


def get_snippet_artist(snippet):
    return [artist for work in get_snippet_artworks(snippet)
            for artist in work.get('artists')]


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


def show_hierarchy(sample, pad=''):
    if isinstance(sample, dict):
        for key in sample.keys():
            six.print_('%s%s' % (pad, key))
            show_hierarchy(sample[key], pad + '.')
    elif isinstance(sample, list):
        six.print_('%sLIST (len=%d)' % (pad, len(sample)))
        try:
            show_hierarchy(sample[0], pad + '.')
        except IndexError:
            pass


def fetch_artwork_artists(artwork):
    return artwork.get('artists')


def initialize_artwork_entry(artwork):
    return {
        "artist": list(fetch_artwork_artists(artwork)),
        "questions": list(),
        "artwork": dict(artwork)
    }


def groupby_ocobjects_id(data):
    results = dict()
    for snip in data:
        if isinstance(snip.get('ocobjects'), list):
            for artwork in snip.get('ocobjects'):
                artwork_id = artwork.get('id')
                if not results.get(artwork_id):
                    results[artwork_id] = initialize_artwork_entry(artwork)
                artwork_questions = results[artwork_id]["questions"]
                artwork_questions += [
                    q for q in language.extract_snippet_questions_iter(snip)
                ]
                # for question in extract_snippet_questions_iter(snip):
                # artwork_questions.append(question)
    return results


def groupby_created(data):
    results = dict()
    for item in data:
        date = item.get('created_at').date()
        results[date] = results.setdefault(date, 0) + 1
    return results


def groupby_artist(data):
    results = dict()
    for item in data:
        if isinstance(item.get('ocobjects'), list):
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


def default_serializer(obj):
    """Default JSON serializer."""

    if isinstance(obj, datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis
    raise TypeError('Not sure how to serialize %s' % (obj,))


def make_objectid_file():
    data = load_snippets()
    results = groupby_ocobjects_id(data)
    # print(results.keys())
    # print(json.dumps(
    #     results.get(4002), sort_keys=True, indent=4, default=default_serializer
    # ))
    with open('secret_id_objects.json', 'w') as outfile:
        json.dump(
            results,
            outfile,
            sort_keys=True,
            indent=4,
            default=default_serializer
        )
