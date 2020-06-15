FROM python:3-slim

# Install gmusicapi
RUN pip3 install gmusicapi pyaml python-pushover

# Add script file
ADD g-monitor.py  /app/
WORKDIR /app

# Run script in daemon mode
CMD ["/usr/local/bin/python3", "g-monitor.py", "-d"]