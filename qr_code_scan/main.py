from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.camera import Camera
import threading
import requests
import cv2
from pyzbar.pyzbar import decode

class QRCodeApp(App):

    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        
        # Camera view occupying 80% of the screen
        self.camera = Camera(play=True)
        self.camera.size = (self.camera.resolution[0], self.camera.resolution[1])
        self.layout.add_widget(self.camera)
        
        # Label to display scanned data
        self.label = Label(size_hint_y=0.1, text='Scan a QR Code')
        self.layout.add_widget(self.label)
        
        # Button occupying 20% of the screen
        self.button = Button(size_hint_y=0.1, text='Scan')
        self.button.bind(on_press=self.scan_qr_code)
        self.layout.add_widget(self.button)
        
        return self.layout

    def scan_qr_code(self, instance):
        # Start a new thread to handle the QR code scanning and HTTP POST request
        threading.Thread(target=self.scanning_process).start()

    def scanning_process(self):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite('qrcode.jpg', frame)
            self.scan_with_opencv('qrcode.jpg')
        cap.release()

    def scan_with_opencv(self, filepath):
        # Read the image file
        img = cv2.imread(filepath)

        # Decode the barcode
        decoded_objects = decode(img)

        if decoded_objects:
            # Get the first detected barcode
            result = decoded_objects[0].data.decode('utf-8')
            self.label.text = f"Scanned Data: {result}"

            # Make the HTTP POST request
            response = requests.post('https://mojedelo.scripter.si/api/', data={'USER_ID': result})
            self.label.text += f"\nResponse: {response.text}"
        else:
            self.label.text = "Scan failed. Try again."

if __name__ == '__main__':
    QRCodeApp().run()
