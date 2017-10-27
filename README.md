Requires Python 2.7 with 'requests' module.

# fluImport.py
Auto Import photos from the Ricoh FluCard Pro-1 card (any camera that supports the FluCard Pro-1).
No longer being worked on.  But functions well enough. 

# k1Import.py
Auto Import photos from the Pentax K1. Requires Python 2.7 with 'requests' module.

Notes:
- At the moment when the card contains more than about 500 photos, you mght start to see some slow down 
and communication craps out intermittently.  Just break and restart the Python script.

- The K1 APIs are a bit more advanced than the FluCard.
With that, there is room for improvement with how the latest unread photos might be 
determined and the above issue might be avoidable.
