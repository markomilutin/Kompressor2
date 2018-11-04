__author__ = 'marko'

import sys
from AREncoder import AREncoder
from ARDecoder import ARDecoder
import os
import array
from binascii import unhexlify
import itertools

def main():

    if(len(sys.argv) < 2):
        return

    inputFileName = sys.argv[1]
    outputEncodedFileName = inputFileName + '.enc1'

    fileSize = 0
    encodedFileSize = 0

    inputDataSize = 0

    encoder = AREncoder(16, 257)
    decoder = ARDecoder(16, 257, 256)

    print('Input Filename: ' + inputFileName);
    print('Output Filename: ' + outputEncodedFileName);

    lineCount = 0
    inputFileData = []

    with open(inputFileName, 'rb+') as inputFile:

        byte = inputFile.read(1)
        while byte != b'':
            integerValue = ord(byte)
            inputFileData.append(integerValue)
            byte = inputFile.read(1)
            fileSize += 1

    dataLeftToEncode = fileSize
    dataIndex = 0
    encodedData = []
    encodedFile = []
    encodedDataSize = 0


    while(dataLeftToEncode >0):
        dataChunkToProcess = 1024
        lastBlock = False

        if(dataLeftToEncode < dataChunkToProcess):
            dataChunkToProcess = dataLeftToEncode
            lastBlock = True

        dataToEncode = inputFileData[dataIndex:(dataIndex+dataChunkToProcess)]
        dataToEncode.append(256)
        encodedData = array.array("B", itertools.repeat(0, 1025))

        encodedDataCount = encoder.encode(dataToEncode, dataChunkToProcess+1, encodedData, 1025, lastBlock)
        encodedFile.append([encodedDataCount, encodedData])
        encodedFileSize += encodedDataCount

        dataLeftToEncode -= dataChunkToProcess

        decodedData = array.array("B", itertools.repeat(0, 2048))
        decodedDataLen = decoder.decode(encodedData, encodedDataCount, decodedData, 2048)

        if(decodedDataLen != dataChunkToProcess):
            print("Decode Failed 1")
            return

        for i in range(0, dataChunkToProcess):
            if(decodedData[i] != dataToEncode[i]):
                print("Decode Failed 2")
                return

        dataIndex += dataChunkToProcess

    print('Input File Size: ' + str(fileSize))
    print('Output File Size: ' + str(encodedFileSize))
    print('Compression Percentage: ' + str(100 - int(encodedFileSize*100/fileSize)) + '%')

if __name__ == "__main__":
    main()