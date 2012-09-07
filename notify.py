import contextlib
import json
import time
import urllib2

import hipchat.config
import hipchat.room

import secrets

hipchat.config.token = secrets.hipchat_token


def hipchat_notify(room_id, message):
    # Pure kwargs don't work here because 'from' is a Python keyword...
    hipchat.room.Room.message(**{
        'room_id': room_id,
        'from': 'Mr Gorilla',
        'message': message,
        'color': 'green',
    })


def get_version(url='http://www.khanacademy.org/api/v1/dev/version'):
    try:
        with contextlib.closing(urllib2.urlopen(url)) as f:
            data = json.loads(f.read())
    except urllib2.URLError, e:
        print "Couldn't get version: %s" % e
        if isinstance(e, urllib2.HTTPError):
            # When urlllib2 returns an HTTPError, the textual response returned
            # by read() can be helpful when debugging.
            print e.read()
        return None

    # We only want the major version
    return data['version_id'].split('.', 2)[0]


def version_link(version, text=None):
    if text is None:
        text = version

    return ('<a href="http://%s.khan-academy.appspot.com/">%s</a>'
            % (version, text))


def error_logs_url(version):
    return ("https://appengine.google.com/logs?app_id=s~khan-academy&"
            "version_id=%s&severity_level_override=0&"
            "severity_level=3" % version)


def error_logs_link(version, text="error logs"):
    return '<a href="%s">%s</a>' % (error_logs_url(version), text)


def instances_url(version):
    return ("https://appengine.google.com/instances?&app_id=s~khan-academy&"
            "version_id=%s" % version)


def instances_link(version, text="instances"):
    return '<a href="%s">%s</a>' % (instances_url(version), text)


def build_message(last_version, version):
    return ('App Engine default version just changed: '
            '<a href="http://www.khanacademy.org/">khanacademy.org</a>, '
            '<a href="https://appengine.google.com/dashboard?&app_id=s~khan-academy">appspot dashboard</a>, '
            '<a href="https://appengine.google.com/deployment?&app_id=s~khan-academy">app versions</a><br>'
            '&bull; old: %s (%s, %s)<br>'
            '&bull; new: %s (%s, %s)'

            % (version_link(last_version),
               error_logs_link(last_version), instances_link(last_version),

               version_link(version),
               error_logs_link(version), instances_link(version)))


if __name__ == '__main__':
    last_version = None

    while True:
        version = get_version()
        print version

        if version is not None:
            if last_version is not None and version != last_version:
                hipchat_notify(
                    secrets.hipchat_room_id,
                    build_message(last_version, version))
            last_version = version

        time.sleep(10)
