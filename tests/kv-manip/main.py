#!/usr/bin/kivy
# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty,\
    ListProperty, ObjectProperty
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class TestLabel(Label):
    print("label")

    #testy = ObjectProperty(None)

    def changer(self):
        self.ids.testy.text = "Changed ^_^"


class KanjiOriginApp(App):

    def build(self):
        print("build")

if __name__ == '__main__':
    KanjiOriginApp().run()