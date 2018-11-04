__author__ = 'Marko Milutinovic'

import math

def getMinBytesToRepresent(maxValue_):
    """
    Calculate the number of bytes required to represent the max value provided

    :param maxValue_: The maximum number that needs to be represented
    :return: Return the number of bytes required to represent max number
    """

    # If an invalid value is passed in return 0
    if(maxValue_ < 1):
        return 0

    if(maxValue_ == 1):
        return 1

    return math.ceil(math.ceil(math.log2(maxValue_)/8))

def calculateMaxBytes(wordSize_):
    """
    Calculate the max number of bytes we can compress before we are required
    to normalize the statistics during AR encoding

    :param wordSize_: The number of bits used when generating tags. Must be greater than 2 and less than or equal to 16 to produce a valid result
    :return: Return the max bytes before we need to normalize the statistics
    """

    # If an invalid value is passed in return 0
    if((wordSize_ <= 2) or (wordSize_ > 16)):
        return 0

    maxBytes = math.pow(2, (wordSize_ - 2))

    return int(maxBytes)
