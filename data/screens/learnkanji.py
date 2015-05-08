#!/usr/bin/kivy
# -*- coding: utf-8 -*-

import os
from time import time
from kivy.app import App
from os.path import dirname, join
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty,\
    ListProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

import re
from collections import deque
import sqlite3
from datetime import datetime


class AnswerTextInput(TextInput):
    # Autocorrect filter
    design1 = ObjectProperty(None)

    # redefine insert_text
    def insert_text(self, substring, from_undo=False):
        #print(self.design1.auto_correct_check)

        # if self.design1.auto_correct_check is False:
        #     #Get current text in textfield
        #     #print(substring)
        #     #Clean text
        #     current_text = self.design1.textManipulation(substring)
        #     len_ACT = len(self.design1.auto_correct_text)
        #     #Autocorrect has probably kicked in
        #     if len(current_text) >= len_ACT:
        #         #print("length ACT: " + str(len_ACT))
        #         #Check current text with previous answer for autocorrect
        #         checku = 0
        #         for l in range(len_ACT):
        #             #print(l)
        #             if current_text[l] == self.design1.auto_correct_text[l]:
        #                 checku += 1
        #         #print("Number same letters: " + str(checku))
        #         #If indeed auto correct
        #         if checku == len_ACT:
        #             #print("Do I come here?")
        #             #print(current_text[len_ACT:])
        #             s = current_text[len_ACT:]
        #             self.auto_correct_check = True
        #             return super(AnswerTextInput, self).insert_text(s, from_undo=from_undo)

        #self.auto_correct_check = True
        #substring = substring.lower()
        return super(AnswerTextInput, self).insert_text(substring, from_undo=from_undo)

    def resettext(self, next_kanji):
        if next_kanji == True:
            self.text = ""
            self.focus = True


class DBhandling():
    def __init__(self):
        pass




# Handles everything related to shown Kanji
class MasterKanji():
    def __init__(self):
        self.current, self.cur_answer, self.story = self.conndb("current", "SELECT", "*")
        self.upcoming = deque(range(1,13)) #learnAlg
        #self.story = "Love is such a profound thing"
        self.story_show = False
        self.story_hidden = "The answer is hidden, nanana"

    # Handles database
    def conndb(self, tabl, action, item, req=""):
        # tabl = Table, action = SELECT/UPDATE, item = what should be selected/*

        # Connect Database
        print("Trying to connect to DB")
        conn = sqlite3.connect(os.path.join("data", "db", "Kanji-story.db")) # path from main.py
        c = conn.cursor()
        print("DB connected with Table: {} and Action: {}".format(tabl, action))

        c.execute("{} {} FROM {}{}".format(action, item, tabl, req))
        result = c.fetchall()
        print(result)

        if tabl == "current" or "Kanji" and action == "SELECT":
            if tabl == "Kanji":
                returny = result[0]
                #c.execute("UPDATE current SET framenum = {}".format(req[-1])) # Uncomment when should not start love
            else:
                c.execute("SELECT character, meanings, story FROM KANJI WHERE framenum={}".format(result[0][0]))
                returny = c.fetchone()
            returny = list(returny)
            answers = returny[1].split('/')
            returny[1] = answers

        # Save change to database
        #conn.commit()

        # Close connection
        conn.close()
        print("DB connection closed")

        if action == "SELECT":
           return returny
           #return #list


    # Next Kanji
    def nextkanji(self):
        # All Kanji's are learned
        if not self.upcoming:
            self.story = "That was the last Kanji 0.o\nYou dit it, YOU DID IT!!!!!"
            self.current = "DONE"
            self.cur_answer = "amazing"

        # Get next Kanji character, answer, story and also update current table
        else:
            # Get new Kanji and answer
            self.current, self.cur_answer, self.story = self.conndb("Kanji", "SELECT", "character, meanings, story",
                                                        " WHERE framenum = {}".format(self.upcoming.popleft()))

    # Update database with current knowledge of answered Kanji
    def updateKanji(self, correct):

        pass

    # Check if typed answer is correct
    def check(self, answer):
        if answer in self.cur_answer:
            return 1
        else:
            return 0


class LayoutFunctioning(BoxLayout):

    # Keyboard stuff, still has to be changed
    keyb_height = NumericProperty(260) #260, 526
    #   Keyboard height will be available in a newer version of Kivy
    #keyb_height = Window.keyboard_height
    print(keyb_height)

    font_kanji = os.path.join('data', 'fonts', 'TakaoPMincho.ttf')
    #Kanji_s = ["爪", "冖", "心", "夂"]

    next_kanji = False
    master_kanji = MasterKanji()

    # Current Time
    def timeNow(self):
        now = datetime.now()
        f = "%Y-%m-%d %H:%M:%S"
        now = now.strftime(f)
        print("time now: " + str(now))
        return now

    # Calculate difference between 2 time points
    def timeDifference(self, time_1, time_2):
        # Gets time in strings
        # Returns difference in days
        f = "%Y-%m-%d %H:%M:%S"
        t_1 = datetime.strptime(time_1, f)
        t_2 = datetime.strptime(time_2, f)
        time_diff = t_2 - t_1
        #print(time_diff)
        #print(time_diff.total_seconds())

        return time_diff.total_seconds() / 86400 #1 day

    #Formats the answer of the user
    def textFormat(self, answer):
        #Set answer to lower case and clean the answer of strange symbols
        answer = answer.lower()
        pattern = '[a-z0-9]'
        answer = ''.join(re.findall(pattern, answer))
        return answer

    # Function when the check/next button is pressed
    def btnPressed(self, answer):
        print("- - - - -")

        #Only do something when user actually typed or answer has been correct
        if len(answer) > 0 or self.next_kanji == True:

            # Get next Kanji after answered correctly
            if self.next_kanji == True:
                # Next Kanji
                self.master_kanji.nextkanji()
                self.ids.learn_kanji.text = self.master_kanji.current

                # Next Story although hidden
                #self.ids.story.text = self.master_kanji.story

                #re-init
                self.next_kanji = False
                self.ids.send_btn.text = "Check"
                print(self.master_kanji.cur_answer)
                self.ids.answer_bar.opacity = 0
                self.ids.answer_bar.text = ', '.join(self.master_kanji.cur_answer)
                self.ids.story.text = self.master_kanji.story_hidden
                self.master_kanji.story_show = False

            # Check given answer
            else:
                answer = self.textFormat(answer)

                # Correct answer
                if self.master_kanji.check(answer):
                    print("Correct answer")
                    self.next_kanji = True
                    self.ids.send_btn.text = "Next"
                    self.ids.answer_bar.background_color = (0, 0.7, 0, 1)
                    self.master_kanji.updateKanji(True)

                # Wrong answer
                else:
                    print("Wrong answer")
                    self.ids.answer_bar.background_color = (0.7, 0, 0, 1)
                    self.master_kanji.updateKanji(False)

                # An answer is given changes
                self.ids.answer_bar.opacity = 1
                self.show_answer = 1
                self.ids.story.text = self.master_kanji.story
                self.master_kanji.story_show = True


if __name__ == '__main__':
    print("This code needs to be run with KanjiOrigin")
