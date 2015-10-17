#!/usr/bin/kivy
# -*- coding: utf-8 -*-

from os.path import dirname, join
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty
from kivy.clock import Clock


# class DBScreen(Screen):
#
#     def add_widget(self, *args):
#         if 'content' in self.ids:
#             return self.ids.content.add_widget(*args)
#         return super(DBScreen, self).add_widget(*args)


class DatabaseManager(ScreenManager):

    # Kivy variables
    screen_names = ListProperty([])

    def __init__(self, **kwargs):
        super(DatabaseManager, self).__init__(**kwargs)

        # Setting up screens for screen manager
        self.screensy = {}
        self.available_screens = (['DBmenu', 'BackupSD', 'RestoreSD', 'koohiiCSV', 'ResetKO'])
        print(self.available_screens)
        self.available_screens = ([fn.lower() for fn in self.available_screens])
        print(self.available_screens)
        self.screen_names = self.available_screens
        curdir = dirname(__file__)
        self.available_screens = [join(curdir, 'db_kv',
            '{}.kv'.format(fn)) for fn in self.available_screens]
        self.go_screen(0)  # Clock.schedule_once(lambda dt:

    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(DatabaseManager, self).add_widget(*args)

    # Go to other screen
    def go_screen(self, idx):
        print("Change DBScreen to: {}".format(idx))
        self.index = idx
        # Go not to Database menu
        if idx == 0:
            self.switch_to(self.load_screen(idx), direction='right')

        # Go to Database menu
        else:
            self.switch_to(self.load_screen(idx), direction='left')

    # Load kv file with Builder
    def load_screen(self, index):
        print("Buildozer loading screen...")
        print(type(self.screensy))
        if index in self.screensy:
            return self.screensy[index]
        
        print(self.available_screens[index])
        screeny = Builder.load_file(self.available_screens[index])
        print(type(screeny))
        print(screeny)
        self.screensy[index] = screeny
        return screeny
