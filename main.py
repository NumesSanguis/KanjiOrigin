#!/usr/bin/kivy
# -*- coding: utf-8 -*-

#import os
from kivy.app import App
from os.path import dirname, join
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty,\
    ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
#from kivy.uix.behaviors import FocusBehavior
#from kivy.metrics import dp
#import csv
#from kivy.utils import platform
import data.screens.learnkanji_k_alg as lrnalg
#from kivy.resources import resource_add_path

from kivy import platform
from sys import exc_info


# Screen used by main ScreenManager
class KanjiOriginScreen(Screen):
    fullscreen = BooleanProperty(False)
    #has_screenmanager = BooleanProperty(False)
    # If there is a ScreenManager in a ScreenManager
    ac_prev = ObjectProperty(None)

    # def __init__(self, **kwargs):
    #     super(KanjiOriginScreen, self).__init__(**kwargs)
    #     self.bind(txt_input_focus = self.TextFocusChange)

    # 'content' refers to the id of the GridLayout in KanjiOriginScreen in kanjiorigin.kv
    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(KanjiOriginScreen, self).add_widget(*args)
    #
    # def TextFocusChange(self):
    #     print("Screen TextInput focus: {}".format(self.txt_input_focus))


# Main app
class KanjiOriginApp(App):

    # Kivy variables
    index = NumericProperty(-1)
    current_title = StringProperty()
    time = NumericProperty(0)
    screen_names = ListProperty([])
    actionbar_status = ListProperty([0, 0, 0, 0])
    ac_prev = ObjectProperty(None)

    def build(self):
        self.title = 'KanjiOrigin'
        self.icon = 'ko.png'

        if platform != 'android' and platform != 'ios':
            from kivy.core.window import Window
            Window.size = (600, 720)

        #Clock.schedule_interval(self._update_clock, 1 / 60.)

        # Relative import
        # resource_add_path(os.path.join(os.path.dirname(__file__), 'data'))
        # resource_add_path(os.path.join('data', 'screens'))
        # resource_add_path(os.path.join('screens', 'db_kv'))

        # Setting up screens for screen manager
        self.screens = {}
        self.available_screens = ([
            'MainMenu', 'LearnKanji_k', 'LearningMethod', 'DBmanager', 'Donation', 'Credits'])  # Backup
        self.screen_names = self.available_screens
        curdir = dirname(__file__)
        self.available_screens = [join(curdir, 'data', 'screens',
            '{}.kv'.format(fn)) for fn in self.available_screens]
        self.go_screen(0)  # Clock.schedule_once(lambda dt: )

        # Binds the back button on Android
        self.bind(on_start=self.post_build_init)

        # Status bar
        try:
            self.learnalg_count = lrnalg.LearnCount()
            if self.learnalg_count.db_exist:
                self.actionbar_status = self.learnalg_count.countlearned()
            else:
                self.actionbar_status = [-1, -1, -1, -1]

        except:
            print("Database error or learnkanji_k_alg.py not found")

    # Binds the back button on Android
    def post_build_init(self, *args):
        # if platform() == 'android':
        #     import android
        #     android.map_key(android.KEYCODE_BACK, 1001)

        win = Window
        win.bind(on_keyboard=self.my_key_handler)

    def my_key_handler(self, window, keycode1, keycode2, text, modifiers):
        # Esc or Android back button pressed
        if keycode1 in [27, 1001]:
            print("Esc or back button pressed")
            # Keyboard open -> close it
            #if Window.keyboard_height > dp(25):
            #    window.close()

            # if FocusBehavior._keyboards and any(FocusBehavior._keyboards.values()):
            #     print(FocusBehavior._keyboards.values())

            return(self.screen_changer(True))

        #return True

    def screen_changer(self, kill=False):
        # Not in main screen
        print("self.index: {}".format(self.index))
        if self.index != 0:
            print("Moving screen back")
            print(self.screens[self.index])
            # if self.screens[self.index].has_screenmanger == True:
            #     pass
            # else:
            print("self.index not 0")
            self.go_screen(0)
            # Tell that the key is handled, so not closing app
            return True

        # In main screen
        else:
            print("self.index 0")
            # Don't kill app when ActionPrevious is pressed
            if kill == True:
                print("Closing App")
                App.get_running_app().stop()



    # On App pause
    def on_pause(self):
        # Keeps the app running in the background
        return True

    # App is reopened
    def on_resume(self):
        # Refresh current learn status
        if self.learnalg_count:
            if self.learnalg_count.db_exist:
                self.actionbar_status = self.learnalg_count.countlearned()

        # Defocus AnswerInput to prevent having to defocus and focus for keyboard
        try:
            print("Defocus try")
            # If in screen Learn Kanji
            if self.index == 1:
                print("Before: {}".format(self.screens[1].children[0].children[0].ids.txt_field.focus))
                # Set AnswerTextInput to False
                self.screens[1].children[0].children[0].ids.txt_field.focus = False
                if not self.screens[1].children[0].children[0].answered:
                    # If answer still has to be given, open keyboard after delay
                    # (needed for proper functioning)
                    Clock.schedule_once(lambda dt: self.keyboard_opener(), .2)
                    #self.screens[1].children[0].children[0].ids.txt_field.focus = True
                print("After: {}".format(self.screens[1].children[0].children[0].ids.txt_field.focus))
        except:  # KeyError:
            print("Defocus AnswerInput failed or not existing")
            print(exc_info()[0])

    # Open keyboard by setting AnswerTextInput focused
    def keyboard_opener(self):
        self.screens[1].children[0].children[0].ids.txt_field.focus = True

    # Go to other screen
    def go_screen(self, idx):
        print("Change MainScreen to: {}".format(idx))
        self.index = idx
        # Go to not main menu
        if idx == 0:
            self.root.ids.sm.switch_to(self.load_screen(idx), direction='right')
        # Go to main menu
        else:
            # Only load learnkanji.py when the screen is called
            #if idx == 1:
            #    import data.screens.learnkanji
            self.root.ids.sm.switch_to(self.load_screen(idx), direction='left')


        # try:
        #     print("Next Kanji:")
        #     print(self.screens[1].children[0].children[0].ids.send_btn.text)
        #     print(self.screens[1].children[0].children[0].answered)  #TODO
        # except:
        #     print(exc_info()[0])

        # Defocus AnswerInput to prevent having to defocus and focus for keyboard
        # try:
        #     print("Defocus try")
        #     print(self.screens[1])
        #     #if self.screens[1].txt_input_focus:
        #     print("Before: {}".format(self.screens[1].txt_input_focus))
        #     #self.screens[1].txt_input_focus = True
        #     self.screens[1].children[0].children[0].ids.txt_field.focus = False
        #     print("After: {}".format(self.screens[1].txt_input_focus))
        # except:  # KeyError:
        #     print("Defocus AnswerInput failed or not existing")
        #     print(exc_info()[0])

    # Load kv file with Builder
    def load_screen(self, index):
        if index in self.screens:
            return self.screens[index]
        screen = Builder.load_file(self.available_screens[index].lower())
        self.screens[index] = screen
        return screen

    # def _update_clock(self, dt):
    #     self.time = time()

if __name__ == '__main__':
    KanjiOriginApp().run()