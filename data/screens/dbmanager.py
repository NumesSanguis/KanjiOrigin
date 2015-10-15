#!/usr/bin/kivy
# -*- coding: utf-8 -*-

from os.path import dirname, join
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty


class DBScreen(Screen):
    pass


class DatabaseManager(ScreenManager):

    # Kivy variables
    screen_names = ListProperty([])

    def __init__(self, **kwargs):
        super(DatabaseManager, self).__init__(**kwargs)

        # Setting up screens for screen manager
        self.screens = {}
        self.available_screens = (['DBmenu', 'BackupSD', 'RestoreSD', 'koohiiCSV', 'ResetKO'])
        self.screen_names = self.available_screens
        curdir = dirname(__file__)
        self.available_screens = [join(curdir, 'db_kv',
            '{}.kv'.format(fn)) for fn in self.available_screens]
        self.go_screen(0)

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
            App.get_running_app().root.ids.dbm.switch_to(self.load_screen(idx), direction='right')
            # File "properties.pyx", line 757, in kivy.properties.ObservableDict.__getattr__ (kivy/properties.c:11093)
            # AttributeError: 'super' object has no attribute '__getattr__'
        # Go to Database menu
        else:
            App.get_running_app().root.ids.dbm.switch_to(self.load_screen(idx), direction='left')

    # Load kv file with Builder
    def load_screen(self, index):
        if index in self.screens:
            return self.screens[index]
        screen = Builder.load_file(self.available_screens[index].lower())
        self.screens[index] = screen
        return screen
