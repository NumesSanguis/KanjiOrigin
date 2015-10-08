#!/usr/bin/kivy
# -*- coding: utf-8 -*-

import os
from kivy.app import App
from os.path import isfile
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
import string
import sqlite3
import shutil
from jnius import autoclass  # SDcard Android
#pyobjus #SDcard IOS


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


class RestoreSD(Screen):
    lbtext = "Restore a learning process backup from SD-card." \
             "The app looks in sdcard/KanjiOrigin/ for Kanji-story_bak.db ."
    bttext = "Restore learning process"
    poplbtext = "Are you sure you wish to overwrite the current learning process" \
                "by your backup on the SD card?\n\n" \
                "Kanji Origin will close after performing this action."

    # Get path to SD card
    try:
        Environment = autoclass('android.os.Environment')
        sdpath = Environment.get_running_app().getExternalStorageDirectory()
    except:
        sdpath = App.get_running_app().user_data_dir
    # TODO IOS

    print("Path SD: {}".format(sdpath))

    def callback(self):
        print("\nRestoring DB from SD-card...")

        sdpathfile = os.path.join(self.sdpath, 'Kanji-story_bak.db')
        print("Backup file: {}".format(sdpathfile))

        if os.path.isfile(sdpathfile):
            # Connect Database
            print("Trying to connect to DB Kanji-story.db")
            conn = sqlite3.connect(os.path.join("data", "db", "Kanji-story.db"))
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS current")
            c.execute("DROP TABLE IF EXISTS learnAlg")

            print("Attaching DB Kanji-story_bak.db")
            c.execute("ATTACH DATABASE ? AS db2", (sdpathfile,))

            print("Transferring backup data to current database...")

            #   If backup is pre v0.3, add framekanji column
            # Check number of columns to determine < or >= v0.3
            c.execute("PRAGMA db2.table_info(learnalg)")
            columnnames = c.fetchall()
            print(columnnames)
            print(len(columnnames))

            # Restore learning process < v0.3
            if len(columnnames) == 9:
                print("Pre v0.3 backup detected")

                # File with which Kanji framenumbers are added
                if isfile('RTK_v4-v6.txt'):
                    # Get framenums that chaned
                    with open('RTK_v4-v6.txt', 'r') as f:
                        change_numbers = f.readline()
                        change_numbers = change_numbers.split(',')
                        change_numbers = [int(i) for i in change_numbers]
                        print(change_numbers)

                    #   TABLE CURRENT
                    # Get create Table code, then insert data from backup
                    c.execute("SELECT sql FROM db2.sqlite_master WHERE type='table' AND name='current'")
                    table_command = c.fetchone()[0]
                    print("Table current:")
                    print(table_command)
                    # Add column framekanji
                    table_command = string.replace(table_command, ',', ', framekanji TEXT,')
                    print(table_command)
                    c.execute(table_command)
                    c.execute("INSERT INTO main.current SELECT framenum, NULL, nextKanji FROM db2.current")
                    print("Table 'current' transferred")

                    # Update framenum of table current
                    c.execute("SELECT framenum FROM current")
                    current = c.fetchone()[0]
                    extra = 0
                    i = -1
                    while i <= current:
                        if i in change_numbers:
                            extra += 1
                        i += 1

                    current += extra
                    print("Increase current framenum by: {}, to: {}".format(extra, current))

                    # Update current with new framenum and framekanji
                    c.execute("UPDATE current SET framenum=?, framekanji="
                              "(SELECT character FROM Kanji WHERE framenum=?)", (current,current))

                    #   TABLE LEARNALG
                    # Get table creation command from backup
                    c.execute("SELECT sql FROM db2.sqlite_master WHERE type='table' AND name='learnAlg'")
                    table_command = c.fetchone()[0]
                    #print(table_command)

                    # Add framekanji column
                    table_command = string.replace(table_command, ' PRIMARY KEY', ', framekanji TEXT PRIMARY KEY')
                    print("Table learnAlg:")
                    print(table_command)

                    # Add new table to DB
                    c.execute(table_command)

                    # Transfer backup data to new table
                    c.execute("INSERT INTO main.learnAlg SELECT framenum, NULL, "
                              "decay, timeseen, timelearn, tlsoft, xseen, active, prevcorrect, prevtime "
                              "FROM db2.learnAlg")
                    # Test Kanji
                    c.execute("UPDATE learnAlg SET framekanji=0 WHERE framenum=0")

                    # Change framenum from RTK v4 to v6
                    # c.execute("SELECT rowid, framenum FROM learnAlg")
                    # db_framenum = c.fetchall()
                    # print(db_framenum)
                    #
                    # # How much v6 framenum differentiates from v4
                    # change_fn = 0
                    # for e, f in enumerate(db_framenum):
                    #     e += 1
                    #     db_framenum_new = f[1]
                    #     if db_framenum_new in change_numbers:
                    #         change_fn += 1
                    #     db_framenum_new = db_framenum_new + change_fn
                    #
                    #     c.execute("UPDATE learnAlg SET framenum=? WHERE rowid=?",
                    #               (db_framenum_new, e))
                    #
                    # print("")
                    # print(db_framenum_new)
                    # c.executemany("UPDATE learnAlg SET framenum=? WHERE rowid=?",
                    #               (db_framenum_new[1], db_framenum_new[0]))

                    # Max rowid
                    c.execute("SELECT MAX(rowid) FROM learnAlg")
                    max = c.fetchone()[0]

                    change = 0
                    print("rowid - 1:")
                    for fn in range(max):
                        if fn+change in change_numbers:
                            change += 1
                            # c.execute("UPDATE learnAlg SET rowid=? WHERE rowid=?", (fn+1, fn+2))
                            # c.execute("INSERT INTO learnAlg framenum=?, framekanji=NULL, decay=NULL, "
                            #           "timeseen=NULL, timelearn=NULL")
                        print(fn)
                        # Increase framenum
                        c.execute("UPDATE learnAlg SET framenum=? WHERE rowid=?", (fn+change, fn+1))


                    # Give framekanji to table learnAlg
                    c.execute("UPDATE learnAlg SET framekanji=(SELECT character FROM Kanji WHERE "
                                  "framenum = learnAlg.framenum) WHERE framenum != 0")

                    # print("fn in range(max)")
                    # for fn in range(max):
                    #     fn += 1
                    #     # !! Add framekanji !!
                    #     c.execute("UPDATE learnAlg SET framekanji=(SELECT character FROM Kanji WHERE "
                    #               "framenum = learnAlg.framenum) WHERE framenum = ?", (fn,))
                    #     print(fn)

                    #c.execute("SELECT framenum, framekanji FROM learnAlg")
                    #print(c.fetchall())

                    # c.execute("SELECT rowid, framenum FROM learnAlg")
                    # db_framenum = c.fetchall()
                    # print(db_framenum)
                    #
                    # db_framenum_new = []
                    # # How much v6 framenum differentiates from v4
                    # change_fn = 0
                    # for e, f in enumerate(db_framenum):
                    #     e += 1
                    #     t = f[1]
                    #     if t in change_numbers:
                    #         change_fn += 1
                    #     t = t + change_fn
                    #     db_framenum_new.append((t, e))
                    #
                    # print("")
                    # print(db_framenum_new)
                    # c.executemany("UPDATE learnAlg SET framenum=? WHERE rowid=?",
                    #               (db_framenum_new))


                    # !! Add framekanji !!
                    #c.execute("UPDATE learnAlg SET framekanji=(SELECT character FROM Kanji WHERE)")

                else:
                    print("RTK v4 to v6 txt not found")

            # Restore learning process >= v0.3
            else:
                # Get create Table code, then insert data from backup
                c.execute("SELECT sql FROM db2.sqlite_master WHERE type='table' AND name='current'")
                c.execute(c.fetchone()[0])
                c.execute("INSERT INTO main.current SELECT * FROM db2.current")
                print("Table 'current' transferred")

                # Get table creation command from backup
                c.execute("SELECT sql FROM db2.sqlite_master WHERE type='table' AND name='learnAlg'")
                # Add new table to DB
                c.execute(c.fetchone()[0])

                # Transfer backup data to new table
                c.execute("INSERT INTO main.learnAlg SELECT * FROM db2.learnAlg")
                print("Table 'learnAlg' transferred")
                print("Backup data transferred.")

            # Save change to database
            conn.commit()

            # Close connection
            conn.close()
            print("Connection closed Kanji-story.db")
            print("Closing App")
            App.get_running_app().stop()

        else:
            print("No database backup found")

        print("Finished restoring DB from SD-card.")


