#!/usr/bin/env python

import datetime
import os
import re

import mandrill
import pystache

from lib import log


def send_mail(url, sources, dry_run=False):
    ctx = {
        'url': url,
        'display_url': ellipsize(url, 50),
        'start_date': rel_date(sources[0][1]),
        'count': len(sources),
        'sources': [{
            'url': source_url,
            'timestamp': rel_date(ts),
            'name': parse_source_name(source_url),
        } for source_url, ts in sources],
    }
    log.warn('Context: %r', ctx)
    with open('resources/email.compiled.html.mustache') as f:
        template = f.read()
        body = pystache.render(template, ctx)

    if dry_run:
        log.warn('Skipping send... Email:\n%s', body)
        return False

    m = mandrill.Mandrill(os.environ['MANDRILL_APIKEY'])
    resp = m.messages.send({
        'from_email': os.environ['FROM_ADDRESS'],
        'to': [{'email': os.environ['TO_ADDRESS']}],
        'subject': 'New link from your thresholderbot',
        'html': body,
    })
    if resp[0]['status'] != 'sent':
        log.error('Error sending mail: %r', resp)
        return False
    return True


def rel_date(d):
    # Source: http://stackoverflow.com/a/5164027/151221
    if isinstance(d, (int, float)):
        d = datetime.datetime.fromtimestamp(d)
    diff = datetime.datetime.utcnow() - d
    s = diff.seconds
    if diff.days > 7 or diff.days < 0:
        return d.strftime('%d %b %y')
    elif diff.days == 1:
        return '1 day ago'
    elif diff.days > 1:
        return '{} days ago'.format(diff.days)
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{} seconds ago'.format(s)
    elif s < 120:
        return '1 minute ago'
    elif s < 3600:
        return '{} minutes ago'.format(s/60)
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{} hours ago'.format(s/3600)


def parse_source_name(source_url):
    return re.search(r'twitter\.com/([^/]+)/', source_url).group(1)


def ellipsize(s, m, c=u'\u2026'):
    """Truncates string s to max size m by inserting char c at its midpoint,
    leaving the beginning and end of s unchanged. Assumes c is a single char,
    which defaults to an ellipsis.
    """
    return s if len(s) <= m else s[:(m-1)/2] + c + s[-(m-1)/2:]
