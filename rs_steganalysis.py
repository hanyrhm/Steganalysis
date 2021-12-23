import sys
import math
import os
import pandas as pd
import glob
from PIL import Image

def main():
    list_result = []
    file_path = input("input your file_path: ")
    result_csv = input("input your path of file csv that you want to save: ")
    
    # Mask yang digunakan
    best_mask = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]

    # the discriminator overlap controls if the mask overlaps with adjacent pixels
    discriminator_overlap = 0

    list_image = []
    for filename in os.listdir(file_path):
        list_image.append(filename)

    for file in glob.glob(file_path + '/*'):
        img_file = Image.open(file)
        
        list_result.append(analyseimage(img_file, best_mask, discriminator_overlap))

    dict = {'image_name' : list_image, 'probability' : list_result}
    df = pd.DataFrame(dict)

    df.to_csv(result_csv)

# fungsi diskriminasi untuk melihat the smoothness of pixels
def discrimination_function(group):

    # initialise variables
    amount = 0
    totalrow = len(group)
    totalcolumn = len(group[0])

    # cycles through the columns using the discrimination function
    for row in range(0, totalrow):
        for column in range(0, totalcolumn):
            if column < (totalcolumn - 1):
                amount += abs(group[row][column] - group[row][column + 1])
    # cycles through the rows using the discrimination function
    for column in range(0, totalcolumn):
        for row in range(0, totalrow):
            if row < (totalrow - 1):
                amount += abs(group[row][column] - group[row + 1][column])
    return amount

# this applies the mask to the group of pixels
def groupmask(gmask, mask):

    # initialise the new mask variable
    newgroupmask = []

    # adds to the list for the new mask
    for line in gmask:
        newgroupmask.append(list(line))

    # sets the row and column values
    totalrow = len(newgroupmask)
    totalcolumn = len(newgroupmask[0])

    # adds/subtracts from the group depending on if it is divisible by 2 (mod2)
    for row in range(0, totalrow):
        for column in range(0, totalcolumn):
            if newgroupmask[row][column] % 2 == 0:
                newgroupmask[row][column] += mask[row][column]
            else:
                newgroupmask[row][column] -= mask[row][column]

    # returns the calculated mask
    return newgroupmask


# this function takes an array of pixel values and returns a small group based on the provided position
# based on RS steganalysis project by Brandon Hurst
def breakimage(imagearray, maskk, position):

    # initiate a new list
    brokeimage = []

    # adds each line to the list
    for line in maskk:
        brokeimage.append(list(line))

    # cycles through the image with the chosen mask to break the image
    for temprow in range(0, len(maskk)):
        for tempcol in range(0, len(maskk[0])):
            brokeimage[temprow][tempcol] = imagearray[temprow + position[0]][tempcol + position[1]]

    return brokeimage


# this function takes an image and splits the colours into separate arrays
# based on RS steganalysis project by Brandon Hurst
def splitpixels(img):

    # initialises number of pixels and the list for each colour
    pixnum = 0
    redrow = []
    greenrow = []
    bluerow = []
    red = []
    green = []
    blue = []

    # the get data function is used to retrieve the value of each pixel in the image
    rgb = img.getdata()

    # using the getdata function the pixel values are split into red, green and blue values
    for pix in rgb:

        # the position of the value is used to determine if it is red, green or blue
        redrow.append(pix[0])
        if len(pix) > 1:  # incase the image is grayscale
            greenrow.append(pix[1])
            if len(pix) > 2:  # incase the image is grayscale
                bluerow.append(pix[2])
        pixnum += 1

        # adds the separated pixel values to a list
        if pixnum % img.size[0] == 0:
            red.append(redrow)
            redrow = []
            if len(pix) > 1:  # incase the image is grayscale
                green.append(greenrow)
                greenrow = []
                if len(pix) > 2:  # incase the image is grayscale
                    blue.append(bluerow)
                    bluerow = []
    #print(pixnum, " pixels")

    return red, green, blue


