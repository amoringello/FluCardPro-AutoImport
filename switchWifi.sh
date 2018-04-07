#!/bin/bash
# Switch to camera's FluCard internal network

# The following is the Internet capable SSID/Password
SSID1='wirelessname1'
PSWD1='password1'
DESC1='Internet-capable WiFi. DropBox should sync shortly'
# The following is the SSID/Password for the camera's FluCard access.
CAMERA_SSID='FluCardSSID'
CAMERA_PSWD='FluPassword'
CAMERA_DESC='Connected to camera. FYI, no Internet will be available'

# Get current SSID name.
ssidname=$(networksetup -getairportnetwork en1 | cut -c 24-)

# Find which one we're on and swap.
if [ $ssidname == $SSID1 ]
then
    ssidname=$CAMERA_SSID
    password=$CAMERA_PSWD
    description=$CAMERA_DESC
else
    ssidname=$SSID1
    password=$PSWD1
    description=$DESC1
fi

# Status....
echo "Switching to network: $ssidname ..."
networksetup -setairportnetwork en1 $ssidname $password

# We should not need to sleep, but just to ba safe.
sleep 2

# Now get the current SSID again. If it is what we expect, we're good to go.
newssidname=$(networksetup -getairportnetwork en1 | cut -c 24-)
if [ $ssidname == $newssidname ]
then
    echo "++ Successfully changed to $ssidname ++"
    echo "+( $description )+"
    echo " "
else
    echo "[!] ==================================="
    echo "[!] FAILED to change network. Still: $newssidname"
    echo "[!] If connecting to camera, half-press to wake up and wait 30 seconds"
    echo "[!] ==================================="
fi

