from io import BytesIO
import win32clipboard, win32con,os,base64
from PIL import ImageGrab,Image,PngImagePlugin,BmpImagePlugin,ExifTags
from mime_types import get_mime_type
def send_to_clipboard(clip_type, data):
    """
    Send data to the computer's clipboard with the correct type
    """
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()




def get_clipboard():
    """
    Get the data from the computer's clipboard
    """ 
    result = {}
    file= ImageGrab.grabclipboard()
    #If file is None, the clipboard is empty or the clipboard data is not an image (probably text)
    if file!=None:
        if isinstance(file,list):             #check if it is a link to a file  
            file = fr'{ImageGrab.grabclipboard()[0]}'
            
            result['format'] = get_mime_type(file.split('.')[-1])
            result['type'] = 'filepath'
            result['data'] = file
            return result
        

                
        if isinstance(file,PngImagePlugin.PngImageFile) or isinstance(file,BmpImagePlugin.DibImageFile): #An image taken with snipingtool or WIN+SHIFT+S
            #On recupere le chemin du repertoire temporaire
            # On le convertit en BMP pour eviter les problemes de format et on la sauvgarde en binaire 
            data=BytesIO()
            file.convert("RGB").save(data, "BMP")
            result['type'] = 'screenshot'                                      
            result['format'] = 'image/bmp'
            result['data'] = data.getvalue()
            return result
        
   
    else:
        win32clipboard.OpenClipboard()
        result['type'] = 'text'
        result['format'] = 'text/plain'
        try:
            data = win32clipboard.GetClipboardData(win32con.CF_TEXT)

            result['data'] = data.decode('latin-1')
        except Exception as Error:
            print(Error)
            result['data'] = None

        win32clipboard.CloseClipboard()

        return result
    

def sendto_clipboard_as_file(filepath):
    """
    Sends the file sent by the requestor to the clipboard
    """
    try :
        command = f"powershell Set-Clipboard -LiteralPath {filepath}"
        print("\033[90mExecuting the following command :\n"+command+"\033[0m")
        os.system(command)
        return True
        
    except Exception as Error:
        print(Error)
        return False




def sendto_clipboard_as_text(text):
    """
    Sends the text sent by the requestor to the clipboard
    """
    try :
        send_to_clipboard(win32clipboard.CF_UNICODETEXT, text)
        return True
    except Exception as Error:
        print(Error)
        return False


def get_image_file_thumbnail(file):
    """
    Get the thumbnail of an image file, and return it as base64 
    """
    try :
        img = Image.open(file)
        for orientation in ExifTags.TAGS.keys() : 
            if ExifTags.TAGS[orientation]=='Orientation' : break 
        exif=dict(img._getexif().items())

        if   exif[orientation] == 3 : 
            img=img.rotate(180, expand=True)
        elif exif[orientation] == 6 : 
            img=img.rotate(270, expand=True)
        elif exif[orientation] == 8 : 
            img=img.rotate(90, expand=True)

        # We use the size of the original image to keep the same aspect ratio
        size=(img.size[0]//10,img.size[1]//10)
        img.thumbnail(size)
        #We return it as base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img.close()
        return base64.b64encode(buffered.getvalue()).decode('latin-1')

    except Exception as Error:
        print(Error)
        return False
