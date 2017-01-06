try:
    from tkinter import *
except:
    from Tkinter import *
import pygubu

class main_GUI:
    """GUI for one-time setup."""
    def __init__(self, master):
        """Create GUI object using pygubu."""
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_from_file('setup.ui')
        self.top = builder.get_object('top', master)
        builder.connect_callbacks(self)
        self.top.protocol('WM_DELETE_WINDOW', self.on_close)
        root.withdraw()

    def go(self):
        """Write consumer key and consumer secret to file."""
        f = open('setup.txt', 'w')
        f.write(self.builder.get_object('k_entry').get())
        f.write('\n')
        f.write(self.builder.get_object('s_entry').get())
        f.close()
        self.master.destroy()

    def on_close(self):
        """Exit program when user closes GUI window."""
        self.master.destroy()

if __name__ == '__main__':
    root = Tk()
    gui = main_GUI(root)
    root.mainloop()

