#!/usr/bin/kivy
# -*- coding: utf-8 -*-

import os
from kivy.app import App
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

import re
from collections import deque
import sqlite3
#import numpy as np # Needed for pyxdameraulevenshtein
#from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance_withNPArray # Add module TODO
from difflib import SequenceMatcher

import learnkanji_k_alg

#from __future__ import unicode_literals  # TODO test if works

#font_kanji = os.path.join('data', 'fonts', 'TakaoPMincho.ttf')


from kivy.core.text import LabelBase
KIVY_FONTS = [
    {
        "name": "TakaoPMincho",
        "fn_regular": os.path.join('data', 'fonts', 'TakaoPMincho_transformed_full.ttf'),
        "fn_bold": os.path.join('data', 'fonts', 'TakaoPMincho_transformed_full_bold2.ttf')
    }
]

for font in KIVY_FONTS:
    LabelBase.register(**font)


class SKanjiToggleButton(ToggleButton):
    lfunc = ObjectProperty(None)

    def on_lfunc(self, obj, lfunc):
        if lfunc:
            self.font_name = lfunc.font_kanji
            #self.text = self.text


class AnswerTextInput(TextInput):
    #focus = BooleanProperty(False)
    # redefine insert_text
    #def insert_text(self, substring, from_undo=False):
    #    return super(AnswerTextInput, self).insert_text(substring, from_undo=from_undo)

    def resettext(self, next_kanji):
        if next_kanji == True:
            self.text = ""
            self.focus = True

    # def _on_focus(self, instance, value, *largs):
    #     super(AnswerTextInput, self)._on_focus(instance, value, *largs)
    #     print("TextInput is focused")
    #     keyb_height = Window.keyboard_height
    #     #print(App.get_running_app().root.ids.story_box.height)
    #     #App.get_running_app().root.ids.story_box.height = keyb_height


