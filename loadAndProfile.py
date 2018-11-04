__author__ = 'marko'

import sys
import os
import array
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

def main():

    if(len(sys.argv) < 2):
        return

    inputFileName = sys.argv[1]

    fileSize = 0
    fileData = []

    print('Input Filename: ' + inputFileName)

    uniqueSymbols = dict()

    with open(inputFileName, 'rb+') as inputFile:

        byte = inputFile.read(1)
        while byte != b'':

            integerValue = ord(byte)
            if(integerValue in uniqueSymbols):
                uniqueSymbols[integerValue] += 1
            else:
                uniqueSymbols[integerValue] = 1

            fileData.append(integerValue)
            byte = inputFile.read(1)
            fileSize += 1

    symbolCounts = dict()

    for i in range(0,255):
        if i in uniqueSymbols:
            symbolCounts[i] = uniqueSymbols[i]
        else:
            symbolCounts[i] = 0


    print('Input File Size: {0} bytes'.format(str(fileSize)))

    xaxis = range(0,255)

    yaxis = uniqueSymbols

    # Note that using plt.subplots below is equivalent to using
    # fig = plt.figure() and then ax = fig.add_subplot(111)
    fig, ax = plt.subplots()
    ax.plot(range(len(symbolCounts)), symbolCounts.values())

    ax.set(xlabel='8-bit symbols (0-255)', ylabel='Count', title='Symbol count vs all symbols')
    ax.grid()

    fig.savefig("test.png")
    plt.show()

if __name__ == "__main__":
    main()