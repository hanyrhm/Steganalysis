from PIL import Image
import glob

image_list = []
resized_image = []

for filename in glob.glob('the flickr30k/flickr30k_images/cover/*.png'):
    img = Image.open(filename)
    image = img.resize((400,400))
    resized_image.append(image)

for (i, new) in enumerate(resized_image):
    new.save('{}{}{}'.format('the flickr30k/flickr30k_images/resized_1/cover', i+1,'.png'))