import cv2
import numpy as np
import os


class step1(object):

    LAPOFGAUSS_BLUR_SIZE = 7

    def __init__(self, img, **kwargs):
        # load img
        self.img = img
        self.step_img = self.img.copy()

    def process(self):
        '''
        correct_brightness: Remove noise from image, enhance edges
        '''
        print('Starting step1')
        # make background mask
        self.make_convoluted_mask()
        inverted_mask = cv2.bitwise_not(self.conv_mask)

        # split channels
        # channels = cv2.split(self.img)
        # split a costly operation (in terms of time).
        # Numpy indexing is much more efficient.
        blue = self.step_img[:,:,0]
        green = self.step_img[:,:,1]
        red = self.step_img[:,:,2]
        channels = [blue, green, red]

        for idx,channel in enumerate(channels):

            # remove masked region from channel[i]
            channel = cv2.subtract(channel, inverted_mask)

            # maintain aspect ratio
            r = 196.0 / channel.shape[1];

            # shrink image down
            conv = cv2.resize(channel,
                              dsize=(0,0),
                              fx = r,
                              fy = r,
                              interpolation = cv2.INTER_AREA
            )

            # reduce noise while maintaining edges
            conv = cv2.medianBlur(conv, 11)

            # scale image back up to original dimensions
            conv = cv2.resize(
                conv,
                dsize=(channel.shape[1],channel.shape[0]),
                fx = 0,
                fy = 0,
                interpolation=cv2.INTER_LINEAR
            );

            # Extract Foreground mask
            # channel = 255*(conv/self.conv_mask) - channel;
            div = cv2.divide(conv, self.conv_mask)
            channel = cv2.subtract(div*255, channel)

            # Normalise image
            cv2.normalize(
                src = channel,
                dst = channel,
                alpha = 0,
                beta = 255,
                norm_type = cv2.NORM_MINMAX,
                dtype = -1,
                mask = self.conv_mask
            );

            # Subtract positive Laplacian of Gaussian
            channels[idx] = self.subtract_Lap_of_gaussian(channel, step1.LAPOFGAUSS_BLUR_SIZE)

        # merge all channels into grayscale step_img and return
        return cv2.cvtColor(cv2.merge(channels), cv2.COLOR_BGR2GRAY)

    def make_convoluted_mask(self):
        ''' All "mask" white image of size original(rows,col) '''
        self.conv_mask = np.full(
            (self.img.shape[0], self.img.shape[1]),
            255,
            dtype = "uint8"
        )

    def subtract_Lap_of_gaussian(self, img_in, blur_size):
        '''
        Find and enhance edges of colonies using Laplacian of Gaussian
        '''
        temp_mat = cv2.GaussianBlur(img_in, (blur_size, blur_size), 3)
        temp_mat = cv2.Laplacian(temp_mat, ddepth=cv2.CV_8U, ksize=5, scale=0.3)
        ret, temp = cv2.threshold(temp_mat, 10, 255, cv2.THRESH_BINARY) # <-- WHY ?? hardcoded
        contoursToDraw = []

        #find contours
        _, contours, hierarchy = cv2.findContours(
            temp,
            mode=cv2.RETR_CCOMP,
            method=cv2.CHAIN_APPROX_SIMPLE
        )

        hierarchy = hierarchy[0]
        for idx,cnt in enumerate(contours):
            # if the contour has no holes and if it is not a hole
            if hierarchy[idx][2] < 0 and hierarchy[idx][3] < 0:

                contoursToDraw.append(cnt)
                x,y,w,h = cv2.boundingRect(contoursToDraw[0])
                cv2.drawContours(
                    temp_mat,
                    contoursToDraw,
                    0,
                    (0,0,0),      # color
                    thickness=-1, # fill contours
                    lineType=8,
                    maxLevel=1,
                    #offset=(-x, -y) # shift all contours by (x,y)
                )
                contoursToDraw.pop()

        out_img = cv2.subtract(img_in, temp_mat)
        return out_img

if __name__ == '__main__':
    img = 'test_images/good_3.jpg'
    img_path = os.path.abspath(img)
    print(img_path)
    cc = step1(img_path)
    cc.process()

