
IMPORTANT: Requires 'requests' module.
           At one time requests module did not work with Pytohnn 3.12.
           This has been fixed in late 2024. Be sure to update your Python
           and modules to ensure the requests module is functional.


# fluImport.py
Auto Import photos from the Ricoh FluCard Pro-1 card (any camera that supports the FluCard Pro-1).
No longer being worked on since the card is no longer sold nor supported.
But should function well enough if you have one fo these cards.

# k1Import.py
Auto Import photos from the Pentax K1.
See main docstring for usage.

Notes:
- The lastest fixes now allow much more than 500 photos to be downloaded before things slow down.
It still isn't perfect, but I can now go most of a full day event without restarting the script.
At some point you might start to see some slow down and communication craps out intermittently.  
Just break and restart the Python script. It will safely pick up where it left off.

- If you take more than 1000 photos and the camera rolls over into a new folder, I suspect this
script may fail to get new photos.   

- The K1 APIs are a bit more advanced than the FluCard.
With that, there is room for improvement with how the latest unread photos might be 
determined and the above issue might be avoidable.  But I have not found the need to 
invest the time to research the alternatives.  


If you like Python environments, you can do the following...
$ pienv install
$ pipenv run python3 k1import.py -d <full path to store files> 

