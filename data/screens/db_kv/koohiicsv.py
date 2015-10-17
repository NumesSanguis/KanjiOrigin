#!/usr/bin/kivy
# -*- coding: utf-8 -*-

from kivy.uix.screenmanager import  Screen


class KoohiiCSV(Screen):
    lbtext = "Not working yet. In the future you can here import your own stories in collabaration with " \
             "kanji.koohii.com/"
    bttext = "Not working yet"
    print("koohiiCSV initialized")

    def callback(self):
        print("\nImporting koohii .csv...")



        print("Finished importing koohii .csv.")