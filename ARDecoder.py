
__author__ = 'Marko Milutinovic'

"""
This class will implement an Arithmetic Coding decoder
"""

import array
import utils
import math

class ARDecoder:
    BITS_IN_BYTE = 8

    def __init__(self, wordSize_, vocabularySize_, terminationSymbol_):
        """
        Initialize the object

        :param wordSize_: The word size (bits) that will be used for compression. Must be greater than 2 and less than 16
        :param: vocabularySize_: The size of the vocabulary. Symbols run rom 0 to (vocabularySize -1)
        :param terminationSymbol_: Symbol which indicates the end of encoded data where decoding should stop. This is required to properly terminate decoding
        :return: None
        """

        self.mMaxDecodingBytes = utils.calculateMaxBytes(wordSize_)                          # The max number of bytes we can decode before the statistics need to be re-normalized
        self.mVocabularySize = vocabularySize_
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

        # We are initializing with an assumption of a value of 1 for the count of each symbol.
        self.mSymbolCount = array.array('i', [1]*self.mVocabularySize)

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
        self.mTotalSymbolCount = self.mVocabularySize                           # The total number of symbols encountered

        self.mLowerTag = 0                                                      # The lower tag threshold
        self.mUpperTag = self.mWordBitMask                                      # The upper tag threshold
        self.mCurrentTag = 0                                                    # The current tag we are processing

        # We are initializing with an assumption of a value of 1 for the count of each symbol
        for i in range(0,self.mVocabularySize):
            self.mSymbolCount[i] = 1

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
        if(self.mTotalSymbolCount >= self.mMaxDecodingBytes):
            self._normalize_stats()

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

    def _update_range_tags(self, currentSymbolIndex_, cumulativeCountSymbol_):
        """
        Update the upper and lower tags according to stats for the incoming symbol

        :param newSymbol_: Current symbol being encoded
        :param cumulativeCountSymbol_: The cumulative count of the current symbol
        :return: None
        """

        prevLowerTag = self.mLowerTag
        prevUpperTag = self.mUpperTag
        rangeDiff = prevUpperTag - prevLowerTag
        cumulativeCountPrevSymbol = cumulativeCountSymbol_ - self.mSymbolCount[currentSymbolIndex_]

        self.mLowerTag = int((prevLowerTag + math.floor(((rangeDiff + 1)*cumulativeCountPrevSymbol))/self.mTotalSymbolCount))
        self.mUpperTag = int((prevLowerTag + math.floor(((rangeDiff + 1)*cumulativeCountSymbol_))/self.mTotalSymbolCount - 1))

        self._increment_count(currentSymbolIndex_)

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

        # Until we have reached the end keep decompressing
        while(not finished):
            currentSymbol = 0
            currentCumulativeCount = int(math.floor(((self.mCurrentTag - self.mLowerTag + 1)*self.mTotalSymbolCount - 1)/(self.mUpperTag - self.mLowerTag +1)))

            symbolCumulativeCount = self.mSymbolCount[0]

            while(currentCumulativeCount >= symbolCumulativeCount):
                currentSymbol += 1

                if(currentSymbol >= self.mVocabularySize):
                    raise Exception("Symbol count of out range")

                symbolCumulativeCount += self.mSymbolCount[currentSymbol]

            # If we have reached the termination symbol then decoding is finished, otherwise store the decompressed symbol
            if(currentSymbol == self.mTerminationSymbol):
                finished = True
            else:
                self.mDecodedData[self.mDecodedDataLen] = currentSymbol
                self.mDecodedDataLen += 1

                # If there is no more room extend the bytearray by BASE_OUT_SIZE bytes
                if(self.mDecodedDataLen >= maxDecodedDataLen_):
                    raise Exception('Not enough space to store decoded data')

            self._update_range_tags(currentSymbol, symbolCumulativeCount)
            self._rescale()

        return self.mDecodedDataLen