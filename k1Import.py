'''
Author: Anthony Moringello Photography
        & Psychotic Psoftware

Licensing: Creative Commons.
Use and modify as you wish, but I would appreciate attribution.
Look me up under Anthony Moringello Photography if you wish to make any donation for my effort.

Purpose:
Import any new files from K1 to a specified folder.

Main intent to be used with LightRoom's Auto Import.
LightRoom will import and remove any existing files form the AutoImport directory.
So in order to not re-download existing files, we must store known already downloaded
files in some sort of "database". A simple text file will be sufficient.
We will also assume all images are named in a monotonically increasing fashion.
i.e. the last imported will have the highest numbered filename.
Special case when 9999 rolls over to 0000.

You must choose a Dest Dir (-d flag) on first use.  After that, the same folder will be used
without needing to specify the location.

Database will retain:
- initialization date in seconds
- "first" imported file
- "last" imported file
- rollover flag
- Destination AutoImport Dir
This database file is created in:  '/Library/Preferences/com.PsychoticPsoftware.FluImport.json'
See K1BASE_DIR and K1BASE_FILE to change specific to your OS requirements.

Filenames are assumed to be four characters followed by four numbers. e.g. "ABCD1234.jpg".
This program makes no assumption with regards to files being of type JPG or RAW format.
Whatever is saved to the SD Card will be captured.

The program will reset the database file on startup if it has been more than two days since the last
file download occurred.  This makes sense in most cases, as the card will eventually roll over
file numbers and we need a way to not get confused.
NOTE: This does mean that after two days, EVERY file on the card will be re-downloaded.
It is a best practice to clean your card before any major use.


K1 REST API
"/v1/photos/path"
"/v1/photos:path/info"
"/v1/photos/latest/info"
"/v1/photos?storage=sd{1,2}"
"/v1/photos/102_1026/_AMP9018.DNG?storage=sd1"
"/v1/photos/102_1026/_AMP9018.JPG?storage=sd2"
"/v1/props"
"/v1/props/camera"
"/v1/props/lens"
"/v1/props/liveview"
"/v1/props/device"
"/v1/variables"
"/v1/variables/camera"
"/v1/variables/lens"
"/v1/variables/liveview"
"/v1/variables/device"
"/v1/status"
"/v1/status/camera"
"/v1/status/lens"
"/v1/status/liveview"
"/v1/status/device"
"/v1/params"
"/v1/params/camera"
"/v1/params/lens"
"/v1/params/liveview"
"/v1/params/device"
"/v1/constants"
"/v1/constants/camera"
"/v1/constants/lens"
"/v1/constants/liveview"
"/v1/constants/device"
"/v1/ping"
"/v1/liveview"
"/v1/params/camera"
"/v1/params/device"
"/v1/camera/shoot"
"/v1/camera/shoot/start"
"/v1/camera/shoot/finish"
"/v1/lens/focus"
"/v1/liveview/zoom"
"/v1/changes"
"/v1/apis"

Add ?storage=sd{1,2}
E.g. ?http://192.168.0.1/v1/photos?storage=sd2?
'''

import requests
import argparse
import os
import time
import json

# TODO: User Modifyable for now -- Change depending on platform.
# These are Macintosh locations.  Change to something useful for Windows or Linux.
K1BASE_DIR = '/Library/Preferences'
K1BASE_FILE = 'com.PsychoticPsoftware.K1Import.json'
DEBUG=False

