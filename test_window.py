# test_window.py
from kivy.app import App
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        return Label(text="정상 작동?")

if __name__ == '__main__':
    TestApp().run()
