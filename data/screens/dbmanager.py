#!/usr/bin/kivy
# -*- coding: utf-8 -*-

from os.path import dirname, join
#from kivy.resources import resource_find
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ListProperty
from kivy.clock import Clock
from kivy.core.window import Window


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
        self.available_screens = (['DBmenu', 'BackupSD', 'RestoreSD', 'KoohiiCSV', 'ResetKO'])

        # print(self.available_screens)
        # self.available_screens = ([fn.lower() for fn in self.available_screens])

        print(self.available_screens)
        self.screen_names = self.available_screens

        curdir = dirname(__file__)
        self.available_screens = [join(curdir, 'db_kv',
            '{}.kv'.format(fn.lower())) for fn in self.available_screens]
        # self.available_screens = [resource_find('{}.kv'.format(fn))
        #                           for fn in self.available_screens]
        # print(self.available_screens)

        win = Window
        win.bind(on_keyboard=self.my_key_handler)

        self.go_screen(0)  # Clock.schedule_once(lambda dt:

    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(DatabaseManager, self).add_widget(*args)

    def my_key_handler(self, window, keycode1, keycode2, text, modifiers):
        print("Esc or back button pressed")

        # Esc or Android back button pressed
        if keycode1 in [27, 1001]:
            self.screen_changer()

    def screen_changer(self):
        # Not in main screen
        print("self.index: {}".format(self.index))
        if self.index != 0:
            print("Moving screen back")
            #print(self.screens[self.index])
            print("self.index not 0")
            self.go_screen(0)
            # Tell that the key is handled, so not calling the same function in the main.py
            return True
        # In main screen
        else:
            print("self.index 0")
            print("Going back to main menu")
            #App.get_running_app().stop()

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
        print("Buildozer loading screen: {}".format(index))
        print(type(self.screensy))
        if index in self.screensy:
            print("Screen loaded before")
            return self.screensy[index]

        print("Screen NOT loaded before")
        print(self.available_screens[index])
        screeny = Builder.load_file(self.available_screens[index])
        print(type(screeny))
        print(screeny)
        self.screensy[index] = screeny
        return screeny