class PentaxWiFi:

    def __init__(self, args):
        # get args
        self.destdir = args.destdir
        self.ipaddr  = args.ipaddr
        self.refresh = args.refresh
        # get initial existing photo list
        self.k1base = self.get_k1_base_data()
        self.sdparam = "storage=sd"+str(args.sdcard)   # tack onto http request to specify SD card slot
        self.suffix = (".DNG" if args.getdng else ".JPG")

        if not os.path.isdir(self.destdir):
            raise ValueError('Storage Directory does not exist: ' + self.destdir)

    def get_k1_base_data(self):
        '''
        Obtain values from k1base preferences database file.
        :return: Dictionary of values
        '''
        cwd = os.getcwd() # save original dir
        homedir = os.path.expanduser("~") + K1BASE_DIR
        os.chdir(homedir)

        if not os.path.isfile(K1BASE_FILE):
            # User should set a Destination Auto Import dir. If not, report error and exit.
            # Do not create initial preferences file.
            if self.destdir == 'None':
                raise ValueError("Please choose a Destination Auto Import Dir with the '-d' flag.")

            # Create new file if none exists
            k1base = self.new_K1BASE_FILE()
        else:
            with open (K1BASE_FILE) as datafile:
                k1base = json.load(datafile)

            if self.destdir == 'None':
                if 'destDir' in k1base:
                    self.destdir = k1base['destDir']
                    print_debug("Using prior Photo Dir:" + str(self.destdir))
                else:
                    raise AttributeError("Prior AutoImport Dir not found in Preference file.  Supply on command line.")

            lastSeconds = k1base['lastSeconds']
            curSeconds = time.time()
            # Check if last update was two days ago or more (86400 seconds per day)
            if curSeconds - lastSeconds >= 172800:
                # k1base file is too old.  Create new one.
                #NOTE# This does mean EVERY file on th ecard will be imported!
                k1base = self.new_K1BASE_FILE()

        os.chdir(cwd)   # Get back to original dir
        return k1base

    def new_K1BASE_FILE(self):
        '''
        Create new k1base preferences file.
        This puts things in a state where EVERY file on the SD Card will be imported.
        Normally this is a good thing, as when this program is first run.
        The database is also reset after two days, which in most cases makes sense.
        :return: no returns
        '''
        # 86400 seconds per day
        print_debug("Creating new k1base file.")
        seconds = time.time()
        k1base = {
            'firstFile'     : 'None',
            'lastFile'      : 'None',
            'rollover'      : False,
            'lastSeconds'   : seconds,
            'destDir'       : str(self.destdir)
            }
        with open(K1BASE_FILE, 'w') as outfile:
            json.dump(k1base, outfile)

        return k1base

    def update_k1_base_data(self):
        '''
        Write new info to k1base file.
        Stores latest captured file info so we can re-run and continue from where we left off.
        :return: no returns
        '''
        cwd = os.getcwd() # save original dir
        homedir = os.path.expanduser("~") + K1BASE_DIR
        os.chdir(homedir)

        seconds = time.time()
        self.k1base = {
            'firstFile'     : self.k1base['firstFile'],
            'lastFile'   : self.k1base['lastFile'],
            'rollover'      : self.k1base['rollover'],
            'lastSeconds'      : seconds,
            'destDir': str(self.destdir)
        }
        with open(K1BASE_FILE, 'w') as outfile:
            json.dump(self.k1base, outfile)
        os.chdir(cwd)

    def get_photo_list(self):
        '''
        Get list of photos from PentaxWiFi. Parse into list of image URLs.
        :return: List of image URLs. None if connection failed.
        '''
        urlPhotoList = 'http://' + self.ipaddr + '/v1/photos' + "?" + self.sdparam
        print_debug("Get photo list from URL: " + urlPhotoList )
        try:
            r = requests.get(urlPhotoList)
        except:
            print_debug ("Connection timeout on PhotoList. Will re-try. ")
            return None

        if r.status_code != 200:
            return None
        photolist = self.parse_photo_list_json(r)
        return photolist

    def parse_photo_list_json(self, content):
        '''
        Parse JSON of Folder/Files list obtained from camera.
        Create a simple list of full URL to image;
            http://{ipAddr}/v1/photos/{folder}/{photoName}
        :param content: content object from http request
        :return: list of image URLs
        '''
        photojson = json.loads(content.text)
        photolist = []
        for dirs in photojson['dirs']:
            folderName = dirs['name']
            for file in dirs['files']:
                photourl = "http://"+self.ipaddr+"/v1/photos/"+folderName+"/"+file

                # BY default, we only want .JPG files. But is now user-specified.
                photoSfx = os.path.splitext(photourl)
                if photoSfx[1] == self.suffix:
                    photolist.append(photourl)

        if len(photolist) > 0:
            photoURL = photolist[-1]
            photoName = os.path.basename(photoURL)
            # Assume format "ABCD1234.sfx"
            photoNumber = int(photoName[4:8]) # returns "1234"

            print_debug("Last photo seen: " + photoName)
            return photolist
        else:
            return None

    def downloadPhoto(self, photoURL):
        '''
        :param photoURL: URL of photo do download. e.g. 'http://192.168.0.1/v1/photos/104_1125/_AMP0061.JPG?storage=sd2'
        :return: True if file is written successully
        '''
        photoName = os.path.basename(photoURL)
        print_debug ("Downloading: " + photoName)

        r = requests.get(photoURL + '?' + self.sdparam)
        try:
            filename =  self.destdir + '/' + str(photoName)
            with open(filename, "wb") as outfile:
                data=bytearray(r.content)
                outfile.write(data)
        except:
            print_debug ('Error writing file. Will re-try later.')
            return False

        return True

    def get_new_photos(self):
        '''
        Download all new photos and update k1base file.
        :return: No returns.
        '''
        photoList = self.get_photo_list()
        if photoList == None:
            return
        for photoURL in photoList :
            if self.k1base['lastFile'] == 'None':
                lastNum = -1
            else:
                lastNum = int(self.k1base['lastFile'])
            if self.k1base['firstFile'] == 'None':
                firstNum = -1  # accept any file number on first download
            else:
                firstNum = int(self.k1base['firstFile'])

            photoName = os.path.basename(photoURL)
            # Assume format "ABCD1234.sfx"
            photoNumber = int(photoName[4:8]) # returns "1234"
            download = False

            if self.k1base['rollover'] == False and photoNumber > lastNum and photoNumber > firstNum:
                download = True
            if self.k1base['rollover'] == True and ((photoNumber < firstNum and photoNumber > lastNum) or lastNum == 9999):
                download = True

            if download == True:
                if photoNumber == firstNum:
                    print_debug ("Rollover limit...")
                    # for i in range(1,5):
                    #     self.pentaxwifi_play_beep()
                    # break
                # DOWNLOAD NEW PHOTO(S)
                if self.downloadPhoto(photoURL) == False:
                    # Failed. Retry later. Do not update k1base, do not pass Go.
                    break
                if photoNumber == 9999:
                    self.k1base['rollover'] = True
                self.k1base['lastFile'] = str(photoNumber)
                if self.k1base['firstFile'] == 'None':
                    self.k1base['firstFile'] = str(photoNumber)
                # Be sure to update after each download in case of intermediate failure.
                self.update_k1_base_data()

    def test(self, testarg):
        '''
        Get list of photos from PentaxWiFi. Parse into list of URLs to images.
        :return: List of image URLs. None if connection failed.
        '''
        if testarg == "?":
            print '''
"photos/path"
"photos:path/info"
"photos/latest/info"
"photos"
"photos?storage=sd{1,2}"
"photos/102_1026/_AMP9018.DNG?storage=sd1"  - downloads DNG from card slot 1
"photos/102_1026/_AMP9018.JPG?storage=sd2"  - downloads JPG from card slot 2
"props"
"props/camera"
"props/lens"
"props/liveview"
"props/device"
"variables"
"variables/camera"
"variables/lens"
"variables/liveview"
"variables/device"
"status"
"status/camera"
"status/lens"
"status/liveview"
"status/device"
"params"
"params/camera"
"params/lens"
"params/liveview"
"params/device"
"constants"
"constants/camera"
"constants/lens"
"constants/liveview"
"constants/device"
"ping"
"liveview"
"params/camera"
"params/device"
"camera/shoot"
"camera/shoot/start"
"camera/shoot/finish"
"lens/focus"
"liveview/zoom"
"changes"
"apis"
 ?storage=sd{1,2}
'''
            return

        url = 'http://' + self.ipaddr + '/v1/' + testarg
        print "URL: " + url
        try:
            r = requests.get(url)
        except:
            print_debug ("error...")
            return None

        if r.status_code == 200:
            print "Result: \n"
            print r.content
            return None
        print "Non-200 result"
        return