# Handles everything related to shown Kanji
class MasterKanji(EventDispatcher):
    cur_framenum = NumericProperty()
    cur_framekanji = StringProperty()
    current = StringProperty()
    cur_answer = ListProperty()
    story = StringProperty()
    story_show = BooleanProperty(False)
    fix_answer = StringProperty("")

    def __init__(self, **kwargs):
        super(MasterKanji, self).__init__(**kwargs)

        self.db_name = os.path.join("data", "db", "Kanji-story.db")  # path from main.py
        self.alg = learnkanji_k_alg.LearnAlg()
        self.alg_count = learnkanji_k_alg.LearnCount()
        self.cur_framekanji = self.dbcurrent("framekanji")
        #print("Init with current framekanji: {}".format(self.cur_framekanji))
        self.cur_framenum, self.cur_answer, self.story = self.dbkanji_info()
        print(self.cur_answer)
        if self.cur_framekanji == '-1' or self.cur_framekanji == '0':
            print("-1 or 0: {}".format(self.cur_framekanji))
            self.cur_framekanji = self.dbspecial(self.cur_framekanji)
        self.upcoming = deque()  # deque(self.alg.retrieveKanji()) gives error
        self.story_hidden = "The answer is hidden, please provide an answer in the text-bar above and press 'check'." \
                            "\nYou cannot advance to the next Kanji until you have typed the right response."
        self.radicals_list = []
        self.radicalDict()
        self.sKanji_list = []
        self.sKanjiDict()
        print("--- INIT MasterKanji COMPLETE ---\n")

    def dbspecial(self, item):
        print("Trying to connect to DB table Kanji (special)...")
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        print("DB connected with special: {}".format(item))

        c.execute("SELECT character FROM Kanji WHERE framenum = ?", (item,))
        result = c.fetchone()
        #print(result[0])
        resulty = result[0]

        # To prevent UnicodeEncodeError: 'ascii'
        if item == '0':
            resulty = resulty.encode('utf-8')

        # Close connection
        conn.close()
        print("DB current connection closed")

        return(resulty)

    def dbcurrent(self, col):
        # Connect Database
        print("Trying to connect to DB table current...")
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        print("DB connected with column: {}".format(col))

        c.execute("SELECT {} FROM current".format(col))
        result = c.fetchone()
        print(result)
        resulty = result[0]

        # To prevent UnicodeEncodeError: 'ascii'
        if col == "framekanji":
            resulty = resulty.encode('utf-8')

        #print(resulty)

        # Close connection
        conn.close()
        print("DB current connection closed")

        return(resulty)

    def dbkanji_info(self, item=''):
        # If no framekanji is given, use current framekanji
        if item == '':
            item = self.cur_framekanji
        item = item.decode('utf-8')

        # Connect Database
        print("Trying to connect to DB table Kanji (info)...")
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        #print("DB connected with item: {}".format(item.encode('utf-8')))
        if item == '-1' or item == '0':
            c.execute("SELECT framenum, meanings, story FROM Kanji WHERE framenum = ?", (item,))
        else:
            c.execute("SELECT framenum, meanings, story FROM Kanji WHERE character = ?", (item,))
        result = c.fetchall()
        returny = list(result[0])
        returny[1] = result[0][1].split('/')
        print(returny)

        # Replace | for / in meanings
        returny[1] = [x.replace('|', '/') for x in returny[1]]

        # Close connection
        conn.close()
        print("DB current connection closed")

        return(returny)

    def dbupdate(self, nxt_cur):
        # Connect Database
        print("Trying to connect to DB table Kanji (update)...")
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        print("DB connected with:")
        #print(self.cur_framenum, self.cur_framekanji.decode('utf-8'), nxt_cur)

        # Finish and tutorial
        if self.cur_framenum == -1 or self.cur_framenum == 0:
            update_framekanji = str(self.cur_framenum)
        else:
            update_framekanji = self.cur_framekanji

        c.execute("UPDATE current SET framenum = ?, framekanji = ?, nextKanji = ?",
                  (self.cur_framenum, update_framekanji.decode('utf-8'), nxt_cur))

        # Close connection
        conn.commit()
        conn.close()
        print("DB current connection closed")

    # Handles database
    # def conndb(self, tabl, action, item, req=""):
    #     # tabl = Table, action = SELECT/UPDATE, item = what should be selected/*
    #
    #     # Connect Database
    #     print("Trying to connect to DB")
    #     conn = sqlite3.connect(self.db_name)
    #     c = conn.cursor()
    #     print("DB connected with Table: {}, Action: {} and item: {}".format(tabl, action, item))
    #
    #     if action == "SELECT":
    #         c.execute("{} {} FROM {}{}".format(action, item, tabl, req))
    #         result = c.fetchall()
    #         print(result)
    #         if item != "nextKanji" and item != "framekanji":
    #             print("I have no nextKanji or framekanji, because item = {}".format(item))
    #             if tabl == "Kanji":
    #                 returny = result[0]
    #                 #c.execute("UPDATE current SET framenum = {}".format(req[-1])) # Uncomment when should not start love
    #             else:
    #                 c.execute("SELECT character, meanings, story FROM KANJI WHERE character={}".format(result[0][0]))
    #                 returny = c.fetchone()
    #             returny = list(returny)
    #             answers = returny[1].split('/')
    #             # Makes the answers lower case
    #             returny[1] = answers  #[x.lower() for x in answers]
    #             returny[0] = returny[0].encode('utf-8')  # TODO fix this for Kanji Koohii (maybe fixed)
    #         else:
    #             print("I do have {}".format(item))
    #             returny = result[0][0]
    #             print(returny)
    #
    #     else:
    #         c.execute("{} {} SET {}".format(action, tabl, req))
    #
    #         # Save change to database
    #         conn.commit()
    #
    #     # Close connection
    #     conn.close()
    #     print("DB connection closed")
    #
    #     if action == "SELECT":
    #        return returny
    #        #return #list

        # Creates list for radicals of current Kanji
    def radicalDict(self):
        # Connect Database
        print("\nTrying to connect to DB with table Radical and RadicalMeaning")
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()

        c.execute("SELECT radicals FROM Radical WHERE framekanji = ?", (self.cur_framekanji.decode('utf-8'),))
        result = c.fetchone()
        if result:
            print(result)
            # Split radical
            r_list = result[0].split('/')
            self.radicals_list = [x.encode('utf-8') for x in r_list]

            #radical_num = result[0].split('/')
            #print(radical_num)

            # Get refered radicals
            # for rnum in radical_num:
            #     c.execute("SELECT radical FROM RadicalMeaning WHERE number = ?", (rnum,))
            #     result = c.fetchone()
            #     print(result)
            #     self.radicals_list.append(result[0])  # .encode('utf-8')

            print(self.radicals_list)
        else:
            print("No radicals")
            self.radicals_list = []

    # Creates list for small Kanji of current Kanji
    def sKanjiDict(self):
        # Connect Database
        print("\nTrying to connect to DB with table sKanji")
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()

        c.execute("SELECT smallKanji FROM sKanji WHERE framekanji = ?", (self.cur_framekanji.decode('utf-8'),))
        result = c.fetchone()
        if result:
            print(result)
            # Split number reference to Kanji to a list
            s_list = result[0].split('/')
            self.sKanji_list = [x.encode('utf-8') for x in s_list]
            print(self.sKanji_list)

            # Get refered Kanji's
            # for snum in sKanji_num:
            #     # Get highest Kanji shown to not have small Kanji higher than so far shown.
            #     c.execute("SELECT MAX(framenum) FROM learnAlg")
            #     max = c.fetchone()
            #     print("Max framenum seen: {}".format(max))
            #
            #     c.execute("SELECT character FROM Kanji WHERE framenum = ? AND framenum <= ?", (snum, max[0]))
            #     result = c.fetchone()
            #     print(result)
            #     if result:
            #         self.sKanji_list.append(result[0].encode('utf-8'))
            #
            # print(self.sKanji_list)
        else:
            print("No small Kanji")
            self.sKanji_list = []

    # Next Kanji
    def nextkanji(self):

        # Get next list of to be learned Kanji
        if not self.upcoming:
            self.upcoming = deque(self.alg.retrieveKanji())

        # All Kanji's are learned
        if not self.upcoming:
            self.cur_framekanji = '-1'
            self.cur_framenum, self.cur_answer, self.story = self.dbkanji_info(self.cur_framekanji)
            self.cur_framekanji = self.dbspecial(self.cur_framekanji)
            #self.conndb("Kanji", "SELECT", "character, meanings, story", " WHERE framenum = -1")

        # Get next Kanji character, answer, story and also update current table
        else:
            # Get new Kanji and answer
            self.cur_framekanji = self.upcoming.popleft()
            #print(self.cur_framekanji)
            self.cur_framenum, self.cur_answer, self.story = self.dbkanji_info()
            #self.conndb("Kanji", "SELECT", "character, meanings, story", " WHERE framenum = {}".format(self.cur_framenum))

        # Update status learning
        print("Updating actionbar_status")
        App.get_running_app().actionbar_status = self.alg_count.countlearned()

        # Update sKanji_dict for sKanji buttons
        self.radicalDict()
        self.sKanjiDict()

        # App.get_running_app().root.ids.lbl1.text = "Now: {}".format(status[0])
        # App.get_running_app().root.ids.lbl2.text = "Forgot: {}".format(status[1])
        # App.get_running_app().root.ids.lbl3.text = "Left: {}".format(status[2])

    # Update current Kanji table
    def updateCurrent(self, nxt, correct=-1):
        # nxt_cur: 0: no answer, 1: correct answer, 2: wrong answer
        print("Updating current with nxt: {} and correct: {}".format(nxt, correct))

        if nxt:
            nxt_cur = 1
        else:
            if correct == 0:
                nxt_cur = 2
            else:
                nxt_cur = 0

        self.dbupdate(nxt_cur)

    # Update database with current knowledge of answered Kanji
    def updateKanji(self, correct):
        # Don't update when showing finished screen
        if self.cur_framenum != -1:
            # Change test
            if self.cur_framenum == 0:
                updatek = '0'
            else:
                updatek = self.cur_framekanji
            self.alg.answerKanji(updatek, correct)

    def story_bold(self):
        print("Making answers bold...")
        # Don't update GUI all the time
        story = self.story

        for x in self.cur_answer:
            print("Search with: {}".format(x))

            # Find all words with answer x in it
            search = [(m.group(),m.start(),m.end()) for m in re.finditer(x, story, flags=re.IGNORECASE)]
            print(search)

            # Start from end of story to not screw over indexes when adding bold [b] [/b]
            i = len(search)-1
            while i >= 0:
                s = search[i][1]
                e = search[i][2]
                #print("Start: {}\tEnd: {}".format(s, e))
                #print("Start: {}\tEnd: {}".format(story[s], story[e]))
                story = story[:s] +"[b]"+ story[s:e] +"[/b]"+ story[e:]

                i -= 1

        self.story = story
        #print(self.story)

    #Formats the answer of the user
    def textFormat(self, answer):
        #Set answer to lower case and clean the answer of strange symbols
        answer = answer.lower()
        pattern = '[a-z0-9 .-]'
        answer = ''.join(re.findall(pattern, answer))
        return answer

    # Check if typed answer is correct by using dameau levenshtein distance
    def check(self, answer):
        print("Answers: {} , given: {}".format(self.cur_answer, answer))

        # Convert list to numpy
        #cur_answer_np = np.asarray(self.cur_answer, dtype='S')
        # Calculate dameau levenshtein distance between given answer and correct answers
        #dam_lev = normalized_damerau_levenshtein_distance_withNPArray(answer, cur_answer_np)
        #print("dam-lev distance: {}".format(dam_lev))
        # Get lowest (and therefore least difference) score
        #dam_lev_ind = np.argmin(dam_lev)

        # If distance is small enough TODO module support
        #if dam_lev[dam_lev_ind] < 0.34:
        #    self.fix_answer = self.cur_answer[dam_lev_ind]
        #    return 1
        #else:
        #    return 0

        # SequenceMatcher(None, a, b).ratio()
        sm_list = []
        print(self.cur_answer)
        cur_ans_lower = [self.textFormat(x) for x in self.cur_answer]
        for a in cur_ans_lower:
            sm_list.append(SequenceMatcher(None, answer, a).ratio())
        print(sm_list)
        sm_ind = sm_list.index(max(sm_list))

        # If distance is small enough (higher is closer)
        if sm_list[sm_ind] > 0.7:
            self.fix_answer = self.cur_answer[sm_ind]
            print("Fix: {}".format(self.cur_answer[sm_ind]))
            return 1
        else:
            return 0

        #if answer in self.cur_answer:
        #    return 1
        #else:
        #    return 0


