import string
import sys
import time
import os
import tweepy
import todoist
import json

class rule:
    """
    Single rule for writing todoist task based on twitter.
    Every rule object has corresponding json file in json/ directory
    """
    def __init__(self, tw_api, td_api, tw_option, tw_threshold, td_option,\
            td_task, td_datestring, task_id=-1, since_id=1):
        """Create rule object using given information"""
        self.tw_api = tw_api
        self.td_api = td_api
        self.tw_option = tw_option
        self.tw_threshold = tw_threshold
        self.td_option = td_option
        self.td_task = td_task
        self.td_datestring = td_datestring
        self.task_id = task_id
        self.since_id = since_id
        if task_id == -1:
            self.init_task()
    
    @classmethod
    def from_file(cls, fname, tw_api, td_api):
        """Return rule object using json file."""
        slib = deser_json(fname)
        tw_option = slib['tw_option']
        tw_threshold = slib['tw_threshold']
        td_option = slib['td_option']
        td_task = slib['td_task']
        td_datestring = slib['td_datestring']
        task_id = slib['task_id']
        since_id = slib['since_id']
        return cls(tw_api, td_api, tw_option, tw_threshold, td_option,\
                td_task, td_datestring, task_id=task_id, since_id=since_id)

    def init_task(self):
        """
        Create task to receive task_id.
        Unique task_id value necessary for serialization.
        """
        item = self.td_api.items.add('', 0)
        item.complete()
        self.td_api.commit()
        time.sleep(1)
        self.task_id = item['id']
        self.ser_json()

    def get_retweets(self):
        """
        Return list of tweet objects of length [0, tw_threshold].
        List contains only retweets of user.
        """
        return self.tw_api.retweets_of_me(count=self.tw_threshold)

    def get_mentions(self):
        """
        Return list of tweet objects of length [0, tw_threshold].
        List contains only @ mentions of user.
        """
        query = '@' + self.tw_api.me().screen_name
        query += ' -filter:retweets'
        return self.tw_api.search(q=query, count=self.tw_threshold)

    def go_task(self):
        """Create task in todoist and update json file."""
        self.td_api.sync()
        item = self.td_api.items.get_by_id(self.task_id)
        if item['checked'] == 1:
            item.update(content=self.td_task, datestring=self.td_datestring)
            item.uncomplete()
        self.td_api.commit()
        self.ser_json()

    def check_rule(self):
        """Check if conditions for creating new task have been met."""
        tweets = []
        if self.tw_option == 'rt':
            tweets = self.get_retweets()
        elif self.tw_option == 'am':
            tweets = self.get_mentions()
        if len(tweets) >= self.tw_threshold and tweets[-1].id >\
                self.since_id:
            self.since_id = tweets[0].id    
            self.go_task()

    def get_string(self):
        """Return short string containing basic information about rule."""
        return str(self.tw_threshold) + '+ ' + self.tw_option + '\'s -> ' +\
                self.td_task + '; ' + self.td_datestring

    def ser_json(self):
        """serialize rule object as json file."""
        slib = {
                'tw_option':  self.tw_option,
                'tw_threshold': self.tw_threshold,
                'td_option': self.td_option,
                'td_task': self.td_task,
                'td_datestring': self.td_datestring,
                'since_id': self.since_id,
                'task_id': self.task_id
                }
        try:
            os.mkdir('json/')
        except:
            pass
        write_json('json/' + str(self.task_id) + '.json', slib)

def deser_json(fname):
    """Return dictionary with object data from json file."""
    return read_json(fname)

def read_json(fname, default='{"0":"0"}'):
    """Return dictionary from json file."""
    text = default
    while True:
        try:
            fin = open(fname, 'r')
            text = fin.read()
            fin.close()
            break
        except IOError:
            fin = open(fname, 'w')
            fin.write(default)
            fin.close()
    return u_to_ascii(json.loads(text, object_hook=u_to_ascii)) 

def write_json(fname, slib):
    """Write dictionary to json file."""
    j = json.dumps(slib, indent=4)
    f = open(fname, 'w')
    f.write(j)
    f.close()

def u_to_ascii(data):
    """Convert uncode to (ascii) str.
       Use recursion to convert nested lists and dicts."""
    if isinstance(data, unicode):
        return data.encode('ascii', 'ignore')
    if isinstance(data, list):
        return [u_to_ascii(item) for item in data]
    if isinstance(data, dict):
        return {
                u_to_ascii(k): u_to_ascii(v) for k, v in data.iteritems()
                }
    return data