class koohiiCSV(Screen):
    lbtext = "Not working yet. In the future you can here import your own stories in collabaration with " \
             "kanji.koohii.com/"
    bttext = "Not working yet"

    def callback(self):
        print("\nImporting koohii .csv...")



        print("Finished importing koohii .csv.")


class ResetKO(Screen):
    lbtext = "Pressing 'RESET KanjiOrigin' below will reset the database which keeps track of your learning progress. " \
             "By doing so, KanjiOrigin will be reset to the state as when this app was first installed. " \
             "This action caries the risk of losing all your data, so ONLY DO THIS IF YOU ARE SURE. " \
             "It's RECOMMENDED to make a backup before proceeding. " \
             "This can be done by using 'Backup to SD-card info' option in the previous menu.\n\n" \
             "Pressing the RESET button will automatically make a local backup, but it's NOT RECOMMENDED " \
             "to rely on this backup for backup purposes. ONLY use the 'UNDO RESET' button " \
             "if the 'Restore from SD-card' option in the previous menu does not work or you forgot to make " \
             "a backup to your (virtual) SD-card."
    rstext = "RESET KanjiOrigin"
    urstext = "UNDO RESET"
    poplbtext = "Are you sure you want to reset Kanji Origin to default AND did you make a backup to SD card?" \
                "\n\nKanji Origin will be closed after reset is completed."
    popurstext = "Only continue if you want to restore learning process AND" \
                 "you didn't make a backup to SD card\n\n" \
                 "Kanji Origin will close after undo reset completion."
    popfailtext = "Restoring reset database backup failed, database not found.\n\n" \
                  "Most likely this app has not been reset before."

    def ResetApp(self):
        print("\nMaking local backup of current learning process...")

        if os.path.isfile(os.path.join('data', 'db', 'Kanji-story.db')):
            shutil.copyfile(os.path.join('data', 'db', 'Kanji-story.db'), os.path.join('data', 'db', 'Kanji-story_bak.db'))
            print("Backup made")
        else:
            print("Backup failed")

        print("Local backup learning process completed")
        print("Resetting Kanji Origin DB...")

        shutil.copyfile(os.path.join('data', 'db', 'Kanji-story_org.db'), os.path.join('data', 'db', 'Kanji-story.db'))

        print("Finished resetting Kanji Origin DB.")
        print("Closing App")
        App.get_running_app().stop()

    def UndoReset(self):
        print("\nRestoring local backup...")

        if os.path.isfile(os.path.join('data', 'db', 'Kanji-story_bak.db')):
            # Connect Database
            print("Trying to connect to DB Kanji-story.db")
            conn = sqlite3.connect(os.path.join("data", "db", "Kanji-story.db"))
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS current")
            c.execute("DROP TABLE IF EXISTS learnAlg")

            print("Attaching DB Kanji-story_bak.db")
            c.execute("ATTACH DATABASE ? AS db2", (os.path.join('data', 'db', 'Kanji-story_bak.db'),))

            print("Transferring backup data to current database...")

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
            print("Closing App")
            App.get_running_app().stop()

        else:
            print("No database backup found")
            self.ids.popundo.dismiss()
            self.ids.popfail.open()

        print("Restoring local backup completed.")


if __name__ == '__main__':
    print("This code needs to be run with KanjiOrigin")
