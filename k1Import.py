'''
Author: Anthony Moringello Photography
        & Psychotic Psoftware

Licensing: Creative Commons.
Use and modify as you wish, but I would appreciate attribution.
Look me up under Anthony Moringello Photography if you wish to make any donation for my effort.

Purpose:
Import any new files from FluCard to a specified folder.

Main intent to be used with LightRoom's Auto Import.
LightRoom will import and remove any existing files form the AutoImport directory.
So in order to not re-download existing files, we must store known already downloaded
files in some sort of "database". A simple text file will be sufficient.
We will also assume all images are named in a monotonically increasing fashion.
i.e. the last imported will have the highest numbered filename.
Special case when 9999 rolls over to 0000.

You must choose a Dest Dir (-d flag) on first use.  After that, the same folder will be usedwithout needing to specify thelocation.

Database will retain:
- initialization date in seconds
- "first" imported file
- "last" imported file
- rollover flag
- Destination AutoImport Dir
This database file is created in:  '/Library/Preferences/com.PsychoticPsoftware.FluImport.json'
See FLUBASE_DIR and FLUBASE_FILE to change specific to your OS requirements.

Filenames are assumed to be four characters followed by four numbers. e.g. "ABCD1234.jpg".
This program makes no assumption with regards to files being of type JPG or RAW format.
Whatever is saved to the FluCard will be captured.

The program will reset the database file on startup if it has been more than two days since the last
file download occurred.  This makes sens in most cases, as the card will eventuallty roll over
file numbers and we need a way to not get confused.
NOTE: This does mean that after two days, EVERY file on the card will be re-downloaded.
It is a best practice to clean your card before any major use.
'''

import requests
import argparse
import os
import time
import json

FLUBASE_DIR = '/Library/Preferences'
FLUBASE_FILE = 'com.PsychoticPsoftware.K1Import.json'
DEBUG=False

