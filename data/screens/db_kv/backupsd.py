#!/usr/bin/kivy
# -*- coding: utf-8 -*-

import os
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
import sqlite3
from jnius import autoclass  # SDcard Android

class BackupSD(Screen):
    lbtext = "Backup the current learning process to your (virtual) SD-card. " \
             "Backup is saved in sdcard/KanjiOrigin/ as Kanji-story_bak.db. " \
             "This backup is not directly detected by your computer, you first have to restart your phone. " \
             "Fix is planned for later."
    bttext = "Backup learning process"
    poplbtext = StringProperty("Backup went wrong")

    # Get path to SD card
    try:
        Environment = autoclass('android.os.Environment')
        sdpath = Environment.get_running_app().getExternalStorageDirectory()
        MediaScannerConnection = autoclass('android.media.MediaScannerConnection')
    except:
        sdpath = App.get_running_app().user_data_dir
    # TODO IOS

    print("Path SD: {}".format(sdpath))

    def callback(self):
        print("\nBackuping DB to SD-card...")

        sdpathfile = os.path.join(self.sdpath, 'Kanji-story_bak.db')
        localpathfile = os.path.join("data", "db", "Kanji-story.db")

        # Delete db if exist
        if os.path.isfile(sdpathfile):
            os.remove(sdpathfile)

        conn = sqlite3.connect(sdpathfile)
        c = conn.cursor()

        print("Attaching DB Kanji-story_bak.db")
        c.execute("ATTACH DATABASE ? AS db2", (localpathfile,))

        print("Transferring data to backup sd database...")

        # Get create Table code, then insert data from backup
        c.execute("SELECT sql FROM db2.sqlite_master WHERE type='table' AND name='current'")
        c.execute(c.fetchone()[0])
        c.execute("INSERT INTO main.current SELECT * FROM db2.current")
        print("Table 'current' transferred")

        c.execute("SELECT sql FROM db2.sqlite_master WHERE type='table' AND name='learnAlg'")
        c.execute(c.fetchone()[0])
        c.execute("INSERT INTO main.learnAlg SELECT * FROM db2.learnAlg")
        print("Table 'learnAlg' transferred")
        print("Backup data transferred.")

        # Save change to database
        conn.commit()

        # Close connection
        conn.close()
        print("Connection closed Kanji-story.db")

        try:
            # TODO fix restart required, below not working
            self.MediaScannerConnection.scanFile(sdpathfile)  # , "RFC6922"
        except:
            print("Not on Android")

        print("Finished backuping DB to SD-card.")
        self.poplbtext = "Backup completed :) Database saved at {}".format(sdpathfile)
        self.ids.popbackup.open()

    # Copy db to SD-card
    # def callback(self):
    #     print("\nBackuping DB to SD-card...")
    #
    #     sdpathfile = os.path.join(self.sdpath, 'Kanji-story_bak.db')
    #     print("Backup file: {}".format(sdpathfile))
    #     shutil.copyfile(os.path.join('data', 'db', 'Kanji-story.db'), sdpathfile)
    #     try:
    #         # TODO fix restart required, below not working
    #         self.MediaScannerConnection.scanFile(sdpathfile)  # , "RFC6922"
    #     except:
    #         print("Not on Android")
    #
    #     print("Finished backuping DB to SD-card.")
    #     self.poplbtext = "Backup completed :) Database saved at {}".format(sdpathfile)
    #     self.ids.popbackup.open()