# determines the percent of pixels with embedded information
# based on RS steganalysis project by Brandon Hurst
def analyseimage(img, chosen_mask, discriminator_overlap):

    # initiating the negative mask
    nmask = []

    # cycles through the selected mask, flipping the values to create the negative mask
    for line in chosen_mask:
        nmask.append(list(line))
    for row in range(0, len(nmask)):
        for column in range(0, len(nmask[0])):
            if nmask[row][column] == 1:
                nmask[row][column] = -1
            elif nmask[row][column] == -1:
                nmask[row][column] = 1

    # calls the splitpixels function to calculate and split the values of rgb pixels
    redpix, greenpix, bluepix = splitpixels(img)

    # analyses the red pixels to determine what percent of them may contain embedded content
    redpercent = analyseLSBs(redpix, chosen_mask, nmask, discriminator_overlap)

    # analyses the green pixels to determine what percent of them may contain embedded content
    greenpercent = analyseLSBs(greenpix, chosen_mask, nmask, discriminator_overlap)

    # analyses the blue pixels to determine what percent of them may contain embedded content
    bluepercent = analyseLSBs(bluepix, chosen_mask, nmask, discriminator_overlap)

    failed = 0
    if redpercent == 0:
        failed += 1
        print("Unable to calculate the percent of red encoded pixels")
    else:
        failed += 0
    if greenpercent == 0:
        failed += 1
        print("Unable to calculate the percent of green encoded pixels")
    else:
        failed += 0
    if bluepercent == 0:
        failed += 1
        print("Unable to calculate the percent of blue encoded pixels")
    else:
        failed += 0

    if failed == 3:
        encodedpercent = "?"
    else:
        # calculates and displays the total percentage of pixels that are likely to be encoded
        encodedpercent = (redpercent + greenpercent + bluepercent) / (3 - failed)

    return redpercent, bluepercent, greenpercent, encodedpercent


