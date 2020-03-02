# -*- coding: utf-8 -*-
import os
import sys
import requests
from PyQt5 import uic, QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt

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
        self.ras_map = ["map.png", "map.jpg", "map.jpg"]
        self.type_iter = 0

        self.refresh()

        self.find_btn.clicked.connect(lambda: self.find_func(self.addres.text()))
        self.reset.clicked.connect(self.reset_func)
        self.post_code.stateChanged.connect(self.post_code_func)

        self.show_post_code = True

        self.post_index = ""

    def mousePressEvent(self, event):
        dy = 30
        x_cur = event.pos().x() 
        y_cur = event.pos().y() 
        if 0 <= x_cur < 600 and dy <= y_cur < 450 + dy: 
            if event.buttons() == Qt.LeftButton:
                x = (x_cur - 300) * 360 / 2 ** (self.z + 8) 
                y = (y_cur - dy - 225) * 230 / 2 ** (self.z + 8) 
                self.x = float(self.x) + x 
                self.y = float(self.y) - y
                print("!!!!: ", self.x, self.y)
                self.point_x, self.point_y = self.x, self.y
                self.get_coords(f"{self.x},{self.y}")
                self.getImage(self.x, self.y)
                self.set_image()
                self.update()
            elif event.buttons() == Qt.RightButton:
                x = (x_cur - 300) * 360 / 2 ** (self.z + 8) 
                y = (y_cur - dy - 225) * 230 / 2 ** (self.z + 8) 
                new_x, new_y, text = self.get_nearby(self.x + x, self.y - y)
                # print(new_x, new_y, text)
                if new_x is not None:
                    self.x, self.y = new_x, new_y
                    self.point_x, self.point_y = self.x, self.y
                    
                    # company["properties"]["name"]
                    self.get_coords(f"{self.x},{self.y}")
                    self.getImage(self.x, self.y)
                    if self.post_code.isChecked():
                        self.label_addres.setText(text)
                        self.post_code_func()
                    else:
                        self.label_addres.setText(text)
                        self.post_code_func()

                    self.set_image()
                    self.update()

    def get_nearby(self, x, y):

        url = "http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b"
        params = {
            "geocode": f"{x,y}",
            "format": "json"
        }
        response = requests.get(url=url, params=params)

        address = response.json()["response"]["GeoObjectCollection"]["featureMember"][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']

        search_api_server = "https://search-maps.yandex.ru/v1/"
        api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
        
        search_params = {
            "apikey": api_key,
            "text": f"{address}",
            "lang": "ru_RU",
            "results": 10,
            # "ll": f"{y},{x}",
            "type": "biz",
            "spn": "0.001,0.001"
        }
        response = requests.get(search_api_server, params=search_params).json()
        # print(response)
        for company in response["features"]:
            x_comp, y_comp = company["geometry"]["coordinates"]
            if self.lonlat_distance((x, y), (x_comp, y_comp)) <= 50:
                # print("get:", x_comp, y_comp)
                # print()
                
                return x_comp, y_comp, company["properties"]["name"]
        return None, None, None

    def lonlat_distance(self, a, b):
        degree_to_meters_factor = 111 * 1000  # 111 километров в метрах
        a_lon, a_lat = a
        b_lon, b_lat = b

        # Берем среднюю по широте точку и считаем коэффициент для нее.
        radians_lattitude = math.radians((a_lat + b_lat) / 2.)
        lat_lon_factor = math.cos(radians_lattitude)

        # Вычисляем смещения в метрах по вертикали и горизонтали.
        dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
        dy = abs(a_lat - b_lat) * degree_to_meters_factor

        # Вычисляем расстояние между точками.
        distance = math.sqrt(dx * dx + dy * dy)

        return distance

    def post_code_func(self):
        if self.post_code.isChecked():
            self.label_addres.setText(self.label_addres.text() + ' ' + self.post_index)
        else:
            if self.label_addres.text().endswith(self.post_index):
                self.label_addres.setText(self.label_addres.text()[:-len(self.post_index) - 2])
        self.update()

    def find_func(self, text):
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
        # print(self.post_index)
        self.label_addres.setText(obj["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"] + ' ')
        self.post_code_func()
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
        self.map_file = self.ras_map[self.type_iter]
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
