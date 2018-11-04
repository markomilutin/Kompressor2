__author__ = 'Marko Milutinovic'

"""
This class implements a table to store symbols for Arithmetic Coding
"""

import array
import utils
import math

class ARDecodeTable:
    ESCAPE_SYMBOL = -1

    def __init__(self, wordSize_, vocabularySize_):
        """
        Initialize the object. The word size must be greater than 2 and less than or equal to 16

        :param wordSize_: The word size (bits) that will be used for encoding. Must be greater than 2 and less than or equal to 16
        :param vocabularySize_: The size of the vocabulary. Symbols run from 0 to (vocabularySize_ - 1)
        :return:
        """
        self.mMaxDecodingBytes = utils.calculateMaxBytes(wordSize_) # The max number of bytes we can compress before the statistics need to be re-normalized

        if(self.mMaxDecodingBytes == 0):
            raise Exception("Invalid word size specified")

        self.mWordSize = wordSize_                                                                 # The tag word size
        self.mWordBitMask = 0x0000                                                                 # The word size bit-mask
        self.mWordMSBMask = (0x0000 | (1 << (self.mWordSize - 1)))                                # The bit mask for the top bit of the word
        self.mWordSecondMSBMask = (0x0000 | (1 << (self.mWordSize - 2)))                          # The bit mask for the second most significant bit of the word

        # Create bit mask for the word size
        for i in range(0, self.mWordSize):
            self.mWordBitMask = (self.mWordBitMask << 1) | 0x0001

        # Reset all the member variables on which encoding is based on
        self.reset()

    def reset(self):
        """
        Reset all member variables that are not constant for the duration of the object life

        :return: None
        """
        self.mE3ScaleCount = 0                                                     # Holds the number of E3 mappings currently outstanding
        self.mCurrentBitCount = 0                                                  # The current number of bits loaded onto the mCurrentByte variable
        self.mSymbolData = []

        # Each table starts with the escape symbol
        self.mSymbolData.append([self.ESCAPE_SYMBOL, 1])
        self.mTotalSymbolCount = 1

        # Initialize the range tags to min and max
        self.mLowerTag = 0
        self.mUpperTag = self.mWordBitMask
        self.mCurrentTag = 0

    def findSymbolIndex(self, symbol_):
        """
        Look for the symbol specified in the table. Return -1 if we can't find it in the table

        : symbol_ : The symbol we are looking for
        :return:
        """
        currentIndex = 0

        #Go through all the symbols currently in the table and if we find a match return the index
        for item in self.mSymbolData:
            if(item[0] == symbol_):
                return currentIndex

            currentIndex += 1

        return -1

    def _update_range_tags(self, symbolIndex_, lowerTag_, upperTag_):
        """
        Update the upper and lower tags according to stats for the incoming symbol

        :param symbolIndex_: Index of current symbol being encoded
        :param lowerTag_: The lower tag that will be used to update range tags
        :param upperTag_: The upper tag that will be used to update range tags
        :return:
        """

        rangeDiff = upperTag_ - lowerTag_
        cumulativeCountSymbol = 0

        for i in range(0, symbolIndex_ + 1):
            cumulativeCountSymbol += self.mSymbolCount[i][1]

        cumulativeCountPrevSymbol = cumulativeCountSymbol - self.mSymbolCount[symbolIndex_][1]

        upperTag_ = int((lowerTag_ + math.floor(((rangeDiff + 1)*cumulativeCountSymbol))/self.mTotalSymbolCount - 1))
        lowerTag_ = int((lowerTag_ + math.floor(((rangeDiff + 1)*cumulativeCountPrevSymbol))/self.mTotalSymbolCount))

        return [lowerTag_, upperTag_]

    def _rescale(self, lowerTag_, upperTag_):
        """
        Perform required rescale operation on the upper and lower tags. The following scaling operations are pefromed:
            E1: both the upper and lower ranges fall into the bottom half of full range [0, 0.5). First bit is 0 for both.
                Shift out MSB for both and shift in 1 for upper tag and 0 for lower tag
            E2: both the upper and lower ranges fall into the top half of full range [0.5, 1). First bit is 1 for both.
                Shift out MSB for both and shift in 1 for upper tag and 0 for lower tag
            E3: the upper and lower tag interval lies in the middle [0.25, 0.75). The second MSB of upper tag is 0 and the second bit of the lower tag is 1.
                Complement second MSB bit of both and shift in 1 for upper tag and 0 for lower tag. Keep track of consecutive E3 scalings
        :param lowerTag_: The lower tag that will be used to rescale
        :param upperTag_: The upper tag that will be used to rescale
        :return: [lowerTag_, upperTag_, encoding, encodedBits] Return the updated lower and upper tags and encoding for the added symbol
        """

        encodedData = 0
        encodedBits = 0

        sameMSB = ((lowerTag_ & self.mWordMSBMask) == (upperTag_ & self.mWordMSBMask))
        valueMSB = ((lowerTag_ & self.mWordMSBMask) >> (self.mWordSize -1)) & 0x0001
        tagRangeInMiddle = (((upperTag_ & self.mWordSecondMSBMask) == 0) and ((lowerTag_ & self.mWordSecondMSBMask) == self.mWordSecondMSBMask))


        while(sameMSB or tagRangeInMiddle):

            # If the first bit is the same we need to perform E1 or E2 scaling. The same set of steps applies to both. If the range is in the middle we need to perform E3 scaling
            if(sameMSB):
                encodedData = (encodedData << 1) | valueMSB
                encodedBits += 1
                lowerTag_ = (lowerTag_ << 1) & self.mWordBitMask
                upperTag_ = ((upperTag_ << 1) | 0x0001) & self.mWordBitMask

                while(self.mE3ScaleCount > 0):
                    encodedData = (encodedData << 1) | ((~valueMSB) & 0x0001)
                    encodedBits += 1
                    self.mE3ScaleCount -= 1

            elif(tagRangeInMiddle):
                lowerTag_ = (lowerTag_ << 1) & self.mWordBitMask
                upperTag_ = (upperTag_ << 1) & self.mWordBitMask

                lowerTag_ = ((lowerTag_ & (~self.mWordMSBMask)) | ((~lowerTag_) & self.mWordMSBMask))
                upperTag_ = ((upperTag_ & (~self.mWordMSBMask)) | ((~upperTag_) & self.mWordMSBMask))

                self.mE3ScaleCount += 1

            sameMSB = ((lowerTag_ & self.mWordMSBMask) == (upperTag_ & self.mWordMSBMask))
            valueMSB = ((lowerTag_ & self.mWordMSBMask) >> (self.mWordSize -1)) & 0x0001
            tagRangeInMiddle = (((upperTag_ & self.mWordSecondMSBMask) == 0) and ((lowerTag_ & self.mWordSecondMSBMask) == self.mWordSecondMSBMask))

        return [lowerTag_, upperTag_, encodedData, encodedBits]

    def addSymbol(self, symbol_):
        """
        Add symbol to table. If it is already in the table increment its count and return encoding in bits. If it is not
        in the table add it and return encoding for escape symbol

        :param symbol_ : The symbol we are are adding
        :return: [encodedData, encodedNumBits] Return encoding for symbol. If number of encoded bits is 0 this was a new symbol for the table
        """

        symbolIndex = self.findSymbolIndex(symbol_)
        encodedData = 0
        encodedNumBits = 0

        #If this is a new symbol add it and return encoding for escape symbol
        if(symbolIndex == -1):
            [self.mLowerTag, self.mUpperTag] = self._update_range_tags(0, self.mLowerTag, self.mUpperTag)
            escapeSymbolEntry = self.mSymbolData[0]
            escapeSymbolEntry[1] += 1

            [self.mLowerTag, self.mUpperTag, encodedData, encodedNumBits] = self._rescale(self.mLowerTag, self.mUpperTag)
        else:
            self.mSymbolData.append([symbol_, 1])

        self.mTotalSymbolCount += 1

        # If we have reached the max number of bytes, we need to normalize the stats to allow us to continue
        if(self.mTotalSymbolCount >= self.mMaxEncodeBytes):
            self._normalize_stats()

        return [encodedData, encodedNumBits]

