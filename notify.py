import contextlib
import json
import logging
import socket
import time
import urllib2

# Must be on the PYTHONPATH!  And secrets.py must be too.
import alertlib


# Explicitly hit the default module, because by default /api/internal/dev goes
# to frontend-highmem.
DEFAULT_VERSION_URL = ('https://default-dot-khan-academy.appspot.com'
                       '/api/internal/dev/version')


def get_version(url=DEFAULT_VERSION_URL):
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


def error_logs_url(version):
    return ("https://appengine.google.com/logs?app_id=s~khan-academy&"
            "version_id=%s&severity_level_override=0&"
            "severity_level=3" % version)


def instances_url(version):
    return ("https://appengine.google.com/instances?&app_id=s~khan-academy&"
            "version_id=%s" % version)


class SlackNotifier(object):
    # channels registered to receive notifications, and whether they want
    # long or short format messages
    CHANNELS = {'#1s-and-0s-deploys': 'long'}
    SENDER_NAME = 'Mr Gorilla'
    ICON_EMOJI = ':monkey_face:'

    def change_message(self, last_version, version):
        """A plaintext message about a version change."""
        return (u':gae: App Engine default version changed: `%s` \u2192 `%s`'
                % (last_version, version))

    def _version_link(self, version):
        if not version:
            return "`unknown`"
        return "<http://{0}.khan-academy.appspot.com|`{0}`>".format(version)

    def change_attachment(self, last_version, version):
        """A richly formatted Slack attachment about a version change."""
        return {
            "fallback": self.change_message(last_version, version),
            "pretext": (
                ":gae: App Engine default version just changed: "
                "<http://www.khanacademy.org|khanacademy.org>, "
                "<https://appengine.google.com/dashboard?&app_id=s~khan-academy|appspot dashboard>, "
                "<https://appengine.google.com/deployment?&app_id=s~khan-academy|app versions>."
            ),
            "fields": [
                {
                    "title": "Old",
                    "value": "%s\n<%s|error logs>, <%s|instances>" % (
                        self._version_link(last_version),
                        error_logs_url(last_version),
                        instances_url(last_version)
                    ),
                    "short": True
                },
                {
                    "title": "New",
                    "value": "%s\n<%s|error logs>, <%s|instances>" % (
                        self._version_link(version),
                        error_logs_url(version),
                        instances_url(version)
                    ),
                    "short": True
                }
            ],
            "mrkdwn_in": ["fields"]
        }

    def notify_version_change(self, last_version, version):
        notification = alertlib.Alert(
            self.change_message(last_version, version),
            severity=logging.INFO)
        attachment = self.change_attachment(last_version, version)

        for channel, desired_msg_length in self.CHANNELS.viewitems():
            if desired_msg_length == 'short':
                notification.send_to_slack(channel,
                                           simple_message=True,
                                           sender=self.SENDER_NAME,
                                           icon_emoji=self.ICON_EMOJI)
            elif desired_msg_length == 'long':
                notification.send_to_slack(channel,
                                           sender=self.SENDER_NAME,
                                           icon_emoji=self.ICON_EMOJI,
                                           attachments=[attachment])

if __name__ == '__main__':
    alertlib.Alert('Restarted `gae-default-version-notifier`...',
                   severity=logging.INFO).send_to_logs()

    version_log = []
    checks_since_new_version_found = 0
    seconds_between_checks = 60
    minutes_for_new_version_to_stick = 60 * 2

    while True:
        version = get_version()
        print '%s: %s' % (time.ctime(), version)

        if version is not None and version not in version_log:
            version_log.append(version)
            checks_since_new_version_found = 0

            # Find the previous version
            last_version = None
            if len(version_log) > 1:
                last_version = version_log[-2]

            # Notify Slack
            SlackNotifier().notify_version_change(last_version, version)

        checks_since_new_version_found += 1

        # After minutes_for_new_version_to_stick, we assume the version has
        # "stuck", so we can clear the log and detect an inadvertant flip.
        sec_elapsed = checks_since_new_version_found * seconds_between_checks
        if sec_elapsed / 60 > minutes_for_new_version_to_stick:
            version_log = version_log[-1:]

        time.sleep(seconds_between_checks)
