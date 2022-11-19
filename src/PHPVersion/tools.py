import webbrowser, time,win32clipboard,pillow_heif,sys,os,win32con,re,urllib.request
from io import BytesIO

from PIL import ImageGrab,Image,PngImagePlugin,BmpImagePlugin

def send_to_clipboard(clip_type, data):
    """
    Send data to the computer's clipboard with the correct type
    """
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()
    #on recupere ce qu'il ya dans le presse papier


def get_clipboard():
    """
    Get the data from the computer's clipboard
    """ 
    img= ImageGrab.grabclipboard()
    #If img is None, the clipboard is empty or the clipboard data is not an image (probably text)
    if img!=None:
        prefix="aXRzYWZpbGVwYXRo" #base64 encoded "itsafilepath" to avoid conflict with text                                          
        if isinstance(img,list):                             #check if it is a link to a file  
            img = fr'{ImageGrab.grabclipboard()[0]}'
            return('aXRzYWZpbGVwYXRo'+img)
                
        if isinstance(img,PngImagePlugin.PngImageFile) or isinstance(img,BmpImagePlugin.DibImageFile): #An image taken with snipingtool or WIN+SHIFT+S
            #On recupere le chemin du repertoire temporaire
            filename=".\\temp\\capture.bmp"
            img.convert("RGB").save(filename, "BMP")
        
            return (prefix+filename)
            #print("It was an Image but needed to be converted")
   
    else:
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
        win32clipboard.CloseClipboard()
        #On creer un fichier dans ./temp
        filename=".\\temp\\outclipboard.txt"
        try:
            with open(filename, "w",encoding='utf-8') as f:
                f.write(data.decode('unicode_escape'))
        except Exception as Error:
            return Error
        return (filename)




    
def open_url(file):
    """
    Opens a url in the default browser the url is stored in the file in parameter
    """
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


    try:
        with open(file, "r",encoding='utf-8') as f:
            data=f.read()
        if not data.startswith("http"):
            data="http://"+data

        if re.match(regex,data) is not None:
            webbrowser.open(data)
            res= True
        else:
            res="Invalid URL"
    except Exception as Error:
        res=Error
    os.remove(file)
    return res


def sendto_clipboard_as_file(file):
    """Sends the image sent by the requestor to the clipboard if possible, not all formats are supported.\n
    Still need fix because BMP file size is way too big (1MB heif -> 11MB bmp))
    """
    try :
        pillow_heif.register_heif_opener() #register the HEIF format comming from IOS
        img=Image.open(file)
        output = BytesIO()
        img.convert("RGB").save(output, "BMP")
        img.close()
        data = output.getvalue()[14:]
        output.close()
        send_to_clipboard(win32clipboard.CF_DIB, data)
        res= True
        os.remove(file) 
    except Exception as Error:
        res=sendto_clipboard_as_text(file)

    return res



def sendto_clipboard_as_text(file):
    """
    Retrieves the data from the client's clipboard
    """
    try :
        with open(file, "r",encoding='utf-8') as f:
            data=f.read()
        send_to_clipboard(win32clipboard.CF_UNICODETEXT, data)
        res= True
        os.remove(file)
    except Exception as Error:
        print(Error)
        res= False

    return res



def delete_temp_files(file):
    """
    Deletes the temporary files created by the program
    """
    try:
        time.sleep(3)
        os.remove(file)
        res= True
    except Exception as Error:
        res=Error
    return res




#On recupere les arguments du script
args = sys.argv[1:]
if len(args) == 0:
    print("No arguments")
    sys.exit(1)


if args[0] == 'send_to_clipboard':
    print(send_to_clipboard(args[1], args[2]))
elif args[0] == 'get_clipboard':
    print(get_clipboard())
elif args[0] == 'open_url':
    print(open_url(args[1]))
elif args[0] == 'sendto_clipboard_as_file':
    print(sendto_clipboard_as_file(args[1]))
elif args[0] == 'sendto_clipboard_as_text':
    print(sendto_clipboard_as_text(args[1]))
elif args[0] == 'delete_temp_files':
    print(delete_temp_files(args[1]))
