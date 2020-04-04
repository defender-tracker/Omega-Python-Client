# stop script on error
set -e

# Enable the cellular data connection
o2lte apn hologram
o2lte data enable

# Enable the positioning system
o2lte gnss enable
# Stop the ogps daemon
/etc/init.d/ugps stop
/etc/init.d/ugps disable

# Start the Python client
python3 /root/client/start.py &
#python3 /root/client/test.py &

