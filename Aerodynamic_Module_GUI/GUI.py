# Config program using PyQt5

import sys
import os
import matplotlib.pyplot as plt
import shutil, tempfile, math, numpy, string
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QFileDialog
import subprocess
import pyqtgraph as pg
import scp

form_class = uic.loadUiType("Config.ui")[0]  # Load the UI


class Mapper(QtWidgets.QMainWindow, form_class):
    def __init__(self,  parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        # Bind the event handlers to the buttons
        self.pushButton_2.clicked.connect(self.runAeroDyn)
        self.pushButton_3.clicked.connect(self.plotCp)
        self.pushButton_4.clicked.connect(self.plotCt)
        self.pushButton_5.clicked.connect(self.saveData)
        self.toolButton.clicked.connect(self.openFileDialogue)
        self.toolButton_2.clicked.connect(self.setWorkingDir)
        self.comboBox.activated.connect(self.showSolverSetup)
        self.pushButton_7.clicked.connect(self.generateALMCase)
        self.pushButton_8.clicked.connect(self.sendToHPC)



	# Set placeholders
        self.lineEdit_7.setText("11.4")
        self.lineEdit_2.setText("start increment end")
        self.lineEdit_3.setText("0")
        self.lineEdit_4.setText("0")
        self.lineEdit_11.setText("200")
        self.lineEdit_5.setText("500")
        self.solverFolder = "/home/kz/openfast/build/modules/aerodyn"
        self.lineEdit_8.setText(self.solverFolder)
        self.workingFolder = "AeroDynCase"
        self.lineEdit_9.setText(self.workingFolder)
        self.workingFolder2 = "ALMCase"
        self.lineEdit_12.setText(self.workingFolder2)
        self.rpm = numpy.array([])
        self.progressBar.setValue(0)
        self.lineEdit_14.setText("amarel.rutgers.edu")
        self.lineEdit_13.setText("kz239")
        self.lineEdit_15.setText("/scratch/kz239/newUploads")

    def showSolverSetup(self):
        print("The user have selected "+str(self.comboBox.currentText()))
        if self.comboBox.currentText() == "AeroDyn (BEM)":
            self.stackedWidget.setCurrentIndex(1)
            self.lineEdit_2.setText("0 0.5 20")
        if self.comboBox.currentText() == "OpenFOAM (ALM)":
            self.stackedWidget.setCurrentIndex(0)
            self.lineEdit_2.setText("0 0.5 20")

    def openFileDialogue(self):
        self.solverFolder = str(QtWidgets.QFileDialog.getExistingDirectory())
        self.lineEdit_8.setText(self.solverFolder)

    def setWorkingDir(self):
        self.workingFolder = str(QtWidgets.QFileDialog.getExistingDirectory())
        self.lineEdit_9.setText(self.workingFolder)
        



    def runAeroDyn(self):
        os.chdir(self.workingFolder)
        self.Cp = numpy.array([])
        self.Ct = numpy.array([])
        rpmStr = self.lineEdit_2.text().split()
        rpmFlo = [float(i) for i in rpmStr] 
        self.rpm = numpy.arange(rpmFlo[0], rpmFlo[2]+rpmFlo[1], rpmFlo[1])
        idx = 0
        nTotal = (self.rpm[-1]+self.rpm[1]-self.rpm[0])/self.rpm[1] 
        for ii in self.rpm:
            idx = idx + 1
            
            shutil.copyfile("driver.dvr.org", "driver.dvr")
            fname = open("driver.dvr", 'a')
            param = [self.lineEdit_7.text(), 0, ii, self.lineEdit_3.text(), self.lineEdit_4.text(), 0.1, 2]
            for line in param:
                fname.write(str(line))
                fname.write("\t")
            fname.close()

            subprocess.run([self.solverFolder+"/aerodyn_driver", "driver.dvr"])

            resultCp = numpy.loadtxt("Test014.1.out", skiprows=8, usecols=(1,))           
            resultCt = numpy.loadtxt("Test014.1.out", skiprows=8, usecols=(3,))           
            self.Cp = numpy.append(self.Cp, resultCp[-1])
            self.Ct = numpy.append(self.Ct, resultCt[-1])
            self.progressBar.setValue(idx/nTotal*100)
        os.chdir("..")


    def plotCp(self):
        plt.plot(self.rpm, self.Cp)
        plt.xlabel('RPM', fontsize=16)
        plt.ylabel('$C_T$', fontsize=16)
        plt.show()

    def plotCt(self):
        plt.plot(self.rpm, self.Ct)
        plt.xlabel('RPM', fontsize=16)
        plt.ylabel('$C_T$', fontsize=16)
        plt.show()

    def saveData(self):
        fileName = self.lineEdit_10.text()
        f1 = open(str(fileName), 'w')
        idx = 0
        f1.write('# RPM \t Cp \t Ct \n')
        for iii in self.rpm:
            f1.write(str(iii)+'\t'+str(self.Cp[idx])+'\t'+str(self.Ct[idx])+'\n')
            idx = idx + 1
        f1.close()


    def generateALMCase(self):    
        self.ALMFolder = self.lineEdit_12.text()
        rpmStr = self.lineEdit_2.text().split()
        rpmFlo = [float(i) for i in rpmStr] 
        self.rpm = numpy.arange(rpmFlo[0], rpmFlo[2]+rpmFlo[1], rpmFlo[1])
        os.chdir(self.ALMFolder)
        for ii in self.rpm:
            caseName = "rpm"+str(ii)
            shutil.copytree('source',caseName)
            os.chdir(caseName)
            tsr = ii*6.28*89.15/60/float(self.lineEdit_7.text())
            fname = open('0/include/initialConditions', 'w')
            fname.write("/*--------------------------------*- C++ -*----------------------------------*\ \n")
            fname.write("| =========                 |                                                 | \n")
            fname.write("| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           | \n")
            fname.write("|  \\    /   O peration     | Version:  4.x                                   | \n")
            fname.write("|   \\  /    A nd           | Web:      www.OpenFOAM.org                      | \n")
            fname.write("|    \\/     M anipulation  |                                                 | \n")
            fname.write("\*---------------------------------------------------------------------------*/ \n")

            fname.write("WndVel		" + self.lineEdit_7.text() + ';\n')
            fname.write("TSR		" + str(tsr) + ';\n')
            fname.write("BldPitchAng	" + self.lineEdit_3.text() + ';\n')
            fname.write("Yaw		" + self.lineEdit_4.text() + ';\n')

            fname.write("EndTime		" + self.lineEdit_11.text() + ';\n')
            fname.write("WriteInterval		" + self.lineEdit_5.text() + ';\n')
            fname.write("DynamicStall	" + self.comboBox_11.currentText() + ';\n');
            fname.write("EndEffectsModel	" + self.comboBox_10.currentText() + ';\n');

            fname.close()
            os.chdir("..")
        os.chdir("..")


    def sendToHPC(self):
        subprocess.run(["scp", "-r", self.lineEdit_12.text() ,self.lineEdit_13.text()+"@"+self.lineEdit_14.text()+":"+self.lineEdit_15.text()])
        subprocess.run(["rm", "-r",  self.ALMFolder+"/rpm*"])

def run():
    app = QtWidgets.QApplication(sys.argv)
    myWindow = Mapper()
    myWindow.show()
    app.exec_()

run()
