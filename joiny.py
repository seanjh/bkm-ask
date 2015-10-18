#!/usr/bin/env python

import json
import pprint
import requests
import snippets
from six.moves.urllib.parse import quote
from secrets import ARTSY, NY_TIMES

session = requests.Session()
pp = pprint.PrettyPrinter(indent=2)

def artsy_request(req):
    req.headers["X-Xapp-Token"] = ARTSY["token"]
    return req.prepare()


def artsy_search_artist(artist_name):
    search_url = ("https://api.artsy.net/api/search/?q=%s%s" % (
        quote(artist_name),
        "+more:pagemap:metatags-og_type:artist"
    ))
    res = session.send(artsy_request(requests.Request("GET", search_url)))
    return res.json()


def mentions_cmp_func(mentions, other):
    return cmp(mentions, other)


def mentions_key_func(work):
    return work["mentions"]


def works_mentioned_sorted(artist_grouping):
    all_works = []
    for artist, works in artist_grouping.iteritems():
        for title, meta in works.iteritems():
            one = dict(meta)
            one["artist"] = artist
            one["title"] = title
            all_works.append(one)
    return sorted(all_works, mentions_cmp_func, key=mentions_key_func, reverse=True)


def most_mentioned_artists(artist_grouping):
    for artist, works in artist_grouping.iteritems():
        pass


def dump_results(filename, data):
    with open(filename, "w") as outfile:
        json.dump(data, outfile, indent=2)
        # outfile.write(json.dump(pp.pformat(data)))


def main():
    data = snippets.load_snippets()
    artist_grouping = snippets.groupby_artist(data)

    dump_results("secret_artist_groups.json", artist_grouping)
    dump_results("secret_mentions.json", works_mentioned_sorted(artist_grouping))

    results = artsy_search_artist(artist_grouping.keys()[0])
    pp.pprint(results)

if __name__ == '__main__':
    main()