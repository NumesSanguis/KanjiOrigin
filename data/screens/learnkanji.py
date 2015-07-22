#!/usr/bin/kivy
# -*- coding: utf-8 -*-

import os
from kivy.app import App
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.uix.button import Button
from kivy.factory import Factory
#from kivy.clock import Clock

import re
from collections import deque
import sqlite3
#import numpy as np # Needed for pyxdameraulevenshtein
#from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance_withNPArray # Add module TODO
from difflib import SequenceMatcher

import learnkanji_alg


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
    current = StringProperty()
    cur_answer = ListProperty()
    story = StringProperty()
    story_show = BooleanProperty(False)
    fix_answer = StringProperty("")

    def __init__(self, **kwargs):
        super(MasterKanji, self).__init__(**kwargs)

        self.alg = learnkanji_alg.LearnAlg()
        self.cur_framenum = self.conndb("current", "SELECT", "framenum")
        print("Init with current framenum: {}".format(self.cur_framenum))
        self.current, self.cur_answer, self.story = self.conndb("current", "SELECT", "*")
        self.upcoming = deque()  # deque(self.alg.retrieveKanji()) gives error
        self.story_hidden = "The answer is hidden, please provide an answer in the text-bar above and press 'check'." \
                            "\nYou cannot advance to the next Kanji until you have typed the right response."

    # Handles database
    def conndb(self, tabl, action, item, req=""):
        # tabl = Table, action = SELECT/UPDATE, item = what should be selected/*

        # Connect Database
        print("Trying to connect to DB")
        conn = sqlite3.connect(os.path.join("data", "db", "Kanji-story.db")) # path from main.py
        c = conn.cursor()
        print("DB connected with Table: {}, Action: {} and item: {}".format(tabl, action, item))

        if action == "SELECT":
            c.execute("{} {} FROM {}{}".format(action, item, tabl, req))
            result = c.fetchall()
            print(result)
            if item != "nextKanji" and item != "framenum":
                print("I have no nextKanji or framnum, because item = {}".format(item))
                if tabl == "Kanji":
                    returny = result[0]
                    #c.execute("UPDATE current SET framenum = {}".format(req[-1])) # Uncomment when should not start love
                else:
                    c.execute("SELECT character, meanings, story FROM KANJI WHERE framenum={}".format(result[0][0]))
                    returny = c.fetchone()
                returny = list(returny)
                answers = returny[1].split('/')
                # Makes the answers lower case
                returny[1] = answers  #[x.lower() for x in answers]
            else:
                print("I do have {}".format(item))
                returny = result[0][0]
                print(returny)

        else:
            c.execute("{} {} SET {}".format(action, tabl, req))

            # Save change to database
            conn.commit()

        # Close connection
        conn.close()
        print("DB connection closed")

        if action == "SELECT":
           return returny
           #return #list

    # Next Kanji
    def nextkanji(self):

        # Get next list of to be learned Kanji
        if not self.upcoming:
            self.upcoming = deque(self.alg.retrieveKanji())

        # All Kanji's are learned
        if not self.upcoming:
            self.cur_framenum = -1
            self.current, self.cur_answer, self.story = self.conndb("Kanji", "SELECT", "character, meanings, story",
                                                        " WHERE framenum = -1")

        # Get next Kanji character, answer, story and also update current table
        else:
            # Get new Kanji and answer
            self.cur_framenum = self.upcoming.popleft()
            print(self.cur_framenum)
            self.current, self.cur_answer, self.story = self.conndb("Kanji", "SELECT", "character, meanings, story",
                                                        " WHERE framenum = {}".format(self.cur_framenum))
            # TODO answers bold in self.story, wrap [b][/b] around it.

        # Update status learning
        status = self.alg.countlearned()

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

        self.conndb("current", "Update", "*", "framenum = {}, nextKanji = {}".format(self.cur_framenum, nxt_cur))

    # Update database with current knowledge of answered Kanji
    def updateKanji(self, correct):
        # Don't update when showing finished screen
        if self.cur_framenum != -1:
            self.alg.answerKanji(self.cur_framenum, correct)

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
        if sm_list[sm_ind] > 0.6:
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
    keyb_height = BooleanProperty(dp(260))  #280  #254
    print("Keyboard height: {}".format(keyb_height))

    font_kanji = os.path.join('data', 'fonts', 'TakaoPMincho.ttf')
    #Kanji_s = ["爪", "冖", "心", "夂"]

    next_kanji = BooleanProperty(False)
    answered = BooleanProperty(False)
    master_kanji = MasterKanji()

    txt_field_focus_i = BooleanProperty(True)
    if master_kanji.cur_framenum == 0:
        txt_field_focus_i = BooleanProperty(False)

    # Link button to website
    ww_link = StringProperty()

    # TODO Enter on keyboard
    #Window.bind(on_key_enter = btnPressed(answer))

    def __init__(self, **kwargs):
        super(LayoutFunctioning, self).__init__(**kwargs)

        # When previously saw finish screen
        if self.master_kanji.cur_framenum == -1:
            self.master_kanji.nextkanji()
            self.reinitscreen(0)
        else:
            self.reinitscreen(self.master_kanji.conndb("current", "SELECT", "nextKanji"))

        # First time opening app show explanation story
        if self.master_kanji.cur_framenum == 0:
            print("First time app")
            self.master_kanji.story_show = True

        # Link button to website
        print("!!!   DEBUG UTF-8   !!!")
        #print(self.master_kanji.current)
        print(type(self.master_kanji.current))
        self.ww_link = u"http://kanji.koohii.com/study/kanji/{}".format("TODO") #self.master_kanji.current error

        # Keyboard height
        #Clock.schedule_once(lambda dt: self.storykeybheight())

        print("Keyboard binding")
        Window.bind(on_keyboard=self.storykeybheight)

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

        # Wrong answer
        else:
            print("Reinit: wrong")
            self.next_kanji = False
            self.answered = 1
            self.master_kanji.story_show = True

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

    # Flash the TextInput red when wrong answer is given
    def flashred(self):
        print("Flashing textinput red")
        self.ids.txt_field.background_color = (1, 0.4, 0.4, 1)
        Animation(background_color=(1, 0.75, 0.75, 1), duration=.5).start(self.ids.txt_field)

    def changeStory(self, skanji):
        print("Change story to {}".format(skanji))

    def addsKanji(self):
        print("addsKanji")
        self.ids.sKanjibox.add_widget(Factory.SKanjiToggleButton(on))
        #self.ids.foo.text = "T"

    # Function when the check/next button is pressed
    def btnPressed(self, answer):
        print("\n- - - - -")

        #Only do something when user actually typed or answer has been correct
        if len(answer) > 0 or self.next_kanji == True:
            #self.ids.story_box.height = Window.keyboard_height - dp(8)
            #print("New keyb height: {}".format(self.ids.story_box.height))

            # TODO bind()
            # Get next Kanji after answered correctly
            if self.next_kanji == True:
                print("Next Kanji...")
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

                # update current in DB
                self.master_kanji.updateCurrent(self.next_kanji)

            # Check given answer
            else:
                print("Checking answer...")
                answer = self.master_kanji.textFormat(answer)

                # Correct answer
                if self.master_kanji.check(answer):
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
