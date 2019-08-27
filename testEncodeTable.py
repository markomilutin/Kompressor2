__author__ = 'marko'

import sys
import os
import array
import ContextEncoder
import ContextDecoder
import itertools

def main():
    encodeTable = ContextEncoder.ContextEncoder(16)
    decodeTable = ContextDecoder.ContextDecoder(16)

    encodedData1 = array.array("B", itertools.repeat(0, 1025))
    encodedData2 = array.array("B", itertools.repeat(0, 1025))
    encodedData3 = array.array("B", itertools.repeat(0, 1025))
    encodedData4 = array.array("B", itertools.repeat(0, 1025))
    encodedData5 = array.array("B", itertools.repeat(0, 1025))

    testData1 = [11, 11, 12, 13, 13, 14, 11, 12, 12, 240, 222, 8, 9, 55, 11, 11, 12, 240, 11, 12, -2]
    testData2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, -2]
    testData3 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, -2]
    testData4 = []
    testData5 = [11, 12, 11, 12, 11, 13, 13, 11, 11, 13, 13, 2, 9, 55, 11, 11, 12, 240, 11, 12, -2]

    for i in range(0, 255):
        testData4.append(i)
    testData4.append(-2)

    encodedLen1 = encodeTable.encode(testData1, len(testData1), encodedData1, 1025, False)
    encodeTable.reset()
    encodedLen2 = encodeTable.encode(testData2, len(testData2), encodedData2, 1025, False)
    encodeTable.reset()
    encodedLen3 = encodeTable.encode(testData3, len(testData3), encodedData3, 1025, False)
    encodeTable.reset()
    encodedLen4 = encodeTable.encode(testData4, len(testData4), encodedData4, 1025, False)
    encodeTable.reset()
    encodedLen5 = encodeTable.encode(testData5, len(testData5), encodedData5, 1025, False)
    encodeTable.reset()


    decodedData1 = array.array("B", itertools.repeat(0, 1025))
    decodedLen = decodeTable.decode(encodedData1, encodedLen1, decodedData1, 1025)
    decodeTable.reset()

    decodedData2 = array.array("B", itertools.repeat(0, 1025))
    decodedLen = decodeTable.decode(encodedData2, encodedLen2, decodedData2, 1025)
    decodeTable.reset()

    decodedData3 = array.array("B", itertools.repeat(0, 1025))
    decodedLen = decodeTable.decode(encodedData3, encodedLen3, decodedData3, 1025)
    decodeTable.reset()

    decodedData4 = array.array("B", itertools.repeat(0, 1025))
    decodedLen = decodeTable.decode(encodedData4, encodedLen4, decodedData4, 1025)
    decodeTable.reset()

    decodedData5 = array.array("B", itertools.repeat(0, 1025))
    decodedLen = decodeTable.decode(encodedData5, encodedLen5, decodedData5, 1025)
    decodeTable.reset()

if __name__ == "__main__":
    main()