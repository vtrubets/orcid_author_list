#!/usr/bin/env python

import re


def munge_field(arg):
    """
    Take a naming field and remove extra white spaces.
    """
    if arg:
        res = re.sub(r'\s+', r' ', arg).strip()
    else:
        res = ''
    return res


def remove_duplicates(l):
    my_set = set()
    res = []
    for e in l:
        if e not in my_set:
            res.append(e)
            my_set.add(e)
    return res


def load_cathryns_changes(xlsx_file):
    pass