class LayoutFunctioning(BoxLayout):

    # 280 dp, because otherwise maybe keyboard over inputfield
    keyb_height = NumericProperty(dp(260))  #280  #254
    print("Keyboard height: {}".format(keyb_height))

    font_kanji = "TakaoPMincho"  # os.path.join('data', 'fonts', 'TakaoPMincho.ttf')  # TakaoPMincho.ttf
    #Kanji_s = ["爪", "冖", "心", "夂"]

    next_kanji = BooleanProperty(False)
    answered = BooleanProperty(False)
    master_kanji = MasterKanji()

    txt_field_focus_i = BooleanProperty(True)
    if master_kanji.cur_framenum == 0:
        txt_field_focus_i = BooleanProperty(False)

    # Send button disabled with no text
    send_disabled = BooleanProperty(True)
    # Enable send button timer in sec
    send_disabled_t = 3

    # Link button to website
    ww_link = StringProperty()

    # TODO Enter on keyboard
    #Window.bind(on_key_enter = btnPressed(answer))

    def __init__(self, **kwargs):
        super(LayoutFunctioning, self).__init__(**kwargs)

        # Enable send_btn after some seconds
        self.cb_disablesend = lambda dt: self.disablesend(False)
        Clock.schedule_once(self.cb_disablesend, self.send_disabled_t)

        # When previously saw finish screen
        if self.master_kanji.cur_framenum == -1:
            self.master_kanji.nextkanji()
            self.reinitscreen(0)
        else:
            self.reinitscreen(self.master_kanji.dbcurrent("nextKanji"))

        # First time opening app show explanation story
        if self.master_kanji.cur_framenum == 0:
            print("First time app")
            self.master_kanji.story_show = True

        # Link button to website
        print("!!!   DEBUG UTF-8   !!!")
        #print(self.master_kanji.cur_framekanji)
        print(type(self.master_kanji.cur_framekanji))
        self.ww_link = "http://kanji.koohii.com/study/kanji/{}".format(self.master_kanji.cur_framekanji)  # "TODO")

        # Keyboard height
        #Clock.schedule_once(lambda dt: self.storykeybheight())

        print("Keyboard binding")
        Window.bind(on_keyboard=self.storykeybheight)

        print("--- INIT LayoutFunctioning COMPLETED ---\n")

    def reinitscreen(self, nxt_cur):
        # No answer given yet
        if nxt_cur == 0:
            print("Reinit: no answer")
            self.next_kanji = False
            self.answered = 0
            self.master_kanji.story_show = False

        # Correct answer
        elif nxt_cur == 1:
            print("Reinit: correct")
            self.next_kanji = True
            self.answered = 1
            self.master_kanji.story_show = True
            Clock.unschedule(self.cb_disablesend)
            self.disablesend(False)

        # Wrong answer
        else:
            print("Reinit: wrong")
            self.next_kanji = False
            self.answered = 1
            self.master_kanji.story_show = True

        # Answers bold in self.story
        #self.master_kanji.story_bold()

        # sKanji buttons (Clock.schedule to call this function after .kv initialisation)
        Clock.schedule_once(lambda dt: self.changeSKanji())
        #self.changeSKanji()

    def disablesend(self, dis):
        print("Disable send button: {}".format(dis))
        self.send_disabled = dis
        Clock.unschedule(self.cb_disablesend)

    # Change the BoxLayout height with the story inside to match user's keyboard height
    def storykeybheight(self, window, keycode1, keycode2, text, modifiers):
        keyb_height_change = Window.keyboard_height
        print("storykeybheight size: {}, current: {}".format(keyb_height_change, self.keyb_height))

        # Keyboard open
        if keyb_height_change > dp(50):
            # remove padding + vague value
            keyb_height_change -= dp(33)
            if self.keyb_height != keyb_height_change:
                print("Keyb before: {}".format(self.keyb_height))
                self.keyb_height = keyb_height_change
                print("Keyb after: {}".format(self.keyb_height))

            # TODO close keyboard when esc or back button
            #if keycode1 in [27, 1001]:
            #    print("close keyboard")
            #    self.txt_field_focus_i = BooleanProperty(False)

    # def storykeybheight(self, *args):
    #     print("storykeybheight")
    #     print("keyb_height before: {}".format(self.keyb_height))
    #     keyb_height_change = Window.keyboard_height
    #     print("Window.keyboard_height: {}".format(keyb_height_change))
    #
    #     # TODO Window.keyboard_height returns 50 ???
    #     if keyb_height_change <= dp(50):
    #         #keyb_height_change = dp(287)
    #         print("Keyb fix: {}".format(keyb_height_change))
    #         #Clock.schedule_once(lambda dt: self.storykeybheight())  # call this function again if too fast
    #     else:
    #         # remove padding
    #         keyb_height_change -= dp(35)
    #         print("Keyb - padding: {}".format(keyb_height_change))
    #         self.keyb_height = keyb_height_change

        # remove padding
        #keyb_height_change -= dp(35)
        #print("Keyb - padding: {}".format(keyb_height_change))

        #self.keyb_height = keyb_height_change

    # Copy current Kanji to clipboard
    def cpClipboard(self):
        print("Copy current Kanji to clipboard")
        Clipboard.copy("{}".format(self.master_kanji.cur_framekanji))  # TODO fix UTF8
        print(Clipboard.get_types())
        #print(Clipboard.paste())


    # Flash the TextInput red when wrong answer is given
    def flashred(self):
        print("Flashing textinput red")
        self.ids.txt_field.background_color = (1, 0.4, 0.4, 1)
        Animation(background_color=(1, 0.75, 0.75, 1), duration=.5).start(self.ids.txt_field)


    # Changes the shown story to the selected radical
    def changeStory(self, skanji, radical):
        print("Doing changeStory")
        #print("Change story to {} and radical: {}".format(skanji, radical))  # Doesn't work on Android
        #print("Change story to "+skanji+"and radical: {}".format(radical))

        # Connect database
        conn = sqlite3.connect(self.master_kanji.db_name)
        #conn.row_factory = lambda cursor, row: row[0]
        c = conn.cursor()

        # Radical or not
        if radical:
            print("story change radical")
            c.execute("SELECT Rjapanese, alt, strokes, meanings FROM RadicalMeaning WHERE radical = ?"
                      , (skanji.decode('utf-8'),))
            story = c.fetchone()
            print(story)
            if story[1] != '':
                self.master_kanji.story = skanji.decode('utf-8')+"Radical: "+story[0]+"\nAlt: "+story[1]\
                                          +"\nStrokes: "+str(story[2])+"\n\nMeanings: [b]"+story[3]+"[/b]"
            else:
                self.master_kanji.story = skanji.decode('utf-8')+"\nRadical: "+story[0]+\
                                          "\nStrokes: "+str(story[2])+"\n\nMeanings: [b]"+story[3]+"[/b]"

        else:
            print("story change skanji")
            #print(skanji.decode('utf-8'))
            if self.master_kanji.cur_framenum == -1 or self.master_kanji.cur_framenum ==  0:
                c.execute("SELECT meanings, story FROM Kanji WHERE framenum = ?", (self.master_kanji.cur_framenum,))
            else:
                c.execute("SELECT meanings, story FROM Kanji WHERE character = ?", (skanji.decode('utf-8'),))
            story = c.fetchone()
            print(story)
            if skanji != self.master_kanji.cur_framekanji:
                self.master_kanji.story = skanji.decode('utf-8')+"\n[b]"+story[0]+"[/b]\n\n"+story[1]
            else:
                self.master_kanji.story = story[1]
                # Try making answers in self.story bold
                try:
                    self.master_kanji.story_bold()
                except:
                    print("Bolding story failed 0.o")
                    self.master_kanji.story += "\n\n[b]Bolding[/b] went wrong!!! Please report Kanji + framenumber " \
                                               "(top-left) to App developer. Screenshot is appreciated :)"

            print("Story changed")


    def addsKanji(self, stext, r):
        print("addsKanji")
        #print(App.get_running_app().root.ids.learn_kanji.text)
        skanj = SKanjiToggleButton(lfunc=self, text=stext, radical=r)  # , lfunc = self.ids.lfunc
        self.ids.sKanjibox.add_widget(skanj)
        #self.ids.foo.text = "T"

    def delsKanji(self):
        print("delsKanji")
        #print(getattr(self.ids, 'togglemain').text)

        # TODO set togglemain to down

        # children = self.children[:]
        #
        # while children:
        #     child = children.pop()
        #
        #     print(child)

        # Remove all buttons except with main Kanji
        for child in [child for child in self.ids.sKanjibox.children if child.text != self.master_kanji.cur_framekanji]:
            print("Remove: {}".format(child))
            self.ids.sKanjibox.remove_widget(child)

        # Set main Kanji button state to down
        for child in self.ids.sKanjibox.children:
            child.state = 'down'

    def changeSKanji(self):
        # Delete current sKanji buttons again to remove radicals same as Kanji
        self.delsKanji()

        # Add new sKanji buttons
        for s in self.master_kanji.radicals_list:
            self.addsKanji(s, True)

        # Add new sKanji buttons
        for s in self.master_kanji.sKanji_list:
            self.addsKanji(s, False)

        # Set radicals_list and sKanji_list to empty after adding buttons
        self.master_kanji.radicals_list = []
        self.master_kanji.sKanji_list = []


    # Function when the check/next button is pressed
    def btnPressed(self, answer):
        print("\n- - - - -")
        Clock.unschedule(self.cb_disablesend)

        #Only do something when user actually typed or answer has been correct
        #if self.send_disabled == False:  # len(answer) > 0 or self.next_kanji == True:
            #self.ids.story_box.height = Window.keyboard_height - dp(8)
            #print("New keyb height: {}".format(self.ids.story_box.height))

        # TODO bind()
        # Get next Kanji after answered correctly
        if self.next_kanji == True:
            print("Next Kanji...")
            # Delete current sKanji buttons
            self.delsKanji()

            # Next Kanji
            self.master_kanji.nextkanji()

            # Next Story although hidden
            #self.ids.story.text = self.master_kanji.story

            #re-init
            print("Reinit button: no answer")
            self.next_kanji = False
            print(self.master_kanji.cur_answer)
            self.master_kanji.story_show = False
            self.answered = 0

            # Disable and then Enable send_btn after some seconds
            self.send_disabled = True
            Clock.schedule_once(self.cb_disablesend, self.send_disabled_t)

            # update current in DB
            self.master_kanji.updateCurrent(self.next_kanji)

            # Change sKanji buttons
            self.changeSKanji()

            # Change story button
            self.ww_link = "http://kanji.koohii.com/study/kanji/{}".format(self.master_kanji.cur_framekanji)

            # Answers bold in self.story
            self.master_kanji.story_bold()

        # Check given answer
        else:
            print("Checking answer...")
            answer = self.master_kanji.textFormat(answer)

            # Correct answer
            if self.master_kanji.check(answer) or self.master_kanji.cur_framenum == -1:
                print("Correct answer")
                self.next_kanji = True
                # TODO Change button color
                # Only update when first time answering
                if self.answered == 0:
                    self.master_kanji.updateKanji(True)
                    self.master_kanji.updateCurrent(self.next_kanji, 1)

            # Wrong answer
            else:
                print("Wrong answer")
                # Only update when first time answering
                if self.answered == 0:
                    self.master_kanji.updateKanji(False)
                    self.master_kanji.updateCurrent(self.next_kanji, 0)
                self.flashred()

            # An answer is given changes
            self.master_kanji.story_show = True
            self.answered = 1


if __name__ == '__main__':
    print("This code needs to be run with KanjiOrigin")