def print_debug(args):
    if DEBUG == True:
        print "DEBUG: " + args



def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Get new files from PentaxWiFi')
    parser.add_argument('-i', '--ipaddr', type=str, default='192.168.0.1',help='K1 WiFi Server IP Address')
    parser.add_argument('-d', '--destdir', type=str, default='None', help='Destination dir to place new photos. Will use prior location if not set.')
    parser.add_argument('-r', '--refresh', type=int, default=2, help='Time in second to re-check for new photos.')
    parser.add_argument('-s', '--sdcard', type=int, default=2, help='SDCard Slot. (1 | 2)')
    parser.add_argument('-g', '--getdng', action='store_true', default=False, help='Download DNG file instead of default JPEG.')
    parser.add_argument('-t', '--test', action='store_true', default=False, help='Start in test mode')
    parser.add_argument('--debug',  help='Debug', action='store_true', default=False)
    args = parser.parse_args()

    if args.debug:
        DEBUG=True

    # Set initial state for TESTRUN.
    TESTRUN=False
    if args.test:
        TESTRUN=True

    if args.sdcard not in [1,2]:
        raise ValueError ("SDCard must be either 1 or 2")

    print_debug("Debug:     " + str(args.debug))
    print_debug("IP Addr:   " + str(args.ipaddr))
    print_debug("Photo Dir: " + str(args.destdir))
    print_debug("Refresh:   " + str(args.refresh))
    print_debug("SD Card:   " + str(args.sdcard))
    print_debug("FileType:  " + ("DNG" if args.getdng else "JPG"))

    fc = PentaxWiFi(args)


    while (1):
        if TESTRUN:  # Allow user to enter commands.
            myarg=raw_input("Enter Command: ")
            if myarg == "run":
                TESTRUN=False   # Next loop, stop testing and do actual intended functionality
                continue
            fc.test(myarg)
        else:       # Actualy do what we're intended to do.  No testing.
            result = fc.get_new_photos()
            # Wait some time and try again.....
            time.sleep(fc.refresh)

if __name__ == '__main__':
    main()
