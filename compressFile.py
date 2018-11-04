__author__ = 'marko'

import sys
from Kompressor import Kompressor
from Dekompressor import Dekompressor
import cProfile
import os
import array
from binascii import unhexlify

def main():

    if(len(sys.argv) < 2):
        return

    inputFileName = sys.argv[1]

    if(len(sys.argv) == 3):
        numLinesAtOnce = int(sys.argv[2])
    else:
        numLinesAtOnce = 1

    outputCompressedFileName = inputFileName + '.compressed'

    totalCompressionTime = 0
    fileSize = 0
    compressedFileSize = 0

    inputData = array.array('i', [0]*2048)
    inputDataSize = 0

    kompressor = Kompressor(2048*numLinesAtOnce, 10, 13)
    dekompressor = Dekompressor(2048*numLinesAtOnce, 10, 13)

    # Hold all the compressed data in lines
    compressedFileData = []

    print('Input Filename: ' + inputFileName);
    print('Output Filename: ' + outputCompressedFileName);

    profile = cProfile.Profile()
    profile.enable()
    # Go through each line in file

    lineCount = 0
    dataToCompress = []

    with open(inputFileName, 'r+') as f, open(outputCompressedFileName, 'wb+') as outputCompressedFile:

        for line in f:

            # Strip terminating characters and conver to hex from ascii
            line = line.strip()
            lineBytes = bytearray.fromhex(line)
            inputDataSize = len(lineBytes)

            # Copy the data into the integer array
            for i in range(0, inputDataSize):
                inputData[i] = lineBytes[i]

            dataToCompress.extend(inputData[:inputDataSize])
            dataToCompressSize = len(dataToCompress)
            lineCount += 1

            if(lineCount >= numLinesAtOnce):
                compressedData = bytearray(2048*numLinesAtOnce)
                compressedLineLen = kompressor.kompress(dataToCompress, dataToCompressSize, compressedData, 2048*numLinesAtOnce,lastDataBlock=False)

                compressedFileData.append([compressedLineLen, dataToCompressSize, compressedData])

                #Write compressed line to compressed file
                outputCompressedFile.write(compressedData[0:compressedLineLen])

                fileSize += dataToCompressSize
                compressedFileSize += compressedLineLen

                dataToCompress = []
                lineCount = 0

    profile.disable()

    print('Input File Size: ' + str(fileSize))
    print('Output File Size: ' + str(compressedFileSize))
    print('Compression Percentage: ' + str(int(compressedFileSize/fileSize*100)) + '%')

    profile.print_stats()

    decompressedFileData = []
    decompressedSize = 0

    # Dekompress the data stored in memory
    for i in range(0,len(compressedFileData)):
        decompressedData = bytearray(2048*numLinesAtOnce)
        [compressedLineLen, inputDataSize, compressedLineData]  = compressedFileData[i]

        decompressedDataLen = dekompressor.dekompress(compressedLineData, compressedLineLen, decompressedData, 2048*numLinesAtOnce)

        if(decompressedDataLen != inputDataSize):
            print('ERROR decompressing 1 at line [' + str(i) + ']')
            #exit(0)

        decompressedSize += decompressedDataLen
        decompressedFileData.append([decompressedDataLen, decompressedData])

    #Go through and veriy all decompressed lines match original
    count = 0
    lineCount = 0
    dataToCompare = bytearray()

    with open(inputFileName, 'r+') as f:

        for line in f:
            # Strip terminating characters and conver to hex from ascii
            line = line.strip()
            lineBytes = bytearray.fromhex(line)

            for dataByte in lineBytes:
                dataToCompare.append(dataByte)

            dataToCompareSize = len(dataToCompare)
            lineCount += 1

            if(lineCount >= numLinesAtOnce):

                if(decompressedFileData[count][0] != dataToCompareSize or decompressedFileData[count][1][:decompressedFileData[count][0]] != dataToCompare):
                    print('ERROR decompressing 2 on line [' + str(count) + ']\r\n')
                    exit(0)

                lineCount = 0
                dataToCompare = bytearray()
                count += 1

    print('\n\n')
    print('Decompression Validated')

if __name__ == "__main__":
    main()