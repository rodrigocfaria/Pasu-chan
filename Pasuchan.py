import pasuchan_guts as pg
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.properties import ListProperty
from kivy.properties import BooleanProperty
from kivy.utils import escape_markup
from kivy.factory import Factory
from kivy.config import Config
from kivy.metrics import dp
from kivy.graphics import Color
from kivy.uix.behaviors import ButtonBehavior
from bisect import bisect
import re
import subprocess as sp
import threading as th
import queue as q
import os
from functools import partial
from time import perf_counter

Config.set('kivy', 'window_icon', "KaraoPy256.png")
Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '600')
#Config.set('modules', 'monitor', 1)

with open("PasuchanUTF8.kv", encoding='utf-8') as f:
    Builder.load_string(f.read())

SEARCH_INDEX_CONST = [0, 100000]

class InterfaceWidget(FloatLayout):

    default_entry_color = ListProperty([100/255, 100/255, 100/255, 1])
    selected_entry_color = ListProperty([12/255,134/255,186/255,1])
    search_bar_msg = 'Type to search by name'
    search_bar_fore_color = [0.3, 0.3, 0.3, 1]
    search_bar_fore_color_focus = [0, 0, 0, 1]
    n = 0
    entries = []
    selected_entries = []
    file_loaded = False
    current_file = ''
    master_password = ''
    user_input = True
    j=0
    search_indexes = SEARCH_INDEX_CONST
    
    def __init__(self, **kwargs):
        super(InterfaceWidget, self).__init__(**kwargs)
        
        search_bar = self.search_class('SearchBar')
        search_bar.ids['search_field'].text = self.search_bar_msg
        search_bar.ids['search_field'].bind(text = self.search)

        self.update_status_bar('Load a file to start.')
    
    def update(self, dt):
        pass
    
    def add_entry(self):
        data = {'name': '', 
                'login': '',
                'password': '', 
                'enc_status': [False, False, False], 
                'new': True, 
                'modified': [False, False, False],
                'visible': [True, False, False]}
        self.search_indexes = SEARCH_INDEX_CONST
        self.unenc_data.append(data)
        self.update_entries()

    def delete_entry(self):
        for index in self.selected_entries:
            for i in range(0,len(self.unenc_data)):
                if index == self.unenc_data[i]['index']:
                    self.unenc_data.pop(i)
                    break

            # for entry in self.entries:
            #     if index == entry.index:
            #         self.entries.remove(entry)
            #         #self.unenc_data.pop(entry.index)
        self.update_entries()
        self.selected_entries = []   

    def clear_search(self):
        search_bar = self.search_class('SearchBar')
        search_bar.ids['search_field'].text = self.search_bar_msg
        search_bar.ids['search_field'].foreground_color = self.search_bar_fore_color
        search_bar.ids['search_field'].focus = False
        search_bar.ids['search_field'].already_focused = False
        self.search_indexes = SEARCH_INDEX_CONST
        self.update_entries()

    def search_focus(self, widget):
       if widget.already_focused == False and widget.focus == True:
            widget.text = ''
            widget.foreground_color = self.search_bar_fore_color_focus
            widget.already_focused = True

    def select_entry(self, entry):
        if entry.state == 'normal':
            entry.state = 'down'
            entry.color = self.selected_entry_color
            self.selected_entries.append(entry.index)
        else:
            entry.state = 'normal'
            entry.color = self.default_entry_color
            self.selected_entries.remove(entry.index)
        
        self.update_selection_button()

    def select_all(self):
        for entry in self.entries:
            if entry.state == 'normal':
                self.select_entry(entry)

        # for entry in self.entries:
        #     self.selected_entries.append(entry)

        self.update_selection_button()

    def deselect_all(self):
        for entry in self.entries:
            if entry.state == 'down':
                self.select_entry(entry)

        self.selected_entries = []
        self.update_selection_button()
 
    def update_entries(self): #update UI
        widget = self.search_class('PasswordsList')
        widget.ids['grid'].clear_widgets()
        self.n = 0
        self.entries = []
        for data in self.unenc_data:
            entry = Factory.EntryLine()
            entry.index = self.n
            data['index'] = self.n
            self.entries.append(entry)
            self.n += 1

            if self.search_indexes[0] <= entry.index <= self.search_indexes[1]:
                widget.ids['grid'].add_widget(entry)

                if data['new'] == True:
                    entry.ids.name.text = '(Name)'
                    entry.ids.login.text = '(Login)'
                    entry.ids.password.text = '(Password)'
                    #data['new'] = False
                else:
                    entry.ids.name.text = data['name']
                if data['enc_status'][1] == True:                
                    entry.ids.login.text = '(Login, encrypted)'
                else:
                    entry.ids.login.text = '(Login, decrypted)'
                if data['enc_status'][2] == True:
                    entry.ids.password.text = '(Password, encrypted)'
                else:
                    entry.ids.password.text = '(Password, decrypted)'

                entry.state = 'normal'
                entry.color = self.default_entry_color
    
        self.update_selection_button()
        self.paint_modified()
        self.update_show()
        ab2 = self.search_class('ActionBar2')
        ab2.ids.change_mp_btn.disabled = False    
        ab1 = self.search_class('ActionBar1')
        ab1.ids.save_btn.disabled = False
        ab1.ids.add_entry.disabled = False
                        
    def update_selection_button(self):
        actionbar2 = self.search_class('ActionBar2')
        actionbar1 = self.search_class('ActionBar1')

        if len(self.entries) == 0:
            actionbar2.ids.deselect_all.disabled = True
            actionbar2.ids.deselect_all.disabled = True
            actionbar1.ids.del_entry.disabled = True
        elif len(self.selected_entries) == 0:
            actionbar2.ids.deselect_all.disabled = True
            actionbar2.ids.select_all.disabled = False
            actionbar1.ids.del_entry.disabled = True
        elif 0 < len(self.selected_entries) < len(self.entries):
            actionbar2.ids.deselect_all.disabled = False
            actionbar2.ids.select_all.disabled = False
            actionbar1.ids.del_entry.disabled = False
        else:
            actionbar1.ids.del_entry.disabled = False
            actionbar2.ids.deselect_all.disabled = False
            actionbar2.ids.select_all.disabled = True

    def scroll_to(self, widget):
        for i in range(0, len(self.children)):
            object_name = re.search('(?<=\.)[A-z0-9]+(?= )', str(self.children[i])).group(0)
            if object_name == 'PasswordsList':
                ScrollView.scroll_to(self.children[i].ids.scroll, widget)

    def search_class(self, classs):
        for i in range(0, len(self.children)):
            class_name = re.search('(?<=\.)[A-z0-9]+(?= )', str(self.children[i])).group(0)
            if class_name == classs:
                return self.children[i]

    def update_status_bar(self, text):
        statusbar = self.ids['status_bar']
        statusbar.text = text

    def open_filechooser(self):
        sp.run('py filechooser.py')

        with open('filechooser_result','r') as f:
            path = f.read()
        os.remove('filechooser_result')
        if path != self.current_file:
            self.master_password = ''
        self.load_file(path)

    def load_file(self, path):

        self.unenc_data = []

        if path != '':
            load_result = pg.load_file(path)
            if load_result == 'FILE_EMPTY':
                self.enc_data = ''
                self.current_file = path
                filebar = self.search_class('FileBar')
                path_input = filebar.ids['current_file']
                path_input.text = self.current_file
                self.update_status_bar('New pasu file opened.')
                self.file_loaded = True
                self.change_mp()
                self.update_entries()
            elif load_result == 'JSON_ERROR':
                self.enc_data = ''
                self.current_file = ''
                self.update_status_bar('Invalid content.')
                self.file_loaded = False
            else:
                self.enc_data = load_result
                self.current_file = path
                #path_input.text = self.current_file
                #self.file_loaded = True
                if self.master_password == '':
                    self.masterpw_input()
                else:
                    self.decrypt_names(self.master_password, None)
  

    def decrypt_names(self, masterpw, popup):

        try:
            self.unenc_data = pg.decrypt_names(masterpw, self.enc_data)
        except Exception as e:
            print(e)
            if popup != None:
                popup.title = 'Password is incorrect or file corrupted, try again.'
                popup.title_color = [1,0,0.1,1]
            self.master_password = ''
        else:
            if popup != None:
                self.master_password = masterpw
                popup.dismiss()
            self.update_status_bar('File loaded.')
            self.file_loaded = True
            filebar = self.search_class('FileBar')
            path_input = filebar.ids['current_file']
            path_input.text = self.current_file
            for data in self.unenc_data:
                data['enc_status'] = [False, True, True]
                data['new'] = False
                data['modified'] = [False, False, False]
                data['visible'] = [True, False, False]
            #os.remove(self.current_file)
            self.indexes_to_display = []
            for i in range(0,len(self.unenc_data)):
                self.indexes_to_display.append(i)
            sb = self.search_class('SearchBar')
            sb.ids['search_field'].disabled = False
            self.update_entries()



    def masterpw_input(self):
        masterpw_popup = Factory.MasterPasswordPopup()
        masterpw_popup.open()

    def open_encrypting_popup(self):
        enc_popup = Factory.EncryptingPopup()
        enc_popup.open()
        Clock.schedule_once(partial(self.save_file, enc_popup),1)

    def save_file(self, enc_popup, dt):
        enc_data = []
        for data in self.unenc_data:
            buf = {}
            for field, i in zip(['name','login','password'], range(3)): #field
                if data['enc_status'][i] == False:
                    buf[field] = pg.encrypt(self.master_password, data[field])
                else:
                    buf[field] = data[field]
            enc_data.append(buf)

        pg.update_file(self.current_file, enc_data)
        self.load_file(self.current_file)
        enc_popup.dismiss()
        self.update_status_bar('File saved.')
    
    def change_mp(self):
        changemp_popup = Factory.ChangempPopup()
        changemp_popup.open()

    def mp_ok(self, popup):
        if popup.ids.masterpwone.text != popup.ids.masterpwtwo.text:
            popup.ids.msg.text = 'Passwords didn\'t match.'
            popup.ids.msg.color = [1,0,0.1,1]
        else:
            self.master_password = popup.ids.masterpwtwo.text
            popup.dismiss()
            self.open_encrypting_popup()
    
    def mp_show(self, popup, state, field):
        if state == 'down':
            popup.ids[field].password = False
        else:
            popup.ids[field].password = True


    def text_changed(self, widget, field):
        index = widget.parent.index
        bg = [249/255, 98/255, 6/255, 1]

        if widget.text != '' and widget.focus == True and self.user_input == True:
            if field == 'login':
                self.unenc_data[index]['modified'][1] = True
                self.unenc_data[index]['enc_status'][1] = False
                self.unenc_data[index]['login'] = widget.text
            if field == 'password':
                self.unenc_data[index]['modified'][2] = True
                self.unenc_data[index]['enc_status'][2] = False
                self.unenc_data[index]['password'] = widget.text
            if field == 'name':
                self.unenc_data[index]['modified'][0] = True
                self.unenc_data[index]['enc_status'][0] = False
                self.unenc_data[index]['name'] = widget.text
            widget.background_color = bg

    def paint_modified(self):
        d = ['name','login','password']
        bg = [249/255, 98/255, 6/255, 1]
        for entry in self.entries:
            for i in range(3):
                if self.unenc_data[entry.index]['modified'][i] == True:
                    entry.ids[d[i]].background_color = bg

    def show(self, widget, state, field):
        self.user_input = False
        index = widget.parent.index

        if field == 'login':
            
            if state == 'down':
                if self.unenc_data[index]['enc_status'][1] == True:
                    self.update_status_bar('Decrypting.')
                    login = pg.decrypt(self.master_password, self.unenc_data[index]['login'])
                    self.unenc_data[index]['login'] = login
                    widget.parent.ids['login'].text = login
                    self.unenc_data[index]['enc_status'][1] = False
                    self.update_status_bar('Decrypted.')
                else:
                    widget.parent.ids['login'].text = self.unenc_data[index]['login']
                self.unenc_data[index]['visible'][1] = True
                widget.parent.ids['login'].password = False
                
            else:
                if self.unenc_data[index]['modified'][1] == False:
                    if self.unenc_data[index]['enc_status'][1] == True:
                        widget.parent.ids['login'].text = '(Login, encrypted)'
                    else:
                        widget.parent.ids['login'].text = '(Login, decrypted)'
                    widget.parent.ids['login'].password = False
                else:
                    widget.parent.ids['login'].password = True
                self.unenc_data[index]['visible'][1] = False
                
        if field == 'password':
            
            if state == 'down':
                if self.unenc_data[index]['enc_status'][2] == True:
                    self.update_status_bar('Decrypting.')
                    password = pg.decrypt(self.master_password, self.unenc_data[index]['password'])
                    self.unenc_data[index]['password'] = password
                    widget.parent.ids['password'].text = password
                    self.unenc_data[index]['enc_status'][2] = False
                    self.update_status_bar('Decrypted.')
                else:
                    widget.parent.ids['password'].text = self.unenc_data[index]['password']
                self.unenc_data[index]['visible'][2] = True
                widget.parent.ids['password'].password = False
                
            else:
                if self.unenc_data[index]['modified'][2] == False:
                    if self.unenc_data[index]['enc_status'][2] == True:
                        widget.parent.ids['password'].text = '(Password, encrypted)'
                    else:
                        widget.parent.ids['password'].text = '(Password, decrypted)'
                    widget.parent.ids['password'].password = False
                else:
                    widget.parent.ids['password'].password = True
                self.unenc_data[index]['visible'][2] = False
    
        self.user_input = True

    def update_show(self):
        d = ['login_button','password_button']
        for entry in self.entries:
            for i in range(2):
                if self.unenc_data[entry.index]['visible'][i+1] == True:
                    entry.ids[d[i]].state = 'down'

    def focus(self, widget, field):
        self.user_input = False
        index = widget.parent.index
        
        if widget.focus == True: ##########################
            if field != 'name':
                idd = field + '_button'
                if widget.parent.ids[idd].state == 'normal':
                    widget.password = True

            if field == 'name':
                if self.unenc_data[index]['modified'][0] == False:
                    widget.text = ''
                else:
                    widget.text = self.unenc_data[index]['name']
            
            if field == 'login':
                if self.unenc_data[index]['modified'][1] == False:
                    if self.unenc_data[index]['enc_status'][1] == True:
                        widget.text = ''
                    else:
                        widget.text = self.unenc_data[index]['login']
                else:
                    pass

            if field == 'password':
                if self.unenc_data[index]['modified'][2] == False:
                    if self.unenc_data[index]['enc_status'][2] == True:
                        widget.text = ''
                    else:
                        widget.text = self.unenc_data[index]['password']
                else:
                    pass

        else:
            if field == 'name':
                if self.unenc_data[index]['modified'][0] == False:
                    widget.text = self.unenc_data[index]['name']
                else:
                    pass
            
            if field == 'login':
                if self.unenc_data[index]['modified'][1] == False:
                    widget.password = False
                    if self.unenc_data[index]['visible'][1] == False:
                        if self.unenc_data[index]['enc_status'][1] == False:
                            widget.text = '(Login, decrypted)'
                        else:
                            widget.text = '(Login, encrypted)'
                else:
                    pass

            if field == 'password':
                if self.unenc_data[index]['modified'][2] == False:
                    widget.password = False
                    if self.unenc_data[index]['visible'][2] == False:
                        if self.unenc_data[index]['enc_status'][2] == False:
                            widget.text = '(Password, decrypted)'
                        else:
                            widget.text = '(Password, encrypted)'
                else:
                    pass
        self.user_input = True

    def search(self, widget, search_text):
        if widget.focus == True:
            self.search_indexes = pg.search_bisect(self.unenc_data, search_text, 'name')
            if self.search_indexes == None:
                self.search_indexes = [-1, -1]
            self.update_entries()

    def copy(self, widget, field):
        index = widget.parent.index
        if field == 'name':
            text = self.unenc_data[index]['name']
        elif field == 'login':
            if self.unenc_data[index]['enc_status'][1] == False:
                text = self.unenc_data[index]['login']
            else:
                self.update_status_bar('Decrypting.')
                text = pg.decrypt(self.master_password, self.unenc_data[index]['login'])
                self.unenc_data[index]['enc_status'][1] == False
                self.update_status_bar('Copied to clipboard.')
                widget.parent.ids['login'].text = '(Login, decrypted)'
        elif field == 'password':
            if self.unenc_data[index]['enc_status'][2] == False:
                text =  self.unenc_data[index]['password']
            else:
                self.update_status_bar('Decrypting.')
                text = pg.decrypt(self.master_password, self.unenc_data[index]['password'])
                self.unenc_data[index]['enc_status'][2] == False
                self.update_status_bar('Copied to clipboard.')
                widget.parent.ids['password'].text = '(Password, decrypted)'
        else:
            text = ''
        widget.parent.ids[field].copy(data = text)



class PasuchanApp(App):

    def build(self):
        self.iw = InterfaceWidget()
        self.title = 'Pasu-chan v0.1'
        Clock.schedule_interval(self.iw.update, 0)
        return self.iw

if __name__ == '__main__':
    PasuchanApp().run()