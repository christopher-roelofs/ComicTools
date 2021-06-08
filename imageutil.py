from PIL import Image,ImageChops, ImageStat
import imagehash
import requests
from io import BytesIO
import base64
import os

def is_image(file):
    try:
        Image.open(file)
    except IOError:
        return False
    return True

def getImageFromUrl(url):
    image = requests.get(url,stream=True)
    return Image.open(image.raw).convert('RGB')

def convert_image(file,type):
    type = type.lower()
    extension = os.path.splitext(file)[1].strip(".").lower()
    if  extension == type:
        print(f"Source image type of {os.path.basename(file)} is the same as target type, skippping conversion.")
        return True
    else:
        print(f"Converting {os.path.basename(file)} to {type}.")
    try:
        basename = os.path.splitext(file)[0]
        image = Image.open(file).convert('RGB')
        if type == "png":
            image.save(f"{basename}.png",save_all=True,optimize=True)
            return True

        elif type == "jpg":
            image.save(f"{basename}.jpg",quality=95,optimize=True)
            return True

        elif type == "webp":
            image.save(f"{basename}.webp",save_all=True,lossless=True,optimize=True)
            return True

        elif type == "gif":
            image.save(f"{basename}.gif",save_all=True)
            return True

        elif type == "tiff":
            image.save(f"{basename}.tiff",quality=100,save_all=True)
            return True

        elif type == "bmp":
            image.save(f"{basename}.bmp")
            return True
        else:
            print(f"Target type {type} not supported.")
            print("Supported image target types: png, jpg, webp, bmp, gif, tiff.")
            return False
        
    except Exception as e:
        return False

def convert_dir_to_type(dir,type):
    print(f"Converting image files to {type}.")
    converted = False
    type = type.lower()
    for subdir, dirs, files in os.walk(dir):
        for file in files:
            filepath = subdir + os.sep + file
            if is_image(filepath):
                if not os.path.splitext(file)[1].strip(".").lower() == type.lower():
                    if not convert_image(filepath,type):
                        return False
                    os.remove(filepath)     
                else:
                    print(f"Source image type of {os.path.basename(file)} is the same as target type, skippping conversion.")         
    return True

def compare_images(image1,image2):
    image1 = image1
    image2 = image2
    width1, height1 = image1.size
    width2, height2 = image2.size
    if width1*height1 > width2*height2:
        image2 = image2.resize((width1,height1))
    else:
        image1 = image1.resize((width2,height2))
    hash1 = imagehash.phash(image1) 
    hash2 = imagehash.phash(image2)
    difference = hash1 - hash2  
    return (100 - difference)

def compare_images2(image1,image2):
    image1 = image1
    image2 = image2
    width1, height1 = image1.size
    width2, height2 = image2.size
    if width1*height1 > width2*height2:
        image2 = image2.resize((width1,height1))
    else:
        image1 = image1.resize((width2,height2))
    diff_img = ImageChops.difference(image1, image2)
    stat = ImageStat.Stat(diff_img)
    diff_ratio = sum(stat.mean) / (len(stat.mean) * 255)
    return round(100 - diff_ratio * 100) 

def compare_images3(image1,image2):
    image1 = image1
    image2 = image2
    width1, height1 = image1.size
    width2, height2 = image2.size
    if width1*height1 > width2*height2:
        image2 = image2.resize((width1,height1))
    else:
        image1 = image1.resize((width2,height2))
    diff_img = ImageChops.difference(image1, image2)
    black_and_white_version = diff_img.convert('1')
    black_pixels = black_and_white_version.histogram()[0]
    total_pixels = diff_img.size[0] * diff_img.size[1]
    similarity_ratio = black_pixels / total_pixels
    return round(similarity_ratio * 100)

if __name__ == "__main__":
    dir = "D:\Downloads\Way Of X #002 (2021)"
    print(convert_dir_to_type(dir,"png"))
