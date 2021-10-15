import sqlite3
import sys
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QTableWidgetItem
from PyQt5.uic import loadUi
from twilio.rest import Client
import cv2
import pytesseract
import imutils
import random
from imutils.video import VideoStream
import time
import serial
from time import sleep
from PyQt5 import QtWidgets, QtGui
from playsound import playsound


class MainDialog(QMainWindow):
    def __init__(self):
        super(MainDialog,self).__init__()
        loadUi('layout.ui',self)


        self.plate_no = 0

        self.frame = None
        self.cap =None
        self.startButton.clicked.connect(self.start_webcam)
        self.load.clicked.connect(self.loadLog)
        self.addUser.clicked.connect(self.AddUser)
        self.updateUser.clicked.connect(self.UpdateUser)
        self.delUser.clicked.connect(self.DeleteUser)
        self.find.clicked.connect(self.FindUser)
        self.refresh.clicked.connect(self.loadCarStatus)
        # Initialize license Plate contour and x,y coordinates
        self.contour_with_license_plate = None
        self.license_plate = None
        self.x = 1
        self.y = 1
        self.w = 1
        self.h = 1
        #self.dev = serial.Serial('COM5', 9600, timeout=1)   ## open serial port


    def start_webcam(self): ## function  of start button
        self.cap = cv2.VideoCapture(0)
        #self.cap = cv2.VideoCapture('rtsp://admin:INVENT123@192.168.1.64/1')
        #self.cap = cv2.VideoCapture('rtsp://admin:INVENT123@192.168.1.64:554/videoMain')
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(300)
        self.timer4=QTimer(self)

    def update_frame(self):
        ret, self.frame = self.cap.read()
        if ret == True:
            self.frame =cv2.resize(self.frame,(550,400))
            img=self.frame.copy()
            self.detected_image = self.get_no(img)

            self.displayImage(self.detected_image)

    def get_no(self, img):
              # Convert to Grayscale Image
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        #Canny Edge Detection
        canny_edge = cv2.Canny(gray_image,30,200)

        # Find contours based on Edges
        contours, new  = cv2.findContours(canny_edge.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours=sorted(contours, key = cv2.contourArea, reverse = True)[:10]
        #self.displyimage2(canny_edge)

        # Find the contour with 4 potential corners and creat ROI around it
        for contour in contours:
                # Find Perimeter of contour and it should be a closed contour
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)
                if len(approx) == 4: #see whether it is a Rect
                    contour_with_license_plate = approx
                    self.x, self.y, self.w, self.h = cv2.boundingRect(contour_with_license_plate)
                    license_plate = gray_image[self.y: self.y + self.h, self.x: self.x + self.w]
                    # Removing Noise from the detected image, before sending to Tesseract
                    license_plate = cv2.bilateralFilter(license_plate, 11, 17, 17)
                    #(thresh, license_plate) = cv2.threshold(license_plate, 150, 180, cv2.THRESH_BINARY)

                    #Text Recognition
                    text = pytesseract.image_to_string(license_plate)
                    #remove any wrong chracters and keep only numbers
                    tex=[]
                    for i in  text:
                        if i in ['0','1','2','3','4','5','6','7','8','9'] :
                            tex.append(i)
                        text= ''.join([str(elem) for elem in tex])
                    if len(text) != 0:
                        #self.timer.stop()
                        print("License Plate :", text)
                        self.plate_no = int(text)
                        self.displyimage2(canny_edge)
                        self.insertlog(text,img[self.y: self.y + self.h, self.x: self.x + self.w])

                        self.checkandSendSMS(text)
                        # #Draw License Plate and write the Text
                        img = cv2.rectangle(img, (self.x,self.y), (self.x+self.w,self.y+self.h), (0,0,255), 3)
                        #img = cv2.putText(img, text, (self.x-100,self.y-50), cv2.FONT_HERSHEY_SIMPLEX, 3, (0,255,0), 6, cv2.LINE_AA)
                        return img
        return img

    def loadCarStatus(self):
        db = sqlite3.connect('plateRecogDB.db')
        cursor = db
        command = '''SELECT * FROM users'''

        result = cursor.execute(command)

        ### to Fill table with result
        self.table2.setRowCount(0)
        for row_number, row_data in enumerate(result):
            self.table2.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.table2.setItem(row_number, column_number, QTableWidgetItem(str(data)))

    def loadLog(self):
        format = "yyyy MM dd hh mm ss";
        db = sqlite3.connect('plateRecogDB.db')
        cursor = db
        command = '''SELECT * FROM log WHERE time BETWEEN ? AND ? ORDER BY time DESC '''
        row= (self.fromTime.dateTime().toString(format),self.toTime.dateTime().toString(format))
        result = cursor.execute(command,row)

        ### to Fill table with result
        self.table.setRowCount(0)
        for row_number, row_data in enumerate(result):
            self.table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                if(column_number==2):
                    item=self.getImageLable(data)
                    self.table.setCellWidget(row_number,column_number,item)
                else :
                    self.table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        self.table.verticalHeader().setDefaultSectionSize(40)

    def getImageLable(self,imName):
        imageLabel =QtWidgets.QLabel(self.log)
        imageLabel.setText("aa")
        imageLabel.setScaledContents(True)
        #pixmap = QtGui.QPixmap("2020 11 16 17 26 04.jpg")
        imagename =str("photos\{0}.jpg".format(str(imName)))
        pixmap = QtGui.QPixmap(str("photos\{0}.jpg".format(imName)))

        #pixmap.loadFromData(image,'jpg')
        imageLabel.setPixmap(pixmap)
        return imageLabel


    def insertlog(self, text,img):
        time_ = str(time.strftime("%Y %m %d %H %M %S"))
        filename = time_.replace(':', ' ')
        cv2.imwrite("photos\{0}.jpg".format(filename), img)
        db = sqlite3.connect('plateRecogDB.db')
        cursor = db.cursor()
        row = (time_, str(text), time_)
        command = '''REPLACE INTO log (time ,plate,photo) VALUES (?,?,?)'''
        cursor.execute(command, row)
        db.commit()

    def AddUser(self):
        db = sqlite3.connect('plateRecogDB.db')
        cursor = db.cursor()
        plate_no_= int(self.textPlate.text())
        name_= self.textName.text()
        tel_=int(self.textTel.text())
        row = (plate_no_,name_, tel_)
        command = '''REPLACE INTO users (plate_no ,name,tel) VALUES (?,?,?)'''
        cursor.execute(command, row)
        db.commit()

    def UpdateUser(self):
        db = sqlite3.connect('plateRecogDB.db')
        cursor = db.cursor()
        plate_no_= int(self.textPlate.text())
        name_= self.textName.text()
        tel_=int(self.textTel.text())
        row = (plate_no_,name_, tel_)
        command = '''REPLACE INTO users (plate_no ,name,tel) VALUES (?,?,?)'''
        cursor.execute(command, row)
        db.commit()

    def DeleteUser(self):
        db = sqlite3.connect('plateRecogDB.db')
        cursor = db.cursor()
        plate_no_ = int(self.textPlate.text())

        command = '''DELETE FROM users WHERE plate_no =? '''
        cursor.execute(command, plate_no_)
        db.commit()

    def FindUser(self):
        db = sqlite3.connect('plateRecogDB.db')
        cursor = db.cursor()
        command = '''SELECT * FROM users WHERE plate_no=? '''

        result = cursor.execute(command, [int(self.textPlate.text())]).fetchone()
        if result:
            self.textName.setText( result[1])
            self.textTel.setText(str(result[2]))
            #self.textName.setText(result[1])
            tel = result[0]

    def checkandSendSMS(self,text):
        db = sqlite3.connect('plateRecogDB.db')
        cursor = db.cursor()
        command = '''SELECT tel FROM users WHERE plate_no=? '''
        result = cursor.execute(command,[text]).fetchone()
        if result:
            tel=result[0]
            # Generate rendom OTP
            otp = random.randint(1000, 9999)
            print(otp)
            # send SMS
            # Your Account SID from twilio.com/console
            account_sid = "ACcb66f8276f5ba0ece809e9a2552fe845"
            # Your Auth Token from twilio.com/console
            auth_token = "8b7a4f808fd9aa2f4a554cae4755b9a6"

            client = Client(account_sid, auth_token)

            # message = client.messages.create(
            #     to=str('+'+str(tel)),
            #     from_="+12314621944",
            #     body="use this OTP to Open the Gate " + str(otp))
            # self.dev.flushInput()
            # self.dev.flushOutput()
            # self.getOtpFromKeypad(otp)
        else:
            print('this car is not registerd')
            playsound('sound_not_auth_car.mp3')
    def getOtpFromKeypad(self,otp):
        data = ""
        line = ''
        while line != 'A':
            #time.sleep(.001)
            line = self.dev.readline().decode().strip()
            if line != 'A':
                if line != '':
                    data=data + line
                    print(data)
        if data == str(otp):
            print('open door')
            self.dev.write(b'1')
            #self.timer4.singleShot(2000,self.checkSensor)
            self.timer4.timeout.connect(self.checkSensor)  # Connect timeout to the output function
            self.timer4.start(2000)

        else :
                print('wrong OTP')

    def checkSensor(self):
        self.dev.flushInput()
        self.dev.flushOutput()
        self.dev.write(b'2')
        time.sleep(3)

        #print(self.dev.readline())
        distance = int(self.dev.readline().decode().strip())
        if distance < 50 :
            print ('car Reached Parking')
            self.updateUserStatus('in Parking')
            self.loadCarStatus()
        else :
            print('car did not reach the parking')
            self.updateUserStatus('out Parking')
            self.loadCarStatus()
            self.timer4.stop()

    def updateUserStatus(self,str):
        db = sqlite3.connect('plateRecogDB.db')
        cursor = db
        command = '''UPDATE users SET status =? WHERE plate_no =?'''
        row = (str ,self.plate_no)
        cursor.execute(command, row)
        db.commit()


    def displayImage(self, img ):
        qformat = QImage.Format_Indexed8

        if len(img.shape) == 3:  # rows[0],cols[1],channels[2]
            if (img.shape[2]) == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        img = QImage(img, img.shape[1], img.shape[0],img.strides[0], qformat)
        # BGR > RGB
        img = img.rgbSwapped()
        self.imgLable.setPixmap(QPixmap.fromImage(img))
        self.imgLable.setScaledContents(True)

    def displyimage2(self,img):
## disply image2
        qformat = QImage.Format_Indexed8

        if len(img.shape) == 3:  # rows[0],cols[1],channels[2]
            if (img.shape[2]) == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        img = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        # BGR > RGB
        img = img.rgbSwapped()
        self.imgLable2.setPixmap(QPixmap.fromImage(img))
        self.imgLable2.setScaledContents(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainDialog()
    window.setWindowTitle('Car Access System')
    window.show()
    sys.exit(app.exec_())