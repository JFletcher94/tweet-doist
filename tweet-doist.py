from rule import *
import tweepy
import todoist
import time
import os
import glob
try:
    from tkinter import *
except:
    from Tkinter import *
import tkMessageBox
import pygubu
import logging 
import webbrowser
logging.basicConfig()

class main_GUI:
    """GUI for twitter-todoist app."""
    def __init__(self, master):
        """Create GUI object using pygubu."""
        self.master = master
        self.rules = []
        self.tw_logged_in = False
        self.td_logged_in = False
        self.builder = builder = pygubu.Builder()
        builder.add_from_file('tw-td.ui')
        self.login_top_level = builder.get_object('login_top_level', master)
        self.trigger_top_level = self.builder.get_object\
                ('trigger_top_level', self.master)
        self.login_top_level.protocol('WM_DELETE_WINDOW', self.on_close)
        self.trigger_top_level.protocol('WM_DELETE_WINDOW', self.on_close)
        builder.connect_callbacks(self)
        self.trigger_top_level.withdraw()
        root.withdraw()

    def td_login(self):
        """Login to todoist with username and password."""
        self.td_api = todoist.TodoistAPI()
        usrname = self.builder.get_object('td_email_entry').get()
        password = self.builder.get_object('td_password_entry').get()
        if 'error' in self.td_api.user.login(usrname, password):
            tkMessageBox.showwarning('Error', 'Login failed')
        else:
            self.builder.get_object('td_login_frame').destroy()
            try:
                self.builder.get_object('login_buffer_frame').destroy()
            except:
                pass
            self.td_logged_in = True
            self.check_login()

    def twitter_login(self):
        """
        Retreieve OAUth tokens from json file.
        Redirect user to generate tokens if none found.
        """
        keys = get_keys()
        auth = tweepy.OAuthHandler(keys[0], keys[1])
        slib = read_json('.tw_oauth_token.json')
        if not 'token' in slib or not 'secret' in slib:
            redirect_url = auth.get_authorization_url()
            webbrowser.open(redirect_url)
            self.builder.get_object('tw_url_button').destroy()
            self.ver_field = Entry(self.builder.get_object\
                    ('tw_login_frame'), width=8)
            self.ver_button = Button(self.builder.get_object\
                    ('tw_login_frame'), text='Go', command=lambda:\
                    self.twitter_verify(auth))
            self.ver_field.grid(row=3, column=0)
            self.ver_button.grid(row=4, column=0)
        else:
            auth.set_access_token(slib['token'], slib['secret'])
            self.twitter_login_final(auth)

    def twitter_verify(self, auth):
        """Generate OAuth tokens after user logs into twitter."""
        verifier = self.ver_field.get()
        auth.get_access_token(verifier)
        slib = {
                'token':auth.access_token, 
                'secret':auth.access_token_secret
                }
        write_json('.tw_oauth_token.json', slib)
        self.twitter_login_final(auth)

    def twitter_login_final(self, auth):
        """Use OAuth tokens to login to twitter."""
        self.tw_api = tweepy.API(auth)
        try:
            self.tw_api.me().screen_name
        except:
            tkMessageBox.showwarning('Error', 'Login failed')
            return
        self.builder.get_object('tw_login_frame').destroy()
        try:
            self.builder.get_object('login_buffer_frame').destroy()
        except:
            pass
        self.tw_logged_in = True
        self.check_login()

    def tw_logout(self):
        """Logout of twitter by deleting OAuth json file."""
        try:
            os.remove('.tw_oauth_token.json')
        except:
            pass

    def check_login(self):
        """
        Check if user has logged into both twitter and todoist.
        If the usser has, launch rule-curation window."""
        if self.tw_logged_in and self.td_logged_in:
            self.login_top_level.withdraw()
            self.trigger_top_level.deiconify()
            self.add_saved_rules()
    
    def add_saved_rules(self):
        """Add all rules saved in json/ directory"""
        fnames = glob.glob('json/*.json')
        for fname in fnames:
            self.rules.append(rule.from_file(fname, self.tw_api,\
                    self.td_api))
            self.builder.get_object('trigger_list_listbox').insert(END,\
                    self.rules[-1].get_string())
    
    def create_rule(self):
        """Create new rule using data provided by user."""
        try:
            r1 = self.builder.get_variable('trigger_tw_option').get()
            r2 = self.builder.get_object('trigger_tw_options_number_entry')\
                    .get()
            r3 = self.builder.get_variable('trigger_td_option').get()
            r4 = self.builder.get_object('trigger_td_text_entry').get()
            r5 = self.builder.get_object('trigger_td_datetime_entry').get()
            assert r1 == 'rt' or r1 == 'am'
            r2 = int(r2)
            assert r2 > 0 and r2 <= 100
            assert r3 == 'add'
            new_rule = rule(self.tw_api, self.td_api, r1, r2, r3, r4, r5)
            self.rules.append(new_rule)
            self.builder.get_object('trigger_list_listbox').insert(END,\
                    new_rule.get_string())
        except:
            tkMessageBox.showwarning('Error', 'Error formatting rule.' +\
                    '\nCheck Readme for formatting instructions')

    def remove_rule(self):
        """Delete rule(s) (including json file) selected in listbox."""
        if not tkMessageBox.askokcancel('Delete Rule?', 'Are you sure?'):
            return
        cs = self.builder.get_object('trigger_list_listbox').curselection()
        for i in reversed(cs):
            os.remove('json/' + str(self.rules[i].task_id) + '.json')
            del self.rules[i]
            self.builder.get_object('trigger_list_listbox').delete(i)

    def commit(self):
        """Close GUI and begin loop for checking/executing rules."""
        tkMessageBox.showinfo('Commit', 'Application now running.\n' +\
                'Use <Ctrl-C> to Quit')
        root.destroy()
        try:
            while True:
                for rule in self.rules:
                    rule.check_rule()
                time.sleep(1)
        except KeyboardInterrupt:
            print('\nQuitting')
        except:
            raise

    def on_close(self):
        """Exit program when user closes GUI window."""
        if tkMessageBox.askokcancel('Quit', 'Do you want to quit?'):
            self.master.destroy()

def get_keys():
    """
    Get consumer key and consumer secret from file.
    User must have already 'run setup.sh.'
    """
    try:
        f = open('setup.txt', 'r')
        text = f.readlines()
        f.close()
        return [text[0].rstrip(), text[1].rstrip()]
    except:
        tkMessageBox.showwarning('Error', 'Please see Readme for setup'+\
                'instructions')
        sys.exit()

if __name__ == '__main__':
    root = Tk()
    gui = main_GUI(root)
    root.mainloop()