# analyse a specific array of pixel values
# based on RS steganalysis project by Brandon Hurst
def analyseLSBs(imagebox, chosen_mask, neg_mask, discriminator_overlap):

    # initialises all the regular and singular groups
    r_p2 = 0
    s_p2 = 0
    r_1p2 = 0
    s_1p2 = 0
    neg_r_p2 = 0
    neg_s_p2 = 0
    neg_r_1p2 = 0
    neg_s_1p2 = 0

    # reassigns the image box and chosen mask into more usable variables
    imrow = len(imagebox)
    imcol = len(imagebox[0])
    maskrow = len(chosen_mask)
    maskcol = len(chosen_mask[0])

    # determine how many groups of pixels will need to be analysed
    if discriminator_overlap:
        # this method is used if discriminator boxes overlap(box shifts by one pixel each time)
        num = float((imrow - maskrow + 1) * (imcol - maskcol + 1))
    else:
        # used of the discriminator boxes are unique
        num = float((imrow - imrow % maskrow) / maskrow * (imcol - imcol % maskcol) / maskcol)

    #print("number of groups to check = ", int(num))

    # initiates the counter
    numcount = 0

    # go row by row through pixel array
    for row in range(0, imrow):

        # then go column by column through pixel array
        for column in range(0, imcol):
            # this set of boxes and calculations is used for overlapping groups
            if discriminator_overlap:
                if row <= imrow - maskrow:
                    if column <= imcol - maskcol:
                        # this is the start of a group
                        pos = [row, column]
                        numcount += 1
                        breakimagebox = breakimage(imagebox, chosen_mask, pos)

                        # semua LSB didflip
                        flip_box = []
                        for line in breakimagebox:
                            flip_box.append(list(line))
                        for fliprow in range(0, len(breakimagebox)):
                            for flipcolumn in range(0, len(breakimagebox[0])):
                                if breakimagebox[fliprow][flipcolumn] % 2 == 0:
                                    flip_box[fliprow][flipcolumn] += 1
                                elif breakimagebox[fliprow][flipcolumn] % 2 == 1:
                                    flip_box[fliprow][flipcolumn] += -1

                        # menghitung nilai diskriminan
                        discr_breakimagebox = discrimination_function(breakimagebox)
                        discr_mask_breakimagebox = discrimination_function(groupmask(breakimagebox, chosen_mask))
                        discr_neg_mask_breakimagebox = discrimination_function(groupmask(breakimagebox, neg_mask))
                        discr_flip_box = discrimination_function(flip_box)
                        discr_mask_flip_box = discrimination_function(groupmask(flip_box, chosen_mask))
                        discr_neg_mask_flip_box = discrimination_function(groupmask(flip_box, neg_mask))

                        # klasifikasi grup regular dan singular
                        if discr_breakimagebox > discr_mask_breakimagebox:
                            s_p2 += 1
                        elif discr_breakimagebox < discr_mask_breakimagebox:
                            r_p2 += 1

                        if discr_breakimagebox > discr_neg_mask_breakimagebox:
                            neg_s_p2 += 1
                        elif discr_breakimagebox < discr_neg_mask_breakimagebox:
                            neg_r_p2 += 1

                        if discr_flip_box > discr_mask_flip_box:
                            s_1p2 += 1
                        elif discr_flip_box < discr_mask_flip_box:
                            r_1p2 += 1

                        if discr_flip_box < discr_neg_mask_flip_box:
                            neg_r_1p2 += 1
                        elif discr_flip_box > discr_neg_mask_flip_box:
                            neg_s_1p2 += 1

            # used for non-overlapping groups
            else:
                if (row + 1) % maskrow == 0:
                    if (column + 1) % maskcol == 0:
                        # this is the start of the group
                        pos = [row - maskrow + 1, column - maskcol + 1]
                        numcount += 1
                        breakimagebox = breakimage(imagebox, chosen_mask, pos)

                        # semua LSB diflip
                        flip_box = []
                        for line in breakimagebox:
                            flip_box.append(list(line))
                        for fliprow in range(0, len(breakimagebox)):
                            for flipcolumn in range(0, len(breakimagebox[0])):
                                if breakimagebox[fliprow][flipcolumn] % 2 == 0:
                                    flip_box[fliprow][flipcolumn] += 1
                                elif breakimagebox[fliprow][flipcolumn] % 2 == 1:
                                    flip_box[fliprow][flipcolumn] += -1

                        # menghitung nilai diskriminan
                        discr_breakimagebox = discrimination_function(breakimagebox)
                        discr_mask_breakimagebox = discrimination_function(groupmask(breakimagebox, chosen_mask))
                        discr_neg_mask_breakimagebox = discrimination_function(groupmask(breakimagebox, neg_mask))
                        discr_flip_box = discrimination_function(flip_box)
                        discr_mask_flip_box = discrimination_function(groupmask(flip_box, chosen_mask))
                        discr_neg_mask_flip_box = discrimination_function(groupmask(flip_box, neg_mask))

                        # melakukan klasifikasi grup regular dan singular
                        if discr_breakimagebox > discr_mask_breakimagebox:
                            s_p2 += 1
                        elif discr_breakimagebox < discr_mask_breakimagebox:
                            r_p2 += 1

                        if discr_breakimagebox > discr_neg_mask_breakimagebox:
                            neg_s_p2 += 1
                        elif discr_breakimagebox < discr_neg_mask_breakimagebox:
                            neg_r_p2 += 1

                        if discr_flip_box > discr_mask_flip_box:
                            s_1p2 += 1
                        elif discr_flip_box < discr_mask_flip_box:
                            r_1p2 += 1

                        if discr_flip_box < discr_neg_mask_flip_box:
                            neg_r_1p2 += 1
                        elif discr_flip_box > discr_neg_mask_flip_box:
                            neg_s_1p2 += 1

    if num == 0:
        return 0

    # definisi variabel yang digunakan pada persamaan kuadrat
    d0 = float(r_p2 - s_p2) / num
    dn0 = float(neg_r_p2 - neg_s_p2) / num
    d1 = float(r_1p2 - s_1p2) / num
    dn1 = float(neg_r_1p2 - neg_s_1p2) / num

    a = 2 * (d1 + d0)
    b = (dn0 - dn1 - d1 - 3 * d0)
    c = (d0 - dn0)

    if b * b < 4 * a * c:
        # nilai akar tidak boleh sama dengan nol
        message_length = 0
    elif a == 0:
        # jika nilai akar dibagi nol
        message_length = 0
    else:
        quadratic_solution1 = (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
        quadratic_solution2 = (-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)
        if abs(quadratic_solution1) < abs(quadratic_solution2):
            quadratic_solution = quadratic_solution1
        else:
            quadratic_solution = quadratic_solution2
        # p = x/(x−1/2), where p is message length
        message_length = abs(quadratic_solution / (quadratic_solution - 0.50))

    return message_length

main()
