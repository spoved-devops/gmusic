## Problem
Google play music has a tendancy to remove songs you've added to your library now and then, seemingly due to publishers/owners removing them at will; maybe they want a slight change in their catalogue for some reason, who knows.  All fair enough, but there's no way to tell what's disappeared, when.  You end up with a gradually diminishing library and don't notice something's gone until months later.

## Solution
Something that tracks what's in your Google Play Music library and alerts you when a track goes AWOL.

Using the gmusicapi package, download tracks currently in your library and compare against a previously downloaded list.  If tracks have been added or removed, send a Pushover alert.

#### Setup
The following are required:
* A Pushover account, with User and Application keys.  See [Pushover](http://pushover.net)
* Python 3 installed, along with the gmusicapi, pyaml and python-pushover modules
* A pre-created OAuth credentials file for your Google account


##### Pushover
Visit [Pushover](https://pushover.net) to create an account.  Free for seven days, a one-off fee of £5 after that.  Your account will have a "User Key" assocaited with it.  Along with this, we need an "Application Key" to distinguish messages from this app from any others you may have.  Simply create a new application to get an app key to use.

##### gmusicapi, pyaml and python-pushover
Install gmusicapi, pyaml and python-pushover python modules with:
```bash
pip3 install gmusicapi pyaml python-pushover
```

##### OAuth Credentials File
The ```get-credentials.py``` script can be used to generate an OAuth credentials file for use by ```g-monitor.py```.  It'll open a browser window, prompt you to log in to your Google account and allow access.  If you grant access, a code will be displayed.  Copy this code and paste it into the terminal running the ```get-credentials``` script.  The credentials file is named ```gcreds.json``` and written to the current directory.

```python
$ /usr/bin/python3 get-credentials.py
Performing OAuth authentication - a browser window should open...

Visit the following url:
 https://accounts.google.com/o/oauth2/v2/auth?client_id=...&access_type=offline&response_type=code

Opening your browser to it now... done.
If you don't see your browser, you can just copy and paste the url.

Follow the prompts, then paste the auth code here and hit enter: 4/XXXXXXXXXXcugX_Bj1nAy4wf9dLdfJZTvP01Pd-WXXXXXXXXXXGsec

Credentials file stored at ./gcreds.json

Set the following environment variables before running g-monitor.py:

   _PUSHOVER_USER_KEY=<your pushover user key>
   _PUSHOVER_API_KEY=<your pushover api key>
   _CREDS=$(<./gcreds.json)

```

### Running the ```g-monitor.py``` script

Set the environment variables ```_PUSHOVER_USER_KEY```, ```_PUSHOVER_USER_KEY``` and ```_CREDS``` as described above.

To run the script as a one off (perhaps to schedule through cron), just run it with no arguments:
```bash
python3 ./g-monitor.py
```

To run the script in daemon mode, add the ```-d``` switch:
```bash
python3 ./g-monitor.py -d
```

### Running ```g-monitor.py``` as a container
Create a Docker image:
```bash
docker build -t gmusic-monitor:latest .
```
Run the image as a container, passing in environment variables:
```bash
docker run -e _PUSHOVER_USER_KEY=<user key> -e _PUSHOVER_APP_KEY=<app key> -e _CREDS="$(<gcreds.json)" gmusic-monitor:latest
```
