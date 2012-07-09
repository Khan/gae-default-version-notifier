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
        'from': 'Mr Monkey',
        'message': message,
        'color': 'purple',
    })


def get_version():
    try:
        f = urllib2.urlopen('http://www.khanacademy.org/api/v1/dev/version')
        data = json.loads(f.read())
    except urllib2.HTTPError, e:
        print "Couldn't get version: %s\n%s" % (e, e.read())
        return None
    finally:
        f.close()

    # We only want the major version
    return data['version_id'].split('.', 2)[0]


last_version = None

if __name__ == '__main__':
    while True:
        version = get_version()

        if version is not None:
            if last_version is not None and version != last_version:
                # 19528 is code for '1s and 0s'
                hipchat_notify(
                    19528, ('App Engine (www.khanacademy.org) default version '
                            'changed to %s' % version))
            last_version = version

        time.sleep(10)
