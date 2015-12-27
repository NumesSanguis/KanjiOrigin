from kivy.app import App
from kivy.cache import Cache
from kivy.atlas import Atlas


class TestApp(App):

    def build(self):
        atlas = Atlas("img/KOtheme.atlas")
        Cache.append("kv.atlas", 'data/images/defaulttheme', atlas)
        super(TestApp, self).build()

if __name__ == '__main__':
    TestApp().run()