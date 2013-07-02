# -----------------------------------------------------------------------------------
# AUTHOR:     Danny Wynne
#             wynne100@gmail.com
#			  www.dannywynne.com
# -----------------------------------------------------------------------------------

'''
USAGE:
import mayauify.dw_uify_example as uify_example
'''

from PyQt4 import QtGui, QtCore, uic
import sip
import maya.OpenMaya as om
import maya.OpenMayaUI as mui
import maya.cmds as cmds
import os, functools

import dw_uify_widget as uify_widget
reload(uify_widget)

#get maya window as qt object
main_window_ptr = mui.MQtUtil.mainWindow()
qt_maya_window = sip.wrapinstance(long(main_window_ptr), QtCore.QObject)

user_maya_dir = os.getenv("MAYA_APP_DIR")
ui_file = os.path.normpath(os.path.join(user_maya_dir, r"scripts\uify\dw_uify_example.ui"))
form_class, base_class = uic.loadUiType(ui_file)

class UifyExample(base_class, form_class):
	def __init__(self, parent = qt_maya_window):
		super(base_class, self).__init__(parent)
		self.setupUi(self)
		self.setWindowTitle("Uify Example")
		self.uify = uify_widget.Uify(self)
		self.verticalLayout.addWidget(self.uify)
		
		self.uify.clicked.connect(self.uify_clicked)
		self.pushButton.clicked.connect(self.load_selected)
		
	def uify_clicked(self, event):
		print event.pos
		if event.click == 0:
			cmds.select(event.path)
		if event.click == 1:
			print "you shift clicked %s "% event.label
		if event.click == 2:
			self.context_menu(event)
			
	def context_menu(self, event):
		menu = QtGui.QMenu(self.uify)
		menu.addAction("do something", functools.partial(self.do_something, event.path))
		menu.popup(self.uify.mapToGlobal(event.pos))
		
	def do_something(self, path):
		print "do something with ", path
		self.uify.release()
		
	def load_selected(self):
		sel = cmds.ls(sl=1)
		self.uify.set_items(sel)
		
def main():
	global uify_example
	try: uify_example.close()
	except:pass
	uify_example = UifyExample()
	uify_example.show()
main()