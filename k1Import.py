"""Author: Anthony Moringello Photography.

        & Psychotic Psoftware

Licensing: Creative Commons.
Use and modify as you wish, but I would appreciate attribution.
Look me up under Anthony Moringello Photography if you wish to make any donation for my effort.

Purpose::

Import any new files from K1 to a specified folder.

Main intent to be used with LightRoom's Auto Import.
LightRoom will import and remove any existing files form the AutoImport directory.
So in order to not re-download existing files, we must store known already downloaded
files in some sort of 'database'. A simple text file will be sufficient.
We will also assume all images are named in a monotonically increasing fashion.
i.e. the last imported will have the highest numbered filename.
Special case when 9999 rolls over to 0000.

You must choose a Dest Dir (-d flag) on first use.  After that, the same folder will be used
without needing to specify the location.

Database will retain::

    - initialization date in seconds
    - 'first' imported file
    - 'last' imported file
    - rollover flag
    - Destination AutoImport Dir
    This database file is created in:  '/Library/Preferences/com.PsychoticPsoftware.FluImport.json'
    See K1BASE_DIR and K1BASE_FILE to change specific to your OS requirements.

Filenames are assumed to be four characters followed by four numbers. e.g. 'ABCD1234.jpg'.
By default, only .JPG files will be downloaded.  Use the '--getdng' flag to download raw images.

The program will clean/reset the database file on startup if it has been more than two days since
the last file download occurred.  This makes sense in most cases, as the card will eventually
roll over file numbers and we need a way to not get confused.
NOTE: This does mean that after two days, EVERY file on the card will be re-downloaded.
It should be a best practice to clean your card before any major use.

USAGE::

    -h, --help:                     Show a help message and exit.
    -i IPADDR, --ipaddr IPADDR:     The K1's internal WiFi Server IP Address
    -d DESTDIR, --destdir DESTDIR:  Destination dir to place new photos. Will use prior location if not set.
    -r REFRESH, --refresh REFRESH:  Time in seconds to re-check for new photos.
    -s SDCARD, --sdcard SDCARD#:    SDCard Slot. (1 | 2)
    -g, --getdng:                   Download DNG file instead of default JPEG. THIS WILL BE SLOW.
    -t, --test:                     Start in test mode. Used to help reverse engineer and diagnose Rest functions.
    --clean:                        Write a clean preferences file. All files will be downloaded from card.
    --debug:                        Debug. Probably more of a verbose mode than debug.



NOTE K1 REST API::

    '/v1/photos/path'
    '/v1/photos:path/info'
    '/v1/photos/latest/info'
    '/v1/photos?storage=sd{1,2}'
    '/v1/photos/102_1026/_AMP9018.DNG?storage=sd1'
    '/v1/photos/102_1026/_AMP9018.JPG?storage=sd2'
    '/v1/props'
    '/v1/props/camera'
    '/v1/props/lens'
    '/v1/props/liveview'
    '/v1/props/device'
    '/v1/variables'
    '/v1/variables/camera'
    '/v1/variables/lens'
    '/v1/variables/liveview'
    '/v1/variables/device'
    '/v1/status'
    '/v1/status/camera'
    '/v1/status/lens'
    '/v1/status/liveview'
    '/v1/status/device'
    '/v1/params'
    '/v1/params/camera'
    '/v1/params/lens'
    '/v1/params/liveview'
    '/v1/params/device'
    '/v1/constants'
    '/v1/constants/camera'
    '/v1/constants/lens'
    '/v1/constants/liveview'
    '/v1/constants/device'
    '/v1/ping'
    '/v1/liveview'
    '/v1/params/camera'
    '/v1/params/device'
    '/v1/camera/shoot'
    '/v1/camera/shoot/start'
    '/v1/camera/shoot/finish'
    '/v1/lens/focus'
    '/v1/liveview/zoom'
    '/v1/changes'
    '/v1/apis'

    Add ?storage=sd{1,2}
    E.g. ?http://192.168.0.1/v1/photos?storage=sd2?
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any

import requests  # type: ignore  FYI, No higher than Python 3.11
from requests.exceptions import Timeout

# Note: User Modifyable for now -- For future work, change depending on platform.
# These are Macintosh locations.  Change to something useful for Windows or Linux.
K1BASE_DIR = "/Library/Preferences"  # Will be added to user's Home path
K1BASE_FILE = "com.PsychoticPsoftware.K1Import.json"
DEBUG = False


class PentaxWiFi:
    """Communication class for Pentax WiFi."""

    def __init__(self, args: argparse.Namespace) -> None:
        """Init."""
        # get args
        self.destdir: str = str(args.destdir)
        self.ipaddr: str = args.ipaddr
        self.refresh: float = args.refresh
        self.clean: bool = args.clean
        # get initial existing photo list
        self.k1base: dict[str, Any] = self.get_k1_base_data()
        # tack onto http request to specify SD card slot
        self.sdparam = "storage=sd" + str(args.sdcard)
        self.suffix: str = ".DNG" if args.getdng else ".JPG"

        if not os.path.isdir(self.destdir):  # noqa: PTH112
            raise ValueError("Storage Directory does not exist: " + self.destdir)

    def get_k1_base_data(self) -> dict[str, Any]:
        """Obtain values from k1base preferences database file.

        Returns:
            Dictionary of values

        """
        cwd = os.getcwd()  # save original dir  # noqa: PTH109
        homedir = os.path.expanduser("~") + K1BASE_DIR  # noqa: PTH111
        os.chdir(homedir)

        if not os.path.isfile(K1BASE_FILE) or self.clean:  # noqa: PTH113
            # User should set a Destination Auto Import dir. If not, report error and exit.
            # Do not create initial preferences file.
            if self.destdir == "None":
                msg = "Please choose a Destination Auto Import Dir with the '-d' flag."
                raise ValueError(msg)

            # Create new file if none exists
            k1base = self.new_k1base_file()
        else:
            with open(K1BASE_FILE) as datafile:  # noqa: PTH123
                k1base = json.load(datafile)

            if self.destdir == "None":
                if "destDir" in k1base:
                    self.destdir = k1base["destDir"]
                    print_debug("Using prior Photo Dir:" + str(self.destdir))
                else:
                    msg = "Prior AutoImport Dir not found in Preference file.  Supply on command line."
                    raise AttributeError(msg)

            last_seconds = k1base["lastSeconds"]
            cur_seconds = time.time()
            # Check if last update was two days ago or more (86400 seconds per day)
            if cur_seconds - last_seconds >= 172800:
                # k1base file is too old.  Create new one.
                # NOTE: This does mean EVERY file on the card will be imported!
                k1base: dict[str, Any] = self.new_k1base_file()

        os.chdir(cwd)  # Get back to original dir
        return k1base

    def new_k1base_file(self) -> dict[str, Any]:
        """Create new k1base preferences file.

        This puts things in a state where EVERY file on the SD Card will be imported.
        Normally this is a good thing, as when this program is first run.
        The database is also reset after two days, which in most cases makes sense.

        Returns:
            Dictionary of values

        """
        # 86400 seconds per day
        print_debug("Creating new k1base file.")
        seconds: float = time.time()
        k1base: dict[str, Any] = {
            "firstDir": "None",
            "firstFile": "None",
            "lastDir": "None",
            "lastFile": "None",
            "rollover": False,
            "lastSeconds": seconds,
            "destDir": str(self.destdir),
        }
        with open(file=K1BASE_FILE, mode="w") as outfile:  # noqa: PTH123
            json.dump(obj=k1base, fp=outfile)

        return k1base

    def update_k1_base_data(self) -> None:
        """Write new info to k1base file.

        Stores latest captured file info so we can re-run and continue from where we left off.

        Returns:
            None

        """
        cwd = os.getcwd()  # save original dir  # noqa: PTH109
        homedir = os.path.expanduser("~") + K1BASE_DIR  # noqa: PTH111
        os.chdir(homedir)

        seconds = time.time()
        self.k1base = {
            "firstDir": self.k1base["firstDir"],
            "firstFile": self.k1base["firstFile"],
            "lastDir": self.k1base["lastDir"],
            "lastFile": self.k1base["lastFile"],
            "rollover": self.k1base["rollover"],
            "lastSeconds": seconds,
            "destDir": str(self.destdir),
        }
        with open(K1BASE_FILE, "w") as outfile:  # noqa: PTH123
            json.dump(self.k1base, outfile)
        os.chdir(cwd)

    def get_photo_list(self) -> list[str]:
        """Get list of photos from PentaxWiFi. Parse into list of image URLs.

        Returns:
            list[str]: List of image URLs. None if connection failed.

        """
        url_photo_list = "http://" + self.ipaddr + "/v1/photos" + "?" + self.sdparam
        print_debug("Get photo list from URL: " + url_photo_list)
        # noinspection PyBroadException
        try:
            r = requests.get(url_photo_list, timeout=(2, 5))
        except Timeout:
            print_debug("Connection timeout on PhotoList. Will re-try. ")
            return []

        if r.status_code != 200:
            return []
        photolist: list[str] = self.parse_photo_list_json(r)
        return photolist

    def parse_photo_list_json(self, content: requests.Response) -> list[str]:
        """Parse JSON of Folder/Files list obtained from camera.

        Create a simple list of full URL to image;
            http://{ipAddr}/v1/photos/{folder}/{photoName}

        Args:
            content (request.Response): content object from http request

        Returns:
            list[str]: list of image URLs or None

        """
        photojson: dict[str, Any] = json.loads(content.text)
        photolist: list[str] = []
        for dirs in photojson["dirs"]:
            folder_name = dirs["name"]
            for filename in dirs["files"]:
                photo_url = (
                    "http://"
                    + self.ipaddr
                    + "/v1/photos/"
                    + folder_name
                    + "/"
                    + filename
                )

                # BY default, we only want .JPG files. But is now user-specified.
                photo_sfx = os.path.splitext(photo_url)  # noqa: PTH122
                if photo_sfx[1] == self.suffix:
                    photolist.append(photo_url)

        if len(photolist) > 0:
            photo_url = photolist[-1]
            photo_name = os.path.basename(photo_url)  # noqa: PTH119
            # # Assume format "ABCD1234.sfx"
            # photo_number = int(photo_name[4:8])  # returns "1234"

            print_debug("Last photo seen: " + photo_name)
            return photolist

        return []

    def download_photo(self, photo_url: str) -> bool:
        """Download photo data from the card.

        Args:
            photo_url: URL of photo do download. e.g. 'http://192.168.0.1/v1/photos/104_1125/_AMP0061.JPG?storage=sd2'

        Returns:
            True if file is written successfully

        """
        photo_name = os.path.basename(photo_url)  # noqa: PTH119
        print("Downloading: " + photo_name)  # noqa: T201 -- yes we want PRINT

        r: requests.Response = requests.get(photo_url + "?" + self.sdparam)  # noqa: S113
        # noinspection PyBroadException
        try:
            filename = self.destdir + "/" + str(photo_name)
            with open(filename, "wb") as outfile:  # noqa: PTH123
                data = bytearray(r.content)
                outfile.write(data)
        except Exception:  # we dont care why the exception happened. # noqa: BLE001
            print_debug("Error writing file. Will re-try later.")
            return False

        return True

    def get_new_photos(self) -> None:  # noqa: C901, PLR0912  # aww, wanna cry; too complex?
        """Download all new photos and update k1base file.

        Returns:
            None

        """
        photo_list: list[str] = self.get_photo_list()
        if not photo_list:
            return
        for photo_url in photo_list:
            if self.k1base["lastFile"] == "None":  # noqa: SIM108
                last_num = -1
            else:
                last_num = int(self.k1base["lastFile"])
            if self.k1base["firstFile"] == "None":  # noqa: SIM108
                first_num = -1  # accept any file number on first download
            else:
                first_num = int(self.k1base["firstFile"])

            photo_name = os.path.basename(photo_url)  # noqa: PTH119
            # Assume format "ABCD1234.sfx"
            photo_number = int(photo_name[4:8])  # returns "1234"
            download = False

            if (
                self.k1base["rollover"] is False
                and photo_number > last_num
                and photo_number > first_num
            ):
                download = True
            if self.k1base["rollover"] is True and (
                (last_num < photo_number < first_num) or last_num == 9999
            ):
                download = True

            if download:
                if photo_number == first_num:
                    print_debug("Rollover limit...")
                    # for i in range(1,5):
                    #     self.pentaxwifi_play_beep()
                    # break
                # DOWNLOAD NEW PHOTO(S)
                if not self.download_photo(photo_url):
                    # Failed. Retry later. Do not update k1base, do not pass Go.
                    break
                if photo_number == 9999:
                    self.k1base["rollover"] = True
                self.k1base["lastFile"] = str(photo_number)
                if self.k1base["firstFile"] == "None":
                    self.k1base["firstFile"] = str(photo_number)
                # Be sure to update after each download in case of intermediate failure.
                self.update_k1_base_data()

    def test(self, testarg: str) -> None:
        """Get list of photos from PentaxWiFi. Parse into list of URLs to images.

        Returns:
            None

        """
        if testarg == "?":
            print(  # noqa: T201 -- yes we want PRINT
                """
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
""",
            )
            return

        url = "http://" + self.ipaddr + "/v1/" + testarg
        print("URL: " + url)  # noqa: T201
        # noinspection PyBroadException
        try:
            r = requests.get(url)  # noqa: S113
        except Exception:  # noqa: BLE001
            print_debug("error...")
            return

        if r.status_code == 200:
            print("Result: \n")  # noqa: T201
            print(r.content)  # noqa: T201
            return
        print("Non-200 result")  # noqa: T201
        return


def print_debug(args: str) -> None:
    """Print debug message."""
    if DEBUG:
        print("DEBUG: " + args)  # noqa: T201


# The 'type=str' in the parser.add_argument will cause IDE warnings.  Ignore them.
# noinspection PyTypeChecker
def main() -> None:
    """Main, start here."""
    global DEBUG  # noqa: PLW0603  # This rule is WRONG. BE EXPLICIT TO AVOID BUGS!
    parser = argparse.ArgumentParser(description="Get new files from PentaxWiFi")
    parser.add_argument(
        "-i",
        "--ipaddr",
        type=str,
        default="192.168.0.1",
        help="K1 internal WiFi Server IP Address",
    )
    parser.add_argument(
        "-d",
        "--destdir",
        type=str,
        default="None",
        help="Destination dir to place new photos. Will use prior location if not set.",
    )
    parser.add_argument(
        "-r",
        "--refresh",
        type=int,
        default=2,
        help="Time in seconds to re-check for new photos.",
    )
    parser.add_argument("-s", "--sdcard", type=int, default=2, help="SDCard Slot. (1 | 2)")
    parser.add_argument(
        "-g",
        "--getdng",
        action="store_true",
        default=False,
        help="Download DNG file instead of default JPEG. THIS WILL BE SLOW.",
    )
    parser.add_argument("-t", "--test", action="store_true", default=False, help="Start in test mode")
    parser.add_argument(
        "--clean",
        help="Write a clean preferences file. All files will be downloaded from card.",
        action="store_true",
        default=False,
    )
    parser.add_argument("--debug", help="Debug", action="store_true", default=False)
    args = parser.parse_args()

    if args.debug:
        DEBUG = True  # type: ignore We know what we're doing. F- constants

    # Set initial state for TESTRUN.
    testrun = False
    if args.test:
        testrun = True

    if args.sdcard not in [1, 2]:
        msg = "SDCard must be either 1 or 2"
        raise ValueError(msg) from None

    print_debug("Debug:     " + str(args.debug))
    print_debug("Clean:     " + str(args.clean))
    print_debug("IP Addr:   " + str(args.ipaddr))
    print_debug("Photo Dir: " + str(args.destdir))
    print_debug("Refresh:   " + str(args.refresh))
    print_debug("SD Card:   " + str(args.sdcard))
    print_debug("FileType:  " + ("DNG" if args.getdng else "JPG"))

    fc = PentaxWiFi(args)
    print_debug("LastFile:  {}".format(fc.k1base["lastFile"]))

    while 1:
        if testrun:  # Allow user to enter commands.
            myarg = input("Enter Command: ")
            if myarg == "run":
                testrun = False  # Next loop, stop testing and do actual intended functionality
                continue
            fc.test(myarg)
        else:  # Actualy do what we're intended to do.  No testing.
            fc.get_new_photos()
            # Wait some time and try again.....
            time.sleep(fc.refresh)


if __name__ == "__main__":
    main()
