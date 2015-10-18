#!/usr/bin/env python2

import json
import re
import string
import snippets
from pattern.en import parse, parsetree, pprint


CUTOFF = 5
EDITED_PATTERN = re.compile(r"(\s)*(DRAFT[\s-]{0,3})*(.+)(\s)*")


def extract_snippet_messages_iter(snippet):
    chat_messages = snippet.get("chat_messages")
    for chat_id, text in chat_messages.iteritems():
        if text.get("edited_text"):
            yield EDITED_PATTERN.match(text["edited_text"]).group(3)
        else:
            yield string.strip(text["message"])


def extract_message_nouns(message):
    parsed = parsetree(message, relations=True, lemmata=True)
    return [
        word.string
        for sentence in parsed
        for chunk in sentence.chunks
        for word in chunk.words
        if chunk.type == "NP" and word.type == "NN"
    ]


def print_message_chunks(message):
    parsed = parsetree(message, relations=True, lemmata=True)
    for sentence in parsed:
        for chunk in sentence.chunks:
            print "\t%s %s %s" % (
                chunk.type,
                chunk.role,
                [(w.string, w.lemma if w.lemma != w.string else "", w.type)
                    for w in chunk.words]
            )


def update_noun_group(grouping, subjects, name_key, noun):
    for subj in subjects:
        name = subj.get(name_key)

        if not grouping.get(name):
            grouping[name] = dict()

        grouping[name][noun] = grouping[name].setdefault(noun, 0) + 1


def noun_count_keyfunc(noun_count):
    return noun_count[1]


def main():
    data = snippets.load_snippets()

    all_nouns = dict()
    nouns_by_artist = dict()
    nouns_by_artwork = dict()

    for snip in data:
        artworks = snippets.get_snippet_artworks(snip)
        artists = [artist for work in artworks
                   for artist in work.get('artists')]
        for message in extract_snippet_messages_iter(snip):
            for noun in extract_message_nouns(message):
                all_nouns[noun] = all_nouns.setdefault(noun, 0) + 1
                update_noun_group(nouns_by_artist, artists, 'name', noun)
                update_noun_group(nouns_by_artwork, artworks, 'title', noun)

    artist_nouns_filtered = dict()
    for artist, nouns in nouns_by_artist.iteritems():
        tmp = {noun: count for noun, count in nouns.iteritems()
               if count >= CUTOFF}
        if tmp:
            artist_nouns_filtered[artist] = tmp

    with open('secret_artist_nouns.json', 'w') as outfile:
        json.dump(artist_nouns_filtered, outfile, indent=2)

    artwork_nouns_filtered = dict()
    for work, nouns in nouns_by_artwork.iteritems():
        tmp = {noun: count for noun, count in nouns.iteritems()
               if count >= CUTOFF}
        if tmp:
            artwork_nouns_filtered[work] = tmp
    with open('secret_artwork_nouns.json', 'w') as outfile:
        json.dump(artwork_nouns_filtered, outfile, indent=2)

    nouns_sorted = sorted(all_nouns.iteritems(),
                          key=noun_count_keyfunc, reverse=True)
    with open('secret_all_nouns.json', 'w') as outfile:
        json.dump({noun: count for noun, count in nouns_sorted if count > 20},
                  outfile, indent=2)

if __name__ == '__main__':
    main()
