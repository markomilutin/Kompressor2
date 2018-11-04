__author__ = 'Marko Milutinovic'

"""
This class will implement an Arithmetic Coding encoder
"""

import array
import utils
import math

class AREncoder:
    def __init__(self, wordSize_, vocabularySize_):
        """
        Initialize the object. The word size must be greater than 2 and less than or equal to 16

        :param wordSize_: The word size (bits) that will be used for encoding. Must be greater than 2 and less than or equal to 16
        :param vocabularySize_: The size of the vocabulary. Symbols run from 0 to (vocabularySize_ - 1)
        :return:
        """
        self.mMaxEncodeBytes = utils.calculateMaxBytes(wordSize_)                                 # The max number of bytes we can compress before the statistics need to be re-normalized
        self.mVocabularySize = vocabularySize_

        if(self.mMaxEncodeBytes == 0):
            raise Exception("Invalid word size specified")

        self.mWordSize = wordSize_                                                                 # The tag word size
        self.mWordBitMask = 0x0000                                                                 # The word size bit-mask
        self.mWordMSBMask = (0x0000 | (1 << (self.mWordSize - 1)))                                # The bit mask for the top bit of the word
        self.mWordSecondMSBMask = (0x0000 | (1 << (self.mWordSize - 2)))                          # The bit mask for the second most significant bit of the word

        # Create bit mask for the word size
        for i in range(0, self.mWordSize):
            self.mWordBitMask = (self.mWordBitMask << 1) | 0x0001

        # We are initializing with an assumption of a value of 1 for the count of each symbol.
        self.mSymbolCount = array.array('i', [1]*self.mVocabularySize)

        # Reset all the member variables on which encoding is based on
        self.reset()

    def reset(self):
        """
        Reset all member variables that are not constant for the duration of the object life

        :return: None
        """

        self.mEncodedData = None
        self.mMaxEncodedDataLen = 0                                                # The max number of bytes that can be stored in mEncodedData
        self.mEncodedDataCount = int(0)                                            # The number of bytes compressed data is taking up
        self.mTotalSymbolCount = self.mVocabularySize                              # The total number of symbols encountered
        self.mE3ScaleCount = 0                                                     # Holds the number of E3 mappings currently outstanding
        self.mCurrentBitCount = 0                                                  # The current number of bits loaded onto the mCurrentByte variable

        # We are initializing with an assumption of a value of 1 for the count of each symbol
        for i in range(0,self.mVocabularySize):
            self.mSymbolCount[i] = 1

        # Initialize the range tags to min and max
        self.mLowerTag = 0
        self.mUpperTag = self.mWordBitMask

    def _append_bit(self, bitValue_):
        """
        Take the incoming bit and append it to the mCurrentByte. Once 8 bits have been appended move to the next
        index of the compressed data array

        :param bitValue: The bit to be appended to the current outstanding compression byte
        :return: None
        """

        # Store the current bit onto the pending byte
        self.mEncodedData[self.mEncodedDataCount] = ((self.mEncodedData[self.mEncodedDataCount] << 1) | bitValue_) & 0xFF

        # Increment the count of bits stored
        self.mCurrentBitCount += 1

        # If max number of bits have been appended, move to compressed data byte array
        if(self.mCurrentBitCount == 8):
            self.mEncodedDataCount += 1

            # If there is no more room throw exception
            if(self.mEncodedDataCount >= self.mMaxEncodedDataLen):
                raise Exception('Out of space')

            self.mCurrentBitCount = 0
            self.mEncodedData[self.mEncodedDataCount] = int(0)

    def _increment_count(self, indexToIncrement_):
        """
        Update the count for the provided index. Update
        the total symbol count as well. If we exceed the max symbol count normalize the stats

        :param indexToIncrement_: The index which we are updating
        :return: None
        """

        self.mSymbolCount[indexToIncrement_] += 1
        self.mTotalSymbolCount += 1

        # If we have reached the max number of bytes, we need to normalize the stats to allow us to continue
        if(self.mTotalSymbolCount >= self.mMaxEncodeBytes):
            self._normalize_stats()

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
        :return: [lowerTag_, upperTag_] Return the updated lower and upper tags
        """

        sameMSB = ((lowerTag_ & self.mWordMSBMask) == (upperTag_ & self.mWordMSBMask))
        valueMSB = ((lowerTag_ & self.mWordMSBMask) >> (self.mWordSize -1)) & 0x0001
        tagRangeInMiddle = (((upperTag_ & self.mWordSecondMSBMask) == 0) and ((lowerTag_ & self.mWordSecondMSBMask) == self.mWordSecondMSBMask))


        while(sameMSB or tagRangeInMiddle):

            # If the first bit is the same we need to perform E1 or E2 scaling. The same set of steps applies to both. If the range is in the middle we need to perform E3 scaling
            if(sameMSB):
                self._append_bit(valueMSB)
                lowerTag_ = (lowerTag_ << 1) & self.mWordBitMask
                upperTag_ = ((upperTag_ << 1) | 0x0001) & self.mWordBitMask

                while(self.mE3ScaleCount > 0):
                    self._append_bit((~valueMSB) & 0x0001)
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

        return [lowerTag_, upperTag_]

    def _update_range_tags(self, currentSymbol_, lowerTag_, upperTag_):
        """
        Update the upper and lower tags according to stats for the incoming symbol

        :param currentSymbol_: Current symbol being encoded
        :param symbolCumulativeCount_: The cumulative count of the current symbol
        :param lowerTag_: The lower tag that will be used to update range tags
        :param upperTag_: The upper tag that will be used to update range tags
        :return:
        """

        rangeDiff = upperTag_ - lowerTag_
        cumulativeCountSymbol = 0

        for i in range(0, currentSymbol_ + 1):
            cumulativeCountSymbol += self.mSymbolCount[i]

        cumulativeCountPrevSymbol = cumulativeCountSymbol - self.mSymbolCount[currentSymbol_]

        upperTag_ = int((lowerTag_ + math.floor(((rangeDiff + 1)*cumulativeCountSymbol))/self.mTotalSymbolCount - 1))
        lowerTag_ = int((lowerTag_ + math.floor(((rangeDiff + 1)*cumulativeCountPrevSymbol))/self.mTotalSymbolCount))

        return [lowerTag_, upperTag_]

    def _normalize_stats(self):
        """
        Divide the total count for each symbol by 2 but ensure each symbol count is at least 1.
        Get new total symbol count from the entries

        :return: None
        """

        self.mTotalSymbolCount = 0

        # Go through all the entries in the cumulative count array
        for i in range(0, self.mVocabularySize):

            value = int(self.mSymbolCount[i]/2)

            # Ensure the count is at least 1
            if(value == 0):
                value = 1

            self.mSymbolCount[i] = value
            self.mTotalSymbolCount += value

    def encode(self, dataToEncode_, dataLen_, encodedData_, maxEncodedDataLen_, lastDataBlock=True):
        """
        Encode the data passed in. The encoded data will be stored in encodedData_ and if there is not enough room an
        exception will be thrown. Encoding statistics will not be reset when this function is called. It is up-to the caller
        to ensure that statistics are initialized properly if required.

        :param dataToEncode_: The data that needs to be compressed (integer array)
        :param dataLen_: The length of data that needs to be compressed
        :param encodedData_: The compressed data should be stored in this byte array
        :param maxEncodedDataLen_ : The max length of compressed data that can be stored in encodedData_
        :param lastDataBlock: Is this the last data block being encoded. If not we need to take special care to terminate
                              properly so that decoder can work properly
        :return: The number of bytes stored in encodedData_
        """

        # If the byte array is smaller than data length pass in throw exception
        if(len(dataToEncode_) < dataLen_):
            raise Exception("Data byte array passed in smaller than expected")

        # If the byte array is smaller than data length pass in throw exception
        if(len(encodedData_) < maxEncodedDataLen_):
            raise Exception("Encoded data byte array passed in smaller than expected")

        self.mEncodedData = encodedData_
        self.mEncodedDataCount = 0
        self.mCurrentBitCount = 0
        self.mMaxEncodedDataLen = maxEncodedDataLen_

        # Go through and compress data one byte at a time
        for i in range(0, dataLen_):
            [self.mLowerTag, self.mUpperTag] = self._update_range_tags(dataToEncode_[i], self.mLowerTag, self.mUpperTag)
            self._increment_count(dataToEncode_[i])
            [self.mLowerTag, self.mUpperTag] = self._rescale(self.mLowerTag, self.mUpperTag)

        lowerTagToSend = self.mLowerTag

        # If not last data block insert extra symbol so that we can properly carry over on decoder. The decoder must be able to fully process the last symbol in order to work properly.
        # As data is transferred in bytes (not bits) there remains the possibility of extra 0 bits after data has ended which will confuse the decoder. If the last symbol encoded is a don't care then the decoder will properly pick up the actual last symbol.
        # The last symbol can't be reflected in the statistics as it will be thrown away on the decoder side
        if(lastDataBlock == False):
            [lower, upper] = self._update_range_tags(0, self.mLowerTag, self.mUpperTag)
            [lower, upper] = self._rescale(lower, upper)
            lowerTagToSend = lower

        # Store the current state of the lower tag to mark the completion of the compression
        for i in range(0, self.mWordSize):
            bitValue = (lowerTagToSend >> ((self.mWordSize - 1) - i)) & 0x0001

            self._append_bit(bitValue)

            # Ensure we account for any E3 scaling
            while(self.mE3ScaleCount > 0):
                self._append_bit((~bitValue) & 0x0001)
                self.mE3ScaleCount -= 1

        # Ensure that the current byte is added to the compressed data length if there are any outstanding bits on it
        if(self.mCurrentBitCount != 0):
            self.mEncodedDataCount += 1

        return self.mEncodedDataCount