# -----------------------------------------------------------------------------------
# AUTHOR:     Danny Wynne
#             wynne100@gmail.com
#			  www.dannywynne.com
# -----------------------------------------------------------------------------------

from PyQt4 import QtGui, QtCore, uic
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import os

class UifyEvent(object):
	def __init__(self):
		self.click = None #int, 0 - left click, 1 - right click, 2 - ctrl + click
		self.pos = None #QtCore.QPoint
		self.name = None
		self.path = None #str maya dag path

class Uify(QtGui.QWidget):
	'''
	project maya transform nodes onto a 2d widget for easy access
	'''
	
	clicked = QtCore.pyqtSignal(UifyEvent)
	
	def __init__(self, parent = None, maya_transform_nodes = []):
		super(QtGui.QWidget, self).__init__(parent)
		#self.setupUi(self)
		self.setMinimumWidth(300)
		self.setMinimumHeight(300)
		self.setStyleSheet("border:1px solid rgb(0, 255, 0); ")
		self.items = []
			
		self.transform_move = QtGui.QTransform()
		self.transform_scale = QtGui.QTransform()
		
		self.prev_mouse_pos = QtCore.QPoint(0,0)
		
		self.color = QtGui.QColor(0,255,50,50)
		self.clicked_color = QtGui.QColor(0,255,50,150)
		self.right_clicked_color = QtGui.QColor(255, 0, 0, 150)
	
		if maya_transform_nodes:
			self.set_items(maya_transform_nodes, projection_vector)
			
	def set_items(self, maya_transform_nodes):
		'''
		convert the 3d transforms to 2d space. by default, projects down the z axis
		'''
		
		self.items = []
		
		view = omui.M3dView.active3dView()
		view_matrix = om.MMatrix()
		proj_matrix = om.MMatrix()
		view.modelViewMatrix(view_matrix)
		view.projectionMatrix(proj_matrix)
		
		pnts = []
		for path in maya_transform_nodes:
			pnt = om.MPoint(*cmds.xform(path, piv=1,ws=1,q=1)[:3])
			pnt = pnt*view_matrix*proj_matrix
			pnts.append(pnt)
			pnts[-1].label = short_name(path)
			pnts[-1].path = path
		
		x_min, x_max, y_min, y_max = pnts[0].x, pnts[0].x, pnts[0].y, pnts[0].y
		for p in pnts[1:]:
			if p.x < x_min: x_min = p.x
			if p.x > x_max: x_max = p.x
			if p.y < y_min: y_min = p.y
			if p.y > y_min: y_max = p.y
		if x_max - x_min < .01:
			x_max = 100
		if y_max - y_min < .01:
			y_max = 100
		canvas_width, canvas_height = 300, 300
		width, height = x_max - x_min, y_max - y_min
		width_scale, height_scale = 1.0, 1.0
		width_padding, height_padding = 30, 30
		if width > height:
			height_scale = height/float(width)
		if height>width:
			width_scale = width/float(height)
		remap_width = canvas_width*width_scale
		remap_height = canvas_height*height_scale
		if remap_width - width_padding < width_padding:
			remap_width += width_padding*2
		if remap_height - height_padding < height_padding:
			remap_height += height_padding*2
		for p in pnts:
			p.x = remap_range(p.x, x_min, x_max, width_padding, remap_width-width_padding)
			p.y = (remap_range(p.y, y_min, y_max, height_padding, remap_height-height_padding)*-1)+300
			p.z = 0.0
		for i in range(3):
			fix_collision(pnts, 30)
		for p in pnts:
			rect = QtCore.QRectF(QtCore.QPointF(p.x-10, p.y-10), QtCore.QPointF(p.x+10, p.y+10))
			self.items.append({"origin_rect": rect, "transformed_rect":rect, "label":p.label, "path": p.path, "right_clicked":False, "clicked":False})
		self.reset_transforms()
		self.update_items()
		self.update()
		
	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		brush = QtGui.QBrush(1)
		rect = event.rect()
		rect.adjust(0,0,-1,-1)
		painter.drawRect(rect)
		painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 255)))
		for i in self.items:
			color = self.color
			if i["right_clicked"]:
				color = self.right_clicked_color
			if i["clicked"]:
				color = self.clicked_color
			brush.setColor(color)
			painter.setBrush(brush)
			painter.drawRect(i["transformed_rect"])
			font = QtGui.QFont()
			font.setPointSize(7)
			painter.setFont(font)
			painter.drawText(i["transformed_rect"].bottomRight()+QtCore.QPointF(5,5), i["label"])
			
	def reset_transforms(self):
		self.transform_scale.reset()
		self.transform_move.reset()
		
	def update_items(self):
		for i in self.items:
			trans = self.transform_scale * self.transform_move
			i["transformed_rect"] = trans.mapRect(i["origin_rect"])
			
	def reset_click_states(self):
		for i in self.items:
			i["right_clicked"] = False
			i["clicked"] = False
		self.update()
		
	def mousePressEvent(self, event):
		#modifiers:
		#shift - 33554432
		#ctrl - 67108864
		#alt - 134217728
		self.reset_click_states()
		uify_event = UifyEvent()
		uify_event.pos = event.pos()
		for i in self.items:
			if i["transformed_rect"].contains(QtCore.QPointF(event.pos())):
				uify_event.path = i["path"]
				uify_event.name = i["label"]
				if int(event.modifiers()) == 33554432:
					uify_event.click = 1
					self.clicked.emit(uify_event)
					i["clicked"] = True
				elif event.button() == 2:
					uify_event.click = 2
					self.clicked.emit(uify_event)
					i["right_clicked"] = True
				else:
					uify_event.click = 0
					self.clicked.emit(uify_event)
					i["clicked"] = True
		self.update()
		self.setMouseTracking(True)
		self.prev_mouse_pos = event.pos()
		
	def mouseReleaseEvent(self, event):
		self.release()
		
	def mouseMoveEvent(self, event):
		move = event.pos() - self.prev_mouse_pos
		self.prev_mouse_pos = event.pos()
		
		self.transform_move.translate(move.x(), move.y())
		
		self.update_items()
		self.update()
		
	def release(self):
		self.setMouseTracking(False)
		self.reset_click_states()
		self.update()
		
	def wheelEvent(self, event):
		if event.delta()>0:
			self.transform_scale.scale(1.1, 1.1)
		if event.delta()<0:
			self.transform_scale.scale(.9, .9)
		
		self.update_items()
		self.update()
	
def short_name(name):
	return name.rpartition(":")[2].rpartition("|")[2]
	
def fix_collision(pnts, radius = 2):
	for pa in pnts:
		for pb in pnts:
			if id(pa) == id(pb): continue
			if pa.distanceTo(pb) < radius:
				res = push_out(pa, pb, radius)
				pb.x, pb.y = res.x, res.y
				
def push_out(pa, pb, radius = 2):
	if pa.distanceTo(pb) < .0001:
		vec = om.MVector(-1, -1)
	else:
		vec = pb - pa
	vec = om.MVector(-1, -1)
	vec.normalize()
	vec = vec*radius
	return pa+vec

def remap_range(value, min, max, new_min, new_max):
	span = max - min
	new_span = new_max - new_min
	if span < .00001:
		return value
	value_scaled = float(value-min)/float(span)
	return new_min + (value_scaled * new_span)
		
			
			
		
		