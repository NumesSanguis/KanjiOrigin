# !! This is not the learning algorithm used by Kanji Origin !!
# !! This is for Tutorial purposes only !!
# !! The reason for this is that I do not wish that someone takes my hard work,
# makes it fancy and earn money from it, while I try to give it for free to everyone !!
# !! Donations are welcome though :) !!

import os
from time import time
import sqlite3


# Algorithm for what Kanji to show and update user's current knowledge
class LearnAlg():
    # 0 = test, 1 = KanjiOrigin
    def __init__(self, KO=1):
        if KO != 0:
            self.db_path = os.path.join("data", "db", "Kanji-story.db") # path from main.py
        else:
            self.db_path = os.path.join("..", "db", "Kanji-story.db") # path from this file
        print("\nLearnAlg initialized")

        # No new Kanji to introduce
        self.finished = 0

        # Connect database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        print("Connected DB with learnAlg")

        # Add table learnAlg if not existing yet
        c.execute("CREATE TABLE IF NOT EXISTS learnAlg (framenum INTEGER PRIMARY KEY, decay REAL, timeseen REAL,"
                  "timelearn REAL, tlsoft REAL, xseen INTEGER, active INTEGER, prevcorrect INTEGER, prevtime REAL)")
        # Love, for test purposes
        c.execute("INSERT OR IGNORE INTO learnAlg VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (0, 0.00000005, time()-1, None, None, 0, 1, 0, None))

        print("TABLE learnAlg created")

        # Save change to database
        conn.commit()

        # Test: print active
        c.execute("SELECT framenum FROM learnAlg WHERE active = 1")
        print("Current active: {}".format(c.fetchone()[0]))

        # Get maximum Kanji
        c.execute("SELECT MAX(framenum) FROM Kanji")
        self.kanji_total = c.fetchone()[0]
        print("self.kanji_total: {} , type: {}".format(self.kanji_total, type(self.kanji_total)))
        print("Total Kanji's in DB: {}".format(self.kanji_total))

        # Close connection
        conn.close()
        print("DB with learnAlg connection closed")

    # Add a new Kanji for learning to DB
    def insertnewKanji(self):
        # Connect database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        print("Connected DB with learnAlg")

        # Get framenum latest Kanji
        c.execute("SELECT MAX(framenum) FROM learnAlg")
        frame_num = c.fetchone()[0]
        print("Max framenum: {}".format(frame_num))

        #Don't inser new Kanji if all introduced
        if frame_num >= self.kanji_total:
            self.finished = 1

        else:
            # No entry in table yet
            if frame_num == None:
                frame_num = 0

            # New Kanji framenum
            frame_num += 1

            #   Initialize new Kanji
            c.execute("INSERT INTO learnAlg VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (frame_num, 0, time(), None, None, 0, 1, 0, None))

            # Save change to database
            conn.commit()

        # Close connection
        conn.close()
        print("DB with learnAlg connection closed")



    def retrieveKanji(self):
        print("\n...Retrieving next Kanji's DB...")

        # Connect database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = lambda cursor, row: row[0]
        c = conn.cursor()
        print("Connected DB with learnAlg")

        # Select next Kanji
        if self.finished == 0:
            # set previous Kanji active = 0
            c.execute("UPDATE learnAlg SET active = 0 WHERE active = 1")
            conn.commit()

            print("Introducing new Kanji")
            self.insertnewKanji()

            c.execute("SELECT framenum FROM learnAlg WHERE active is 1")
            result = c.fetchall()
            print("New Kanji retrieved: {}".format(result))
        else:
            result = []

        # Close connection
        conn.close()
        print("DB with learnAlg connection closed")

        # Return list(result)
        print("List framenums Kanji: {}".format(result))
        return(result)


    def answerKanji(self, framenum, correct):
        print("Doesn't do anything in this function")


    def countlearned(self):
        print("\nUpdate answerbar with status Kanji learned")

        # Connect database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = lambda cursor, row: row[0]
        c = conn.cursor()
        print("Connected DB with learnAlg")

        # Count Kanji learn now
        # Kanji left
        c.execute("SELECT MAX(framenum) FROM learnAlg")
        kanji_intro = c.fetchone()
        count_left = self.kanji_total - kanji_intro
        print("Kanji left: {}".format(count_left))

        return([-1, -1, count_left])


class TestAlg():
    def __init__(self):
        self.testy = LearnAlg(0)
        self.testy.insertnewKanji()
        print("List framenums Kanji: {}".format(self.testy.retrieveKanji()))
        self.testy.answerKanji(1, False)


if __name__ == '__main__':
    print("This code should be run with KanjiOrigin")
    TestAlg()
