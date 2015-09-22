# gae-default-version-notifier

Every 10 seconds it will check the version returned by
http://www.khanacademy.org/api/internal/dev/version and send a notification
to Slack if it has changed since the last check.

This runs as a process on our internal webserver, toby.

Since GAE will serve this URL from different instances for about an
hour after a new default version is designated, we have added some
buffering to alleviate flip-flopping.  This behavior is documented at
    http://stackoverflow.com/questions/15416938/app-engine-version-served-by-default-appears-to-be-inconsistent-and-thrash-for

This means we cannot detect when an actual rollback to a previous
version has occurred within a short window.  But after 2 hours, we
reset our history and can detect an inadvertant flip.

This uses alertlib (a sub-repo) to talk to Slack.  alertlib requires
being able to import a file called secrets.py with the contents:

    slack_alertlib_webhook_url = "<slack url value>"

This service is controlled via upstart, so after modifying, you can
restart like so:

    % sudo stop gae-default-version-notifier
    % sudo start gae-default-version-notifier
