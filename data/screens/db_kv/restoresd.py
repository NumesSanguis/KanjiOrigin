#!/usr/bin/kivy
# -*- coding: utf-8 -*-

import os
from kivy.app import App
from os.path import isfile
from kivy.uix.screenmanager import Screen
import string
import sqlite3


class RestoreSD(Screen):
    lbtext = "Restore a learning process backup from SD-card." \
             "The app looks in sdcard/KanjiOrigin/ for Kanji-story_bak.db."
    bttext = "Restore learning process"
    poplbtext = "Are you sure you wish to overwrite the current learning process " \
                "by your backup on the SD card?\n\n" \
                "Kanji Origin will close after performing this action."

    # Get path to SD card
    try:
        # from kivy import platform
        from jnius import autoclass  # SDcard Android
        #pyobjus #SDcard IOS
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