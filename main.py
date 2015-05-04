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

#from data.screens.learnkanji import *
import data.screens.learnkanji


class KanjiOriginScreen(Screen):
    fullscreen = BooleanProperty(False)

    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(KanjiOriginScreen, self).add_widget(*args)


class KanjiOriginApp(App):

    index = NumericProperty(-1)
    current_title = StringProperty()
    time = NumericProperty(0)
    screen_names = ListProperty([])


    def build(self):
        self.title = 'Kanji Origin'
        Clock.schedule_interval(self._update_clock, 1 / 60.)
        self.screens = {}
        self.available_screens = ([
            'MainMenu', 'LearnKanji', 'LearningMethod', 'Donation', 'Credits'])
        self.screen_names = self.available_screens
        curdir = dirname(__file__)
        self.available_screens = [join(curdir, 'data', 'screens',
            '{}.kv'.format(fn)) for fn in self.available_screens]
        self.go_screen(0)

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def go_screen(self, idx):
        self.index = idx
        if idx == 0:
            self.root.ids.sm.switch_to(self.load_screen(idx), direction='right')
        else:
            self.root.ids.sm.switch_to(self.load_screen(idx), direction='left')

    def load_screen(self, index):
        if index in self.screens:
            return self.screens[index]
        screen = Builder.load_file(self.available_screens[index].lower())
        self.screens[index] = screen
        return screen

    def _update_clock(self, dt):
        self.time = time()

if __name__ == '__main__':
    KanjiOriginApp().run()