Requires Python 2.7 with 'requests' module.

# fluImport.py
Auto Import photos from the Ricoh FluCard Pro-1 card (any camera that supports the FluCard Pro-1).
No longer being worked on since the card is no longer sold nor supported.  But functions well enough.
I still use this script regularly.

# k1Import.py
Auto Import photos from the Pentax K1.

Notes:
- The lastest fixes now allow much more than 500 photos to be downloaded before things slow down.
It still isn't perfect, but I can now go most of a full day event without restarting the script.
At some point you might start to see some slow down and communication craps out intermittently.  
Just break and restart the Python script. It will safely pick up where it left off.

- If you take more than 1000 photos and the camera rolls over into a new folder, I suspect this
script may fail to get new photos.   

- The K1 APIs are a bit more advanced than the FluCard.
With that, there is room for improvement with how the latest unread photos might be 
determined and the above issue might be avoidable.

