import patoolib
from patoolib import *
import os
from PIL import Image
import tempfile
import shutil
import fitz # PyMuPDF
import contextlib
from _ePubMaker import EPubMaker


comic_archive_map = {"rar":"cbr","zip":"cbz","ace":"cba","7z":"cb7","tar":"cbt","epub":"epub","pdf":"pdf"}
comic_archive_types = ["cbr","cbz","cb7","cbt","cba","epub","pdf"]

def pad_to_length(number,length=3):
    return number.zfill(length)

def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()

def is_image(file):
    try:
        Image.open(file)
    except IOError:
        return False
    return True

def get_filename_without_extension(filename):
    return os.path.splitext(filename)[0]

def list_supported_formats():
    print()
    # https://github.com/AVeenstra/Images_To_ePub
    formats = {"epub":{"extact":"native python (zip)","create":"native python (Images_To_ePub)"},"pdf":{"extract":"native python (PyMuPDF)","create":"native python (Pillow)"}}
    for format in patoolib.ArchiveFormats:
        if format in comic_archive_map:
            print(comic_archive_map[format], "files:")
            for command in patoolib.ArchiveCommands:
                if command == "extract" or command == "create":
                    programs = patoolib.ArchivePrograms[format]
                    if command not in programs and None not in programs:
                        print("   %8s: - (not supported)" % command)
                        continue
                    try:
                        program = patoolib.find_archive_program(format, command)
                        print("   %8s: %s" % (command, program), end=' ')
                        if format == 'tar':
                            encs = [x for x in patoolib.ArchiveCompressions if patoolib.util.find_program(x)]
                            if encs:
                                print("(supported compressions: %s)" % ", ".join(encs), end=' ')
                        elif format == '7z':
                            if patoolib.util.p7zip_supports_rar():
                                print("(rar archives supported)", end=' ')
                            else:
                                print("(rar archives not supported)", end=' ')
                        print()
                    except patoolib.util.PatoolError:
                        # display information what programs can handle this archive format
                        handlers = programs.get(None, programs.get(command))
                        print("   %8s: - (no program found; install %s)" %
                            (command, patoolib.util.strlist_with_or(handlers)))
    for format in formats:
        print(f"{format} files:")
        for command in formats[format]:
            print("    ",command + ":",formats[format][command])
    print()

def is_archive(filename):
    file_extension = os.path.splitext(filename)[1].lower().strip(".")
    if file_extension in comic_archive_types:
        return True
    else:
        return False

def is_archive_type(filename,type):
    file_extension = os.path.splitext(filename)[1].lower().strip(".")
    if file_extension in comic_archive_map:
        if file_extension == type:
            return True
    try:
        t = patoolib.get_archive_format(filename)
        if t in comic_archive_map:
            t = comic_archive_map[t]
        if t == type:
            return True
        else:
            return False
    except:
        return False
        
def extract_pdf_to_temp(file,zoom=1):
    filename = os.path.splitext(os.path.basename(file))[0]
    tmpfldr = os.path.join(tempfile.gettempdir(),filename)
    if os.path.exists(tmpfldr):
        shutil.rmtree(tmpfldr)
    os.makedirs(tmpfldr)
    pdf_file = fitz.open(file)
    mat = fitz.Matrix(zoom,zoom)  # 72(defailt pdf dpi) * zoom
    for page_index in range(len(pdf_file)):
        page = pdf_file.loadPage(page_index)  # number of page
        pix = page.getPixmap(matrix=mat)
        extract_path = os.path.join(tmpfldr,f"{filename}-{pad_to_length(str(page_index+1),3)}.png")
        print(f"Extracting page {str(page_index+1)} to {extract_path} at {zoom}x zoom")
        pix.writePNG(extract_path)
    return tmpfldr

def remove_subfolders(dir):
    for subdir, dirs, files in os.walk(dir):
        for file in files:
            filepath = subdir + os.sep + file
            if os.path.dirname(filepath) != dir: 
                print(os.path.dirname(filepath),dir)
                shutil.move(filepath,dir)
        if len(os.listdir(subdir)) == 0:
            shutil.rmtree(subdir)

def dir_to_pdf(folder,file):
    imglist = []
    for img in os.listdir(folder):
        try:
            image = Image.open(img)
            im = image.convert("RGB")
            imglist.append(im)
        except Exception as e:
            print(f"Could not add {img} to PDF: {e}")
    first = imglist[0]
    imglist.remove(first)
    first.save(file,save_all=True,append_images=imglist)
    print(f"{file} created")
    return file

def dir_to_epub(folder,file,metadata):
    name = os.path.splitext(os.path.basename(file))[0]
    publisher = "ComicTools"
    if metadata != None:
        name = metadata["issueName"]
        publisher = metadata["publisher"]
    EPubMaker(
                master=None, input_dir=folder, file=file, name=name,publisher=publisher,
                grayscale=False, max_width=None,
                max_height=None, progress=False,
                wrap_pages=True
            ).run()

def extract_to_temp(file,pdf_zoom=1):
    filename = os.path.splitext(os.path.basename(file))[0]
    tmpfldr = os.path.join(tempfile.gettempdir(),filename)
    if os.path.exists(tmpfldr):
        shutil.rmtree(tmpfldr)
    os.makedirs(tmpfldr)
    folder = ""
    if is_archive_type(file,"pdf"):
        folder = extract_pdf_to_temp(file,pdf_zoom)
    else:
        folder = patoolib.extract_archive(file,outdir=tmpfldr)
    if is_archive_type(file,"epub"):
        epubfolder = folder + "_epub"
        os.makedirs(epubfolder,exist_ok=True)
        for subdir, dirs, files in os.walk(folder):
            for file in files:
                filepath = subdir + os.sep + file
                if is_image(filepath):
                    basename = os.path.splitext(file)[0]
                    if basename.lower() == "cover":
                        extension = os.path.splitext(file)[1]
                        file = f"_cover{extension}"
                    newpath = os.path.join(epubfolder,file)
                    shutil.copy(filepath,newpath)
        shutil.rmtree(folder)
        folder = epubfolder
    return folder

def dir_to_archive(dir,newfile,metadata=None,overwrite_existing=True,remove_dir=True):
    files = tuple(os.listdir(dir))
    olddir = os.getcwd()
    os.chdir(dir)
    try:
        if os.path.isfile(newfile):
            if overwrite_existing:
                os.remove(newfile)
                if is_archive_type(newfile,"pdf"):
                    dir_to_pdf(dir,newfile)
                elif is_archive_type(newfile,"epub"):
                    dir_to_epub(dir,newfile,metadata)
                else:
                    patoolib.create_archive(newfile,files)
        else:
            if is_archive_type(newfile,"pdf"):
                    dir_to_pdf(dir,newfile)
            elif is_archive_type(newfile,"epub"):
                    dir_to_epub(dir,newfile,metadata)
            else:
                patoolib.create_archive(newfile,files)
    finally:
        os.chdir(olddir)
        if remove_dir:
            shutil.rmtree(dir)
    return newfile
