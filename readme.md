This runs as a process on our Continuous Integration server (codename toby). Every 10 seconds it will check the version returned by http://www.khanacademy.org/api/v1/dev/version and send a notification to HipChat if it has changed since the last check.

Since GAE will serve this URL from different instances for about an hour after a new default version is designated, we have added some buffering to alleviate flip-flopping.  This behavior is documented at http://stackoverflow.com/questions/15416938/app-engine-version-served-by-default-appears-to-be-inconsistent-and-thrash-for

This means we cannot detect when an actual rollback to a previous version has occurred within a short window.  But after 2 hours, we reset our history and can detect an inadvertant flip.

You can download the hipchat source here:  https://github.com/Khan/python-hipchat

You can install ConfigObj with:
pip install configobj

After modifying this script, the deployment steps are:
1. ssh toby
2. Find the current process and kill it with ps aux | grep notify.py and kill
3. cd gae-default-version-notifier
4. git pull ??
5. nohup python ~/gae-default-version-notifier/notify.py &
