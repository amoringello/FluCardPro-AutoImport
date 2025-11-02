
IMPORTANT: Requires 'requests' module.
           At one time requests module did not work with Pytohnn 3.12.
           This has been fixed in late 2024. Be sure to update your Python
           and modules to ensure the requests module is functional.

See further important notes below.

# fluImport.py
Auto Import photos from the Ricoh FluCard Pro-1 card (any camera that supports the FluCard Pro-1).

This is no longer being worked on since the card is no longer sold nor supported.
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

IMPORTANT:

    Python module 'requests' is a required prerequisite.  
    Python no longer likes you to install new modules to the system installation.
    Use of Python Environments are strongly encouraged.

A 'Pipfile' for use with pipenv has been included. Do the following::

    $ pienv install
    $ pipenv run python3 k1import.py -d <full path to store files> 

NOTE::

For newer OSX you may have better luck staying with the build-in Python version.
e.g. Tahoe uses Python 3.9.  Therefore, do:
$ pipenv --python 3.9 install

I have had trouble with Homebrew installations of newer Python versions finding the necessary prerequisites. 
Give them a try if you wish, it may just take some tweaking to get the new prerequisites working.  
I have done it, but every new Python3 release has its own issues.
If you don't have time to debug Python environments stick with the OS version.




