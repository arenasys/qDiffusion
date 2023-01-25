import os
import glob
import importlib

from PyQt5.QtCore import pyqtProperty, QObject

class GUI(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.tabs = []
    
    def register_tabs(self, tabs):
        self.tabs = tabs

    @pyqtProperty(list, constant=True)
    def tab_sources(self):
        return [tab.source for tab in self.tabs]

    @pyqtProperty(list, constant=True)
    def tab_names(self): 
        return [tab.name for tab in self.tabs]

    @pyqtProperty('QString', constant=True)
    def title(self):
        return "SD Inference GUI"