class FluCard:

    def __init__(self, args):
        # get args
        self.destdir = args.destdir
        self.ipaddr  = args.ipaddr
        self.refresh = args.refresh
        # get initial existing photo list
        self.flubase = self.get_flu_base_data()

        if not os.path.isdir(self.destdir):
            raise ValueError('Storage Directory does not exist: ' + self.destdir)

    def get_flu_base_data(self):
        '''
        Obtain values from flubase database.
        :return: Dictionary of values
        '''
        cwd = os.getcwd() # save original dir
        homedir = os.path.expanduser("~") + FLUBASE_DIR
        os.chdir(homedir)

        if not os.path.isfile(FLUBASE_FILE):
            # User should set a Destination Auto Import dir. If not, report error and exit.
            # Do not create initial preferences file.
            if self.destdir == 'None':
                raise ValueError("Please choose a Destination Auto Import Dir with the '-d' flag.")

            # Create new file if none exists
            flubase = self.new_flubase_file()
        else:
            with open (FLUBASE_FILE) as datafile:
                flubase = json.load(datafile)

            if self.destdir == 'None':
                if 'destDir' in flubase:
                    self.destdir = flubase['destDir']
                    print_debug("Using prior Photo Dir:" + str(self.destdir))
                else:
                    raise AttributeError("Prior AutoImport Dir not found in Preference file.  Supply on command line.")
                
            lastSeconds = flubase['lastSeconds']
            curSeconds = time.time()
            # Check if last update was two days ago or more (86400 seconds per day)
            if curSeconds - lastSeconds >= 172800:
                # fluBase file is too old.  Create new one.
                #NOTE# This does mean EVERY file on th ecard will be imported!
                flubase = self.new_flubase_file()

        os.chdir(cwd)   # Get back to original dir
        return flubase

    def new_flubase_file(self):
        '''
        Create new fluBase preferences file.
        This puts things ins state where EVERY file on the FluCard will be imported.
        Normally this is a good thing, as when this program is first run.
        The database is also reset after two days, which in most cases makes sense.
        :return: no returns
        '''
        # 86400 seconds per day
        print_debug("Creating new FluBase file.")
        seconds = time.time()
        flubase = {
            'firstFile'     : 'None',
            'lastFile'      : 'None',
            'rollover'      : False,
            'lastSeconds'   : seconds,
            'destDir'       : str(self.destdir)
            }
        with open(FLUBASE_FILE, 'w') as outfile:
            json.dump(flubase, outfile)

        return flubase

    def get_dest_dir_photo_list(self):
        '''
        Get list of photo names in self.destdir.

        :return: List of existing files in self.destdir
        '''
        files = os.listdir(self.destdir)
        return files

    def get_new_photos(self):
        photoList = self.get_photo_list()
        if photoList == None:
            return
        for photoURL in photoList:
            if self.flubase['lastFile'] == 'None':
                lastNum = -1
            else:
                lastNum = int(self.flubase['lastFile'])
            if self.flubase['firstFile'] == 'None':
                firstNum = -1  # accept any file number on first download
            else:
                firstNum = int(self.flubase['firstFile'])

            photoName = os.path.basename(photoURL)
            # Assume format "ABCD1234.sfx"
            photoNumber = int(photoName[4:8]) # returns "1234"
            download = False

            if self.flubase['rollover'] == False and photoNumber > lastNum and photoNumber > firstNum:
                download = True
            if self.flubase['rollover'] == True and ((photoNumber < firstNum and photoNumber > lastNum) or lastNum == 9999):
                download = True

            if download == True:
                if photoNumber == firstNum:
                    print_debug ("Rollover limit...")
                    for i in range(1,5):
                        self.flucard_play_beep()
                    break
                # DOWNLOAD NEW PHOTO(S)
                if self.downloadPhoto(photoURL) == False:
                    # Failed. Retry later. Do not update flubase, do not pass Go.
                    break
                if photoNumber == 9999:
                    self.flubase['rollover'] = True
                self.flubase['lastFile'] = str(photoNumber)
                if self.flubase['firstFile'] == 'None':
                    self.flubase['firstFile'] = str(photoNumber)
                # Be sure to update after each download in case of intermediate failure.
                self.update_flu_base_data()

    def downloadPhoto(self, photoURL):
        '''

        :param photoURL: URL;         # 'http://192.168.0.1/v1/photos/104_1125/_AMP0061.DNG'
                                      # add '?size=full'

        :return: none
        '''
        photoName = os.path.basename(photoURL)
        print_debug ("Downloading: " + photoName)

        r = requests.get(photoURL + '?size=full')
        try:
            filename =  self.destdir + '/' + str(photoName)
            with open(filename, "wb") as outfile:
                data=bytearray(r.content)
                outfile.write(data)
        except:
            print_debug ('Error writing file. Will re-try later.')
            return False

        return True


    def update_flu_base_data(self):
        '''
        Write new info to flubase file.
        :return:
        '''
        cwd = os.getcwd() # save original dir
        homedir = os.path.expanduser("~") + FLUBASE_DIR
        os.chdir(homedir)

        seconds = time.time()
        self.flubase = {
            'firstFile'     : self.flubase['firstFile'],
            'lastFile'   : self.flubase['lastFile'],
            'rollover'      : self.flubase['rollover'],
            'lastSeconds'      : seconds,
            'destDir': str(self.destdir)
        }
        with open(FLUBASE_FILE, 'w') as outfile:
            json.dump(self.flubase, outfile)
        os.chdir(cwd)

    def get_photo_list(self):
        '''
        Get list of photos from FluCard. Parse into list of URLs to images.
        :return: List of image URLs. None if connection failed.
        '''
        urlPhotoList = 'http://' + self.ipaddr + '/v1/photos'
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
        Parse JSON of Folder/Files list.
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

                # For now, we only want .JPG files.
                # Until we have a way to specifiy Card2 v.s. Card1, we will
                # look at everything on Card 1 but just grab JPG.
                photoSfx = os.path.splitext(photourl)
                if photoSfx[1].lower() == '.jpg':
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

def print_debug(args):
    if DEBUG == True:
        print "DEBUG: " + args

def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Get new files from FluCard')
    parser.add_argument('-i', '--ipaddr', type=str, default='192.168.0.1',help='K1 WiFi Server IP Address')
    parser.add_argument('-d', '--destdir', type=str, default='None', help='Destination dir to place new photos. Will use prior location if not set.')
    parser.add_argument('-r', '--refresh', type=int, default=2, help='Time in second to re-check for new photos.')
    parser.add_argument('--debug',  help='Debug', action='store_true', default=False)
    args = parser.parse_args()

    if args.debug == True:
        DEBUG=True

    print_debug("Debug:     " + str(args.debug))
    print_debug("IP Addr:   " + str(args.ipaddr))
    print_debug("Photo Dir: " + str(args.destdir))
    print_debug("Refresh:   " + str(args.refresh))
    print "\n*IMPORTANT* Be sure to save JPG to Card 1, or Raw+JPG. Api cannot access card 2, yet.\n"

    fc = FluCard(args)

    while (1):
        result = fc.get_new_photos()

        # Wait some time and try again.....
        time.sleep(fc.refresh)

if __name__ == '__main__':
    main()
