from collections import deque
import numpy as np

class Smooth:

    # Smooth class with outlier removal, only numpy

    # Length: Length of the smoothing window
    # Threshold: number STD above which to take out outliers

    def __init__(self, length,threshold):
        self.length = length
        self.threshold = threshold
        self.data = deque([],length)

    def add_zscore(self,number):

        # Adds a number if it is not an outlier
        # Returns the mean of the window

        if len(self.data) < self.length: # array still not full
            self.data.appendleft(number)
        else:
            if np.std(self.data)>0.1: # because of quantification deque could be std very small
                if np.abs(number-np.mean(self.data)) < self.threshold * np.std(self.data):
                    self.data.appendleft(number)
            else: # all the same, std = 0 -> reset
                self.data.clear()
        return np.mean(self.data)


    def add_step(self,number):

        # Adds a number if it is not more than threshold away from previous number
        # Returns the mean of the window

        if len(self.data) == 0: # array still not full
            self.data.appendleft(number)
        else:
            if np.abs(number-self.data[0])<self.threshold:
                self.data.appendleft(number)
        return np.mean(self.data)
