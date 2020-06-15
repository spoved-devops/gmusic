# Could use a data store of some sort, but let's just use files
import gmusicapi, urllib.parse, os, sys, datetime, time, oauth2client, argparse
from pathlib import Path
from yaml import safe_load
from pushover import init, Client

_CREDS_FILE = "./creds"
_STORED_TRACKS_FILE = "./stored_tracks"
_MISSING_LOG = "./missing_tracks_log"
_NEW_LOG = "./new_tracks_log"
_SLEEP = 86400 # One day

# Log a message with a timestamp
def log(message, file=sys.stdout):
    print(f"{datetime.datetime.now()} {message}", file=file, flush=True)


# Check each environment variable in a list is set
def check_env_vars(var_list):

    _missing_vars = 0
    for _env_var in var_list:
        if not os.environ.get(_env_var):
            _missing_vars = _missing_vars + 1
            log (f"ERROR: Unable to get environment variable {_env_var}", file=sys.stderr)

    if _missing_vars:
        log("One or more environment variables not set... exiting", file=sys.stderr)
        exit(1)


# Send pushover alert with details of missing tracks
def send_alert(missing_tracks, new_tracks):

    log("Sending track change alert")

    # Construct a message
    _message = f"Google Play Music Library - Track Changes:\n"
    for _track in missing_tracks:
        _message = _message + f"   MISSING: {_track['title']} - {_track['artist']} - {_track['album']}\n"

    for _track in new_tracks:
        _message = _message + f"   NEW: {_track['title']} - {_track['artist']} - {_track['album']}\n"

    Client(os.environ["_PUSHOVER_USER_KEY"]).send_message(_message, title="Google Play Music Library - Track Changes")


# Read stored tracks, url-decode them
def read_stored_tracks(file):

    _stored_tracks = list()

    # If we can find the file given, read in track info from it
    if Path(file).is_file():
        log(f"Found existing list at {file}")
        with open(file, 'r') as _stored_tracks_file:
            _stored_tracks = safe_load(_stored_tracks_file)
    else:
        log(f"Stored tracks file {file} not found")

    # URL-decode stored track details
    for _track in _stored_tracks:
        _track["artist"] = urllib.parse.unquote(_track["artist"])
        _track["title"] = urllib.parse.unquote(_track["title"])
        _track["album"] = urllib.parse.unquote(_track["album"])

    return _stored_tracks


# Get a list of tracks currently in your Google Play Music library
def get_google_play_tracks():

    # Try creating oauth2creds from the file manually
    _oa2_creds = oauth2client.client.OAuth2Credentials.from_json(os.environ["_CREDS"])

    # Create mobile client
    _mobile_client = gmusicapi.Mobileclient()

    # This login attempt will fail, but we can get a valid device ID from the execption thrown
    try:
        _mobile_client.oauth_login("1234567890", _oa2_creds, "en_GB")
    except gmusicapi.exceptions.InvalidDeviceId as e:
        _device_id = e.valid_device_ids[0]

    # Attempt login
    if not _mobile_client.oauth_login(_device_id, oauth_credentials=_oa2_creds, locale="en_GB"):
        log(f"FATAL: Unable to login using device ID {_device_id} and supplied credentials", file=sys.stderr)
        log("       Credentials need renewing?", file=sys.stderr)
        exit(1)

    # Get raw track list
    _library_tracks_raw = _mobile_client.get_all_songs()
    
    # We're only interested in title, artist and album
    _library_tracks = list()
    for track in _library_tracks_raw:
        _library_tracks.append({"artist": track["artist"], "album": track["album"], "title": track["title"]})

    return _library_tracks


# Log missing tracks to a file
def write_track_file(track_list, file, mode):

    try:
        with open(file, mode) as _tracks_file:

            # Write each track out, URL-encoded everything
            for _track in sorted(track_list, key = lambda i: i['title']):
                _tracks_file.write(f"- title: \"{urllib.parse.quote(_track['title'])}\"\n")
                _tracks_file.write(f"  artist: \"{urllib.parse.quote(_track['artist'])}\"\n")
                _tracks_file.write(f"  album: \"{urllib.parse.quote(_track['album'])}\"\n")

    except IOError:
        log("FATAL: Error opening tracks file {file} for writing")
        exit(1)


def main():

    # Check required env vars are set
    check_env_vars(["_PUSHOVER_API_KEY", "_PUSHOVER_USER_KEY", "_CREDS"])

    # Parse arguments - there may be a -d
    _parser = argparse.ArgumentParser()
    _parser.add_argument("-d", "--daemon", help="Run in daemon mode", action="store_true", default=False)
    _args = _parser.parse_args()

    if _args.daemon:
        init(os.environ["_PUSHOVER_API_KEY"])
        Client(os.environ["_PUSHOVER_USER_KEY"]).send_message("Starting Google Play Music Monitor")


    while True:

        _missing_tracks = list()
        _new_tracks = list()
    
        # Get current tracks in google play library.  Requires a device ID
        _current_tracks = get_google_play_tracks()

        # Read stored tracks from a previous run
        _stored_tracks = read_stored_tracks(_STORED_TRACKS_FILE)

        # Look for tracks removed from our library since we last retrieved them
        for _stored_track in _stored_tracks:
            _found = False
            
            for _current_track in _current_tracks:
                if _current_track == _stored_track:
                    # We've found it
                    _found = True

            if not _found:
                log(f"MISSING TRACK: {_stored_track['title']} - {_stored_track['artist']} - {_stored_track['album']}")
                _missing_tracks.append(_stored_track)

        # While we're at it, look for tracks added to the library since we last stored it, but only if we 
        # found some stored tracks
        if _stored_tracks:
            for _current_track in _current_tracks:
                _found = False

                for _stored_track in _stored_tracks:
                    if _stored_track == _current_track:
                        _found = True

                if not _found:
                    log(f"NEW TRACK: {_current_track['title']} - {_current_track['artist']} - {_current_track['album']}")
                    _new_tracks.append(_current_track)


        # If we have missing or new tracks send a pushover alert
        if _missing_tracks or _new_tracks:
            send_alert(_missing_tracks, _new_tracks)
        else:
            log("No changes")

        # Write tracks to logs of missing and new, and update the stored tracks file
        write_track_file(_missing_tracks, _MISSING_LOG, 'a')
        write_track_file(_new_tracks, _NEW_LOG, "a")
        write_track_file(_current_tracks, _STORED_TRACKS_FILE, 'w')

        # If we're not in daemon mode we're done
        if not _args.daemon:
            break

        log(f"Sleeping for {_SLEEP} seconds...")
        time.sleep(_SLEEP)

if __name__ == "__main__":
    main()