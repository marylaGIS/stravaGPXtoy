"""
stravaGPXtoy

QGIS plugin for uploading and modifying .gpx data,
that comes from bike traces recorded with Strava.

    begin                : 2021-04-21
    copyright            : (C) 2021 by marylaGIS
    email                : marylaGISdev@gmail.com
"""

import os

from qgis.core import *
from qgis.gui import *

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *

from .resources import *


class stravaGPXtoy:

    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.loadGpx = QAction(QIcon(":/plugins/stravaGPXtoy/icon1.png"), "Load GPX", self.iface.mainWindow())
        self.loadGpx.triggered.connect(self.onRun)
        self.iface.addToolBarIcon(self.loadGpx)
        self.iface.addPluginToMenu("Strava GPX Toy", self.loadGpx)

        self.styleLyrs = QAction(QIcon(":/plugins/stravaGPXtoy/icon2.png"), "Style layers with Strava color theme", self.iface.mainWindow())
        self.styleLyrs.triggered.connect(self.onStyle)
        self.iface.addPluginToMenu("Strava GPX Toy", self.styleLyrs)

        self.deleteFields = QAction(QIcon(":/plugins/stravaGPXtoy/icon3.png"), "Delete pre-specified fileds from track_points", self.iface.mainWindow())
        self.deleteFields.triggered.connect(self.onDelete)
        self.iface.addPluginToMenu("Strava GPX Toy", self.deleteFields)

    def unload(self):
        self.iface.removePluginMenu("Strava GPX Toy", self.loadGpx)
        self.iface.removeToolBarIcon(self.loadGpx)

        self.iface.removePluginMenu("Strava GPX Toy", self.styleLyrs)
        self.iface.removeToolBarIcon(self.styleLyrs)

        self.iface.removePluginMenu("Strava GPX Toy", self.deleteFields)
        self.iface.removeToolBarIcon(self.deleteFields)

    def onRun(self):
        folder_path = QFileDialog.getExistingDirectory(self.iface.mainWindow(),'Chose a folder with .gpx files')
        if folder_path == "":
            return
        path = folder_path.replace("/", "\\")


        qgi = QInputDialog()
        title = "Importing gpx data"
        label = "Select which part of gpx files you want to import:"
        items = ["tracks", "track_points", "tracks and track_points"]
        current = 0
        editable = False
        item, ok = QInputDialog().getItem(qgi, title, label, items, current, editable)

        choice = []        
        if item == "tracks and track_points" and ok:
            choice.append("tracks")
            choice.append("track_points")
            print(item)
            print(choice)
        elif ok:
            choice.append(item)
        else:
            return


        progressMessageBar = self.iface.messageBar().createMessage("Files importing progress...")
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
        
        progressValue = 0
        for dirpath, subdirs, files in os.walk(path):
            if len(files) == 0:
                self.iface.messageBar().clearWidgets()
            else:
                stepValue = 100/len(files)
            for f in files:
                if f.endswith('.gpx'):
                    for i in choice:
                        self.iface.addVectorLayer(os.path.join(dirpath, f)+"|layername="+i, f[:-4], "ogr")
                    progressValue += stepValue
                    progress.setValue(progressValue)
                else:
                    continue
                

        layerList = QgsProject.instance().mapLayers().values()
        for layer in layerList:
            basename = layer.name()
            layer.setName(basename.replace(" ","_"))

        self.iface.messageBar().clearWidgets()
        self.iface.messageBar().pushMessage("Success", "GPX files imported.", level=Qgis.Success)
        

    def onStyle(self):
        for layer in QgsProject.instance().mapLayers().values():
            try:
                if layer.geometryType() == 0:
                    pointSymbol = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': '#fc4d02', 'outline_width': '0.05'})
                    renderer = QgsSingleSymbolRenderer(pointSymbol)
                    layer.setRenderer(renderer)
                    layer.triggerRepaint()
                elif layer.geometryType() == 1:
                    lineSymbol = QgsLineSymbol.createSimple({'color': '#fc4d02'})
                    renderer = QgsSingleSymbolRenderer(lineSymbol)
                    layer.setRenderer(renderer)
                    layer.triggerRepaint()
            except:
                self.iface.messageBar().pushMessage("Warning", "The project contains other layers that can't be styled with Strava theme.", level=Qgis.Warning)
                continue


    def onDelete(self):
        attr_name_list = ['magvar', 'geoidheight', 'name', \
                          'cmt', 'desc', 'src', 'link1_href', 'link1_text',\
                          'link1_type', 'link2_href', 'link2_text',\
                          'link2_type', 'sym', 'type', 'fix', 'sat', 'hdop',\
                          'vdop', 'pdop', 'ageofdgpsdata', 'dgpsid']
        attr_idx_list = []
        
        layerList = QgsProject.instance().mapLayers().values()
        for layer in layerList:
            try:
                if layer.geometryType() == 0:
                    for i in attr_name_list:
                        attr_idx = layer.fields().indexFromName(i)
                        attr_idx_list.append(attr_idx)
                    layer.dataProvider().deleteAttributes(attr_idx_list)
                    layer.updateFields()
                else:
                    self.iface.messageBar().pushMessage("Works only for track points layers.", Qgis.Warning, -1)
            except:
                self.iface.messageBar().pushMessage("GPX layers must be stored in editable vector format.", Qgis.Warning, -1)
