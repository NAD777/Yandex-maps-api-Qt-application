# -*- coding: utf-8 -*-
import os
import sys

import requests
from PyQt5 import uic, QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow

import math

SCREEN_SIZE = [600, 450]


# 52.727525, 41.456136
class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)
        # self.y, self.x = input().split(", ")
        self.point_x, self.point_y = None, None
        self.y, self.x = 52.727525, 41.456136

        self.z = 14

        self.setWindowTitle('Отображение карты')

        self.type_map = ["map", "sat", "sat,skl"]
        self.type_iter = 0

        self.refresh()

        self.find_btn.clicked.connect(self.find_func)
        self.reset.clicked.connect(self.reset_func)
        self.post_code.clicked.connect(self.post_code_func)

        self.show_post_code = True

        self.post_index = ""

    def post_code_func(self):
        self.show_post_code = not self.show_post_code
        if self.show_post_code:
            self.label_addres.setText(self.label_addres.text() + ' ' + self.post_index)
            self.post_code.setStyleSheet('background-color: green;color:white;')
        else:
            self.post_code.setStyleSheet('')
            self.label_addres.setText(self.label_addres.text()[:-len(self.post_index) - 1])
        self.update()

    def find_func(self):
        text = self.addres.text()
        self.x, self.y = self.get_coords(text)
        self.point_x, self.point_y = self.x, self.y
        self.refresh()
        self.image.setFocus()
        self.update()
    
    def reset_func(self):
        self.point_x, self.point_y = None, None
        self.label_addres.setText("")
        self.post_index = ''
        self.refresh()

    def get_coords(self, place):
        url = "http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b"
        params = {
            "geocode": f"{place}",
            "format": "json"
        }
        response = requests.get(url=url, params=params)
        # print(response.json())
        obj = response.json()["response"]["GeoObjectCollection"]["featureMember"][0]
        # print(obj)
        try:
            self.post_index = obj["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
        except KeyError:
            self.post_index = ""
        print(self.post_index)
        self.label_addres.setText(obj["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"] + ' ' + self.post_index)
        x, y = obj["GeoObject"]["Point"]["pos"].split()
        return x, y

    def getImage(self, x, y):
        map_request = "http://static-maps.yandex.ru/1.x/"
        params = {
            "ll": f"{x},{y}",
            "l": self.type_map[self.type_iter],
            "z": f"{self.z}"

        }
        if self.point_x is not None:
            params["pt"] = f"{self.point_x},{self.point_y},pm2rdm"
        response = requests.get(map_request, params=params)

        if not response:
            print("Ошибка выполнения запроса:")
            print(map_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)

        # Запишем полученное изображение в файл.
        self.map_file = "map.png"
        with open(self.map_file, "wb") as file:
            file.write(response.content)

    def set_image(self):
        # self.getImage(self.x, self.y)
        self.pixmap = QPixmap(self.map_file)
        self.image.setPixmap(self.pixmap)
        self.update()

    def refresh(self):
        self.getImage(self.x, self.y)
        self.set_image()
        self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            self.type_iter = (self.type_iter + 1) % len(self.type_map) 
        if event.key() == QtCore.Qt.Key_Comma:  # < btn
            if self.z < 17:
                self.z += 1

        if event.key() == QtCore.Qt.Key_Period:  # > btn
            if self.z > 1:
                self.z -= 1

        if event.key() == QtCore.Qt.Key_Left:
            move_x = 360 / (2 ** (self.z + 8)) * 575
            if float(self.x) - move_x >= -180:
                self.x = str(float(self.x) - move_x)

        if event.key() == QtCore.Qt.Key_Right:
            move_x = 360 / (2 ** (self.z + 8)) * 575
            if float(self.x) + move_x <= 180:
                self.x = str(float(self.x) + move_x)
        
        if event.key() == QtCore.Qt.Key_Up:
            move_y = math.cos(math.radians(float(self.y))) * 180 / (2 ** (self.z + 8)) * 800
            if float(self.y) + move_y <= 180:
                self.y = str(float(self.y) + move_y)

        if event.key() == QtCore.Qt.Key_Down:
            move_y = math.cos(math.radians(float(self.y))) * 180 / (2 ** (self.z + 8)) * 800
            if float(self.y) - move_y >= -180:
                self.y = str(float(self.y) - move_y)
        
        self.refresh()

    def closeEvent(self, event):
        """При закрытии формы подчищаем за собой"""
        os.remove(self.map_file)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
