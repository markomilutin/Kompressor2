
__author__ = 'Marko Milutinovic'

"""
This class will implement a Context Decoder using Arithmetic Coding
"""

import array
import utils
import math

class ContextDecoder:
    ESCAPE_SYMBOL = -1
    BITS_IN_BYTE = 8

    def __init__(self, wordSize_, terminationSymbol_):
        """
        Initialize the object

        :param wordSize_: The word size (bits) that will be used for compression. Must be greater than 2 and less than 16
        :param terminationSymbol_: Symbol which indicates the end of encoded data where decoding should stop. This is required to properly terminate decoding
        :return: None
        """

        self.mMaxDecodingBytes = utils.calculateMaxBytes(wordSize_)                          # The max number of bytes we can decode before the statistics need to be re-normalized
        self.mTerminationSymbol = terminationSymbol_

        if(self.mMaxDecodingBytes == 0):
            raise Exception("Invalid word size specified")

        self.mWordSize = wordSize_                                                                 # The tag word size
        self.mWordBitMask = 0x0000                                                                 # The word size bit-mask
        self.mWordMSBMask = (0x0000 | (1 << (self.mWordSize - 1)))                                # The bit mask for the top bit of the word
        self.mWordSecondMSBMask = (0x0000 | (1 << (self.mWordSize - 2)))                          # The bit mask for the second most significant bit of the word

        # Create bit mask for the word size
        for i in range(0, self.mWordSize):
            self.mWordBitMask = (self.mWordBitMask << 1) | 0x0001

        # Reset member variables that are not constant
        self.reset()

    def reset(self):
        """ Reset all the member variables that are not constant for the duration of the object life

        :return: None
        """

        self.mEncodedData = None                                                # Holds the encoded data that we are un-compressing. Bytearray
        self.mEncodedDataCount = 0                                              # Number of encoded bytes that we are un-compressing
        self.mDecodedData = None                                                # Holds the data being decoded
        self.mDecodedDataLen = 0                                                # The number of symbols that have been decoded
        self.mCurrentEncodedDataByteIndex = 0                                   # Index of the encoded data with are currently working with
        self.mCurrentEncodedDataBit = 0                                         # The current bit of the current byte we are using from the encoded data bytearray

        self.mLowerTag = 0                                                      # The lower tag threshold
        self.mUpperTag = self.mWordBitMask                                      # The upper tag threshold
        self.mCurrentTag = 0                                                    # The current tag we are processing

        self.mZeroOrderSymbols = []
        self.mZeroOrderSymbols.append([self.ESCAPE_SYMBOL, 1])
        self.mZeroOrderSymbolCount = 1

        self.mFirstOrderSymbols = []
        self.mFirstOrderSymbolCounts = []

        self.mBaseSymbols = []
        # Base symbols are equaly proportional
        for i in range(0,256):
            self.mBaseSymbols.append([i, 1])
        self.mBaseSymbolsCount = 256

    def _get_next_bit(self):
        """
        Get the next bit from encoded data (MSB first). If we move past the current byte move index over to the next one.
        Once there is no more data return None

        :return: next bit value or None if there is no more data
        """

        if(self.mCurrentEncodedDataByteIndex >= self.mEncodedDataCount):
            raise Exception("Exceeded encoded data buffer")

        bitValue = (self.mEncodedData[self.mCurrentEncodedDataByteIndex] >> (self.BITS_IN_BYTE - 1 - self.mCurrentEncodedDataBit)) & 0x0001

        self.mCurrentEncodedDataBit += 1

        # If we have used all the bits in the current byte, move to the next byte
        if(self.mCurrentEncodedDataBit == self.BITS_IN_BYTE):
            self.mCurrentEncodedDataByteIndex += 1
            self.mCurrentEncodedDataBit = 0

        return bitValue

    def _increment_count(self, indexToIncrement_, symbolTable_, totalSymbolCount_):
        """
        Update the count for the provided index. Update
        the total symbol count as well. If we exceed the max symbol count normalize the stats

        :param indexToIncrement_: The index which we are updating
        :param symbolTable_: The symbol table we are updating
        :param totalSymbolCount : The total number of symbols in the table
        :return: The new total symbol count for table
        """

        symbolTable_[indexToIncrement_][1] += 1
        totalSymbolCount_ += 1

        # If we have reached the max number of bytes, we need to normalize the stats to allow us to continue
        if(totalSymbolCount_ >= self.mMaxDecodingBytes):
            totalSymbolCount_ = self._normalize_stats(symbolTable_)

        return totalSymbolCount_

    def _rescale(self):
        """
        Perform required rescale operation on the upper, lower and current tags. The following scaling operations are performed:
            E1: both the upper and lower ranges fall into the bottom half of full range [0, 0.5). First bit is 0 for both.
                Shift out MSB for both and shift in 1 for upper tag and 0 for lower tag. Shift the current tag to left by 1 and move in next bit
            E2: both the upper and lower ranges fall into the top half of full range [0.5, 1). First bit is 1 for both.
                Shift out MSB for both and shift in 1 for upper tag and 0 for lower tag. Shift the current tag to left by 1 and move in next bit
            E3: the upper and lower tag interval lies in the middle [0.25, 0.75). The second MSB of upper tag is 0 and the second bit of the lower tag is 1.
                Complement second MSB bit of both and shift in 1 for upper tag and 0 for lower tag. Complement second MSB of the current tag, shift to the left by 1 and move in the next bit
        :return:None
        """
        sameMSB = ((self.mLowerTag & self.mWordMSBMask) == (self.mUpperTag & self.mWordMSBMask))
        valueMSB = ((self.mLowerTag & self.mWordMSBMask) >> (self.mWordSize -1)) & 0x0001
        tagRangeInMiddle = (((self.mUpperTag & self.mWordSecondMSBMask) == 0) and ((self.mLowerTag & self.mWordSecondMSBMask) == self.mWordSecondMSBMask))


        while(sameMSB or tagRangeInMiddle):

            # If the first bit is the same we need to perform E1 or E2 scaling. The same set of steps applies to both. If the range is in the middle we need to perform E3 scaling
            if(sameMSB):
                self.mLowerTag = (self.mLowerTag << 1) & self.mWordBitMask
                self.mUpperTag = ((self.mUpperTag << 1) | 0x0001) & self.mWordBitMask
                self.mCurrentTag = ((self.mCurrentTag << 1) | self._get_next_bit()) & self.mWordBitMask

            elif(tagRangeInMiddle):
                self.mLowerTag = (self.mLowerTag << 1) & self.mWordBitMask
                self.mUpperTag = (self.mUpperTag << 1) & self.mWordBitMask
                self.mCurrentTag = ((self.mCurrentTag << 1) | self._get_next_bit()) & self.mWordBitMask

                self.mLowerTag = ((self.mLowerTag & (~self.mWordMSBMask)) | ((~self.mLowerTag) & self.mWordMSBMask))
                self.mUpperTag = ((self.mUpperTag & (~self.mWordMSBMask)) | ((~self.mUpperTag) & self.mWordMSBMask))
                self.mCurrentTag = ((self.mCurrentTag & (~self.mWordMSBMask)) | ((~self.mCurrentTag) & self.mWordMSBMask))

            sameMSB = ((self.mLowerTag & self.mWordMSBMask) == (self.mUpperTag & self.mWordMSBMask))
            valueMSB = ((self.mLowerTag & self.mWordMSBMask) >> (self.mWordSize -1)) & 0x0001
            tagRangeInMiddle = (((self.mUpperTag & self.mWordSecondMSBMask) == 0) and ((self.mLowerTag & self.mWordSecondMSBMask) == self.mWordSecondMSBMask))

    def _update_range_tags(self, currentSymbolIndex_, cumulativeCountSymbol_, symbolTable_, symbolTableCount_, actionOnSymbol_):
        """
        Update the upper and lower tags according to stats for the incoming symbol

        :param newSymbol_: Current symbol being encoded
        :param cumulativeCountSymbol_: The cumulative count of the current symbol
        :return: The new symbol table count for symbol table
        """

        prevLowerTag = self.mLowerTag
        prevUpperTag = self.mUpperTag
        rangeDiff = prevUpperTag - prevLowerTag
        cumulativeCountPrevSymbol = cumulativeCountSymbol_ - symbolTable_[currentSymbolIndex_][1]

        self.mLowerTag = int((prevLowerTag + math.floor(((rangeDiff + 1)*cumulativeCountPrevSymbol))/symbolTableCount_))
        self.mUpperTag = int((prevLowerTag + math.floor(((rangeDiff + 1)*cumulativeCountSymbol_))/symbolTableCount_ - 1))

        if(actionOnSymbol_ == 0):
            return symbolTableCount_
        elif(actionOnSymbol_ == -1):
            return self._decrement_count(currentSymbolIndex_, symbolTable_, symbolTableCount_)
        else:
            return self._increment_count(currentSymbolIndex_, symbolTable_, symbolTableCount_)

    def _decrement_count(self, indexToDecrement_, symbolTable_, totalSymbolCount_):
        """

        :param indexToDecrement_: The index which we are updating
        :param symbolTable_: The symbol table we are updating
        :param totalSymbolCount : The total number of symbols in the table
        :return: The new total symbol count for table
        """

        symbolTable_[indexToDecrement_][1] -= 1
        totalSymbolCount_ -= 1

        #If we hit zero count remove the symbol from table
        if(symbolTable_[indexToDecrement_][1] == 0):
            symbolTable_.pop(indexToDecrement_)

        return totalSymbolCount_

    def _normalize_stats(self, symbolTable_):
        """
        Divide the total count for each symbol by 2 but ensure each symbol count is at least 1.
        Get new total symbol count from the entries

        :param: symbolTable_: Current table we are normalizing
        :return: The new symbol count for table
        """

        symbolCount = 0

        # Go through all the entries in the cumulative count array
        for i in range(0, len(symbolTable_)):

            value = int(symbolTable_[i][1]/2)

            # Ensure the count is at least 1
            if(value == 0):
                value = 1

            symbolTable_[i][1] = value
            symbolCount += value

        return symbolCount

    def decodeFromTable(self, symbolTable_, symbolTableCount_, actionOnSymbol_):
        currentSymbolIndex = 0
        currentCumulativeCount = int(math.floor(
            ((self.mCurrentTag - self.mLowerTag + 1) * symbolTableCount_ - 1) / (
            self.mUpperTag - self.mLowerTag + 1)))

        finished = False
        symbolCumulativeCount = symbolTable_[0][1]

        while (currentCumulativeCount >= symbolCumulativeCount):
            currentSymbolIndex += 1

            if (currentSymbolIndex >= len(symbolTable_)):
                raise Exception("Symbol count of out range")

            symbolCumulativeCount += symbolTable_[currentSymbolIndex][1]

        currentSymbol = symbolTable_[currentSymbolIndex][0]
        # If we have reached the termination symbol then decoding is finished, otherwise store the decompressed symbol
        if (currentSymbol == self.mTerminationSymbol):
            finished = True

        symbolTableCount_ = self._update_range_tags(currentSymbolIndex, symbolCumulativeCount, symbolTable_, symbolTableCount_, actionOnSymbol_)
        self._rescale()

        return [currentSymbol, finished, symbolTableCount_]

    def addSymbolTable(self, contextTable_, contextTableCounts_, contextSymbol_):
        contextTable_.insert(len(contextTable_) - 1, [contextSymbol_, [[-1, 0]]])
        contextTableCounts_.insert(len(contextTable_) -1, 1)

    def zeroOrderDecode(self):
        finished = False

        # Attempt to decode from zero order table first
        [currentSymbol, finished, self.mZeroOrderSymbolCount] = self.decodeFromTable(self.mZeroOrderSymbols,
                                                                                     self.mZeroOrderSymbolCount, 1)

        # If we have reached the termination symbol then decoding is finished, otherwise store the decompressed symbol
        if (not finished):
            if (currentSymbol == self.ESCAPE_SYMBOL):
                [currentSymbol, finished, self.mBaseSymbolsCount] = self.decodeFromTable(self.mBaseSymbols,
                                                                                         self.mBaseSymbolsCount, -1)
                self.mZeroOrderSymbols.insert(len(self.mZeroOrderSymbols) - 1, [currentSymbol, 0])
                self.mZeroOrderSymbolCount = self._increment_count(len(self.mZeroOrderSymbols) - 2,
                                                                   self.mZeroOrderSymbols,
                                                                   self.mZeroOrderSymbolCount)
        return [currentSymbol, finished]

    def decode(self, encodedData_, encodedDataLen_, decodedData_, maxDecodedDataLen_):
        """
        Decompress the data passed in. It is the responsibility of the caller to reset the decoder if required before
        calling this function

        :param encodedData_: The data that needs to be decoded (bytearray)
        :param encodedDataLen_: The length of data that needs to be decoded
        :param decodedData_: The decoded data (integer array)
        :param maxDecodedDatalen_ : The max number of symbols that can be stored in decodedData_ array
        :param firstDataBlock: If this is True then mCurrentTag must be loaded
        :return: Returns the number of symbols stored in decodedData_
        """

        # If the byte array is smaller than data length pass in throw exception
        if(len(encodedData_) < encodedDataLen_):
            raise Exception("Data passed in smaller than expected")

        # If the byte array is smaller than data length pass in throw exception
        if(len(decodedData_) < maxDecodedDataLen_):
            raise Exception("Decompressed data byte array passed in smaller than expected")

        self.mEncodedData = encodedData_
        self.mEncodedDataCount = encodedDataLen_
        self.mDecodedData = decodedData_
        self.mDecodedDataLen = 0
        self.mCurrentEncodedDataByteIndex = 0
        self.mCurrentEncodedDataBit = 0
        self.mCurrentTag = 0

        # Load the first word size bits into the current tag
        for i in range(0, self.mWordSize):
            self.mCurrentTag = (self.mCurrentTag | (self._get_next_bit() << ((self.mWordSize - 1) - i)))

        finished = False
        currentContext = None

        # Until we have reached the end keep decompressing
        while(not finished):
            # If we don't have a context don't bother doing first order
            if(currentContext == None):
                [currentSymbol, finished] = self.zeroOrderDecode()
                currentContext = currentSymbol
                self.addSymbolTable(self.mFirstOrderSymbols, self.mFirstOrderSymbolCounts, currentContext)
            else:
                symbolTableIndex = self.findSymbolIndex(currentContext, self.mFirstOrderSymbols)

                if(symbolTableIndex == -1):
                    raise Exception("Not in first order")

                symbolTable = self.mFirstOrderSymbols[symbolTableIndex][1]
                [currentSymbol, finished, self.mFirstOrderSymbolCounts[symbolTableIndex]] = self.decodeFromTable(symbolTable, self.mFirstOrderSymbolCounts[symbolTableIndex], 1)

                #If the symbol is not in the table send escape symbol and use lower order to encode symbol
                if(currentSymbol == -1):
                    self.zeroOrderEncode(dataToEncode_[i])

                    symbolTable.insert(len(symbolTable) - 1, [dataToEncode_[i], 0])
                    self.mFirstOrderSymbolCounts[symbolTableIndex] = \
                        self._increment_count(len(symbolTable) - 2, symbolTable, self.mFirstOrderSymbolCounts[symbolTableIndex])
                    self.mFirstOrderSymbolCounts[symbolTableIndex] = \
                        self._increment_count(len(symbolTable) - 1, symbolTable, self.mFirstOrderSymbolCounts[symbolTableIndex])
                else:
                    [self.mLowerTag, self.mUpperTag] = self._update_range_tags(symbolIndex, symbolTable, self.mFirstOrderSymbolCounts[symbolTableIndex], self.mLowerTag, self.mUpperTag)
                    self.mFirstOrderSymbolCounts[symbolTableIndex] = self._increment_count(symbolIndex, symbolTable, self.mFirstOrderSymbolCounts[symbolTableIndex])
                    [self.mLowerTag, self.mUpperTag] = self._rescale(self.mLowerTag, self.mUpperTag)

                currentContext = dataToEncode_[i]
                symbolTableIndex = self.findSymbolIndex(currentContext, self.mFirstOrderSymbols)

                #If not in symbol table add it
                if(symbolTableIndex == -1):
                    self.addSymbolTable(self.mFirstOrderSymbols, self.mFirstOrderSymbolCounts, currentContext)



            if(not finished):
                self.mDecodedData[self.mDecodedDataLen] = currentSymbol
                self.mDecodedDataLen += 1

                # If there is no more room extend the bytearray by BASE_OUT_SIZE bytes
                if(self.mDecodedDataLen >= maxDecodedDataLen_):
                    raise Exception('Not enough space to store decoded data')


        return self.mDecodedDataLen