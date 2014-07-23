import contextlib
import json
import socket
import time
import urllib2

# Must be on the PYTHONPATH!  And secrets.py must be too.
import alertlib


# These are the rooms we send messages to.
HIPCHAT_ROOMS = ['1s and 0s', '1s/0s: deploys']


def hipchat_notify(message):
    alert = alertlib.Alert(message, html=True)
    # Let's keep a permanent record of our versions in the logs too
    for room in HIPCHAT_ROOMS:
        alert.send_to_hipchat(room, color='green', sender='Mr Gorilla')


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
    except socket.error, e:
        print "Couldn't get version: socket error %s" % e
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
    hipchat_notify('Restarting notify.py!')

    version_log = []
    checks_since_new_version_found = 0
    seconds_between_checks = 60
    minutes_for_new_version_to_stick = 60 * 2

    while True:
        version = get_version()
        print '%s: %s' % (time.ctime(), version)

        if version is not None:
            if version not in version_log:
                version_log.append(version)
                checks_since_new_version_found = 0

                # Find the previous version
                last_version = None
                if len(version_log) > 1:
                    last_version = version_log[-2]

                # Notify HipChat
                hipchat_notify(build_message(last_version, version))

        checks_since_new_version_found += 1

        # After minutes_for_new_version_to_stick, we assume the version has
        # "stuck", so we can clear the log and detect an inadvertant flip.
        if ((checks_since_new_version_found * seconds_between_checks) / 60
            > minutes_for_new_version_to_stick):
            version_log = version_log[-1:]

        time.sleep(seconds_between_checks)
