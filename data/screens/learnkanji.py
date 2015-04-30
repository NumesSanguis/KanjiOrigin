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


class KanjiLearn():
    def __init__(self):
        self.show_kanji = 'BS'

    def nextKanji(self):
        #self.learnAlg()
        self.show_kanji = '爪'

    def learnAlg(self):
        pass

class AnswerTextInput(TextInput):
    #Autocorrect filter
    design1 = ObjectProperty(None)

    #redefine insert_text
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


class LayoutFunction(BoxLayout):

    #!!! This code should be used
    keyb_height = 260 #260, 526
    #   Keyboard height will be available in a newer version of Kivy
    #keyb_height = Window.keyboard_height
    print(keyb_height)

    font_kanji = os.path.join('data', 'fonts', 'TakaoPMincho.ttf')
    show_answer = 0
    Kanji_s = ["爪", "冖", "心", "夂"]
    #!!!

    def timeNow(self):
        now = datetime.now()
        f = "%Y-%m-%d %H:%M:%S"
        now = now.strftime(f)
        print("time now: " + str(now))
        return now


    def timeDifference(self, time_1, time_2):
        # Gets time in strings
        # Returns difference in days
        f = "%Y-%m-%d %H:%M:%S"
        t_1 = datetime.strptime(time_1, f)
        t_2 = datetime.strptime(time_2, f)
        #print("Time: ")
        #print(t_1)
        #print(t_2)
        #print(type(t_1))
        time_diff = t_2 - t_1
        #print(time_diff)
        #print(time_diff.total_seconds())

        return time_diff.total_seconds() / 86400 #1 day

    # Function when the check/next button is pressed
    def btnPressed(self):
        print("- - - - -")


if __name__ == '__main__':
    print("This code needs to be run with KanjiOrigin")
