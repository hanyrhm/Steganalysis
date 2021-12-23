from stegano import lsb
import glob

def stego_txt_lsb(src, text, result):
    secret_images = []
    with open (text, 'rb') as t:
        message = t.read()
        message = message[:14636] #5780=10%, 8754=15%, 11696=20%, 14636=25% 
    for img in glob.glob(src+'/*'):
        secret = lsb.hide(img, message)
        secret_images.append(secret)
    
    for (i, new) in enumerate(secret_images):
        new.save('{}{}{}{}'.format(result, '/stego_', i+1,'.png'))

stego_txt_lsb('the flickr30k/flickr30k_images/resized_1', 'text_msg/long_text.txt', 'the flickr30k/flickr30k_images/resized_stego_25')