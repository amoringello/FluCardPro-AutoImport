Requires Python 2.7 with 'requests' module.

# fluImport.py
Auto Import photos from the Ricoh FluCard Pro-1 card (any camera that supports the FluCard Pro-1). 

# k1Import.py
Auto Import photos from the Pentax K1. Requires Python 2.7 with 'requests' module.
Note, the K1 will currently only import JPEGs from card1.  If anyone knows the API to change which card is selected, that would be AAWESOME!

I apologize for the comment issues confusing K1 and FluCard. 
This is my first Git project and I apparently screwed that up.
But hopefully the code comments are good enough to follow tyhrough and modify if needed.

Notes:
- At the moment when the card contains more than about 500 photos, you mght start to see some slow down 
and communication craps out intermittently.  Just break and restart the Python script.

- The K1 APIs are a bit more advanced than the FluCard.
With that, there is room for improvement with how the latest unread photos might be 
determined and the above issue might be avoidable.
