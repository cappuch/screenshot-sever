import sys
import os
import requests
import pyperclip
import mss
import mss.tools
from PyQt5.QtWidgets import QApplication, QRubberBand, QWidget
from PyQt5.QtCore import QRect, QPoint, Qt, QSize
import time
import yaml

config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

        if 'auth_token' in config:
            AUTH_KEY = config['auth_token']
            print('auth_token loaded from config file')
        else:
            quit('No auth_token found in config file')
            
        if 'upload_url' in config:
            UPLOAD_URL = config['upload_url']
            print('upload_url loaded from config file')
        else:
            quit('No upload_url found in config file')

class ScreenshotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.7)
        geo = QApplication.primaryScreen().geometry()
        self.setGeometry(geo)
        
        self.origin = QPoint()
        self.current_pos = QPoint()
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.show()

    def mousePressEvent(self, event):
        global_pos = self.mapToGlobal(event.pos())
        self.origin = global_pos
        self.current_pos = global_pos
        local_pos = event.pos()
        self.rubberBand.setGeometry(QRect(local_pos, QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        self.current_pos = self.mapToGlobal(event.pos())
        rect = QRect(self.mapFromGlobal(self.origin), event.pos()).normalized()
        self.rubberBand.setGeometry(rect)

    def mouseReleaseEvent(self, event):
        self.rubberBand.hide()
        self.current_pos = self.mapToGlobal(event.pos())

        x1, x2 = sorted([self.origin.x(), self.current_pos.x()])
        y1, y2 = sorted([self.origin.y(), self.current_pos.y()])
        width = x2 - x1
        height = y2 - y1

        if width < 32 or height < 32:
            self.close()
            QApplication.instance().quit()
            return
        self.hide()

        QApplication.processEvents()

        time.sleep(0.2)
        with mss.mss() as sct:
            monitor = {'top': y1, 'left': x1, 'width': width, 'height': height}
            sct_img = sct.grab(monitor)
            temp_path = os.path.join(os.path.dirname(__file__), 'screenshot.png')
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=temp_path)
            upload_and_copy(temp_path)
            os.remove(temp_path)
            QApplication.instance().quit()
        self.close()


def upload_and_copy(filepath):
    headers = {'Authorization': AUTH_KEY}
    with open(filepath, 'rb') as f:
        files = {'file': f}
        response = requests.post(UPLOAD_URL, headers=headers, files=files)
    if response.status_code == 200:
        file_link = response.json().get('url')
        pyperclip.copy(file_link)
    else:
        print('Upload failed:', response.text)

def main():
    app = QApplication(sys.argv)
    window = ScreenshotWidget()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
