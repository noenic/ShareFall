from flask import Flask, Response,send_file, request, render_template,redirect,logging as flog
import backend,argparse,os,logging,base64,tkinter as tk,webbrowser,re
from dotenv import dotenv_values

# Change the current directory to the directory of the script
os.chdir(os.path.dirname(__file__))
# Create the necessary folders if they don't exist
os.makedirs('share',exist_ok=True)
os.makedirs('temp/clipboard',exist_ok=True)

def logger(message,color):
    print(f"\033[{color}m{message}\033[0m")


app = Flask(__name__, static_folder='share')


def is_allowed():
    '''
    Check if the client is allowed to access the ressource
    '''
    passed_token = request.headers.get('token')
    client_ip = request.remote_addr
    if ((request.method == "GET" and request.path == "/share") or passed_token == TOKEN) and client_ip in ALLOWED_IP:
        return True
    elif client_ip not in ALLOWED_IP:
        logger(f"Unauthorized IP : {client_ip}\nAllowed IP : {ALLOWED_IP}", 31)
    else:
        logger(f"Unauthorized token from {client_ip}\nToken : {passed_token}", 31)
    return False




@app.route('/clipboard', methods=['GET'])
def get_clipboard():
    if not is_allowed():
        return Response("Unauthorized", status=401, mimetype="text/plain")
    
    clipboard_data = backend.get_clipboard()

    match clipboard_data['type']:
        case 'text':
            # We write in magenta the text in the log
            logger("sending text from clipboard :\n"+clipboard_data['data'], 35)
            return Response(clipboard_data['data'], mimetype="text/plain")
        
        case 'filepath':
            # We write in magenta the filepath in the log
            logger("sending file from clipboard :\n"+clipboard_data['data'], 35)
            return send_file(clipboard_data['data'], as_attachment=True)
        
        case 'screenshot':
            # We write in magenta the screenshot in the log
            logger("sending screenshot from clipboard", 35)
            return Response(clipboard_data['data'], mimetype=clipboard_data['format'])



@app.route('/clipboard', methods=['POST'])
def send_to_clipboard():
    if not is_allowed():
        return Response("Unauthorized", status=401, mimetype="text/plain")

    data = request.form
    if "text" in data:
        logger("sending text to clipboard :\n"+data['text'], 35)
        backend.sendto_clipboard_as_text(data['text'])

    if "file" in request.files:
        # We save the file in the temp folder
        file = request.files['file']
        # We need to sanitize the filename because apple add a lot of spaces in the filename
        filename = file.filename.replace(" ", "_")
        # We clear the clipboard folder before saving the file
        for files in os.listdir("temp/clipboard"):
            os.remove(f"temp/clipboard/{files}")
        file.save(f"temp/clipboard/{filename}")
        logger("sending file to clipboard :\n"+filename, 35)
        backend.sendto_clipboard_as_file(f"temp/clipboard/{filename}")


    return Response("OK", mimetype="text/plain")





@app.route('/share', methods=['POST'])
def share():
    if not is_allowed():
        return Response("Unauthorized", status=401, mimetype="text/plain")
    
    # We save the file in the share folder
    file = request.files['file']
    filename = file.filename.replace(" ", "_")
    file.save(f"share/{filename}")
    logger("File uploaded to share folder :\n"+filename, 35)
    if AUTO_OPEN_SHARE_FOLDER:
        logger("AUTO_OPEN_SHARE_FOLDER is set to true, opening the share folder", 35)
        logger("Executing the following command :\n"+f"explorer.exe /select,{os.path.join(os.getcwd(), 'share', filename)}", 90)
        # We open the share folder in the file explorer and select the file that has been uploaded
        os.system(f"explorer.exe /select,{os.path.join(os.getcwd(), 'share', filename)}")
    return Response("OK", mimetype="text/plain")


@app.route('/share', methods=['GET'])
def get_share():
    if not is_allowed():
        return Response("Unauthorized", status=401, mimetype="text/plain")
    
    # show the content of the share folder
    directory = 'share'
    files = []
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            file={
                "filename": filename[:15]+"..."+filename.split('.')[-1] if len(filename)>15 else filename,
                "url": f"/share/{filename}",
            }

            # We check if the file as an icon in the icon folder by using its extension
            if os.path.isfile(f"icons/{filename.split('.')[-1]}.svg"):
                # We get the icon as base64
                with open(f"icons/{filename.split('.')[-1]}.svg", "rb") as f:
                    file['icon'] = f"data:image/svg+xml;base64,{base64.b64encode(f.read()).decode()}"
            else:
                with open(f"icons/file.svg", "rb") as f:
                    file['icon'] = f"data:image/svg+xml;base64,{base64.b64encode(f.read()).decode()}"


            # If the file is a picture, we can display it as a thumbnail
            if filename.split('.')[-1].lower() in ['png', 'jpg', 'jpeg', 'bmp']:
                try:
                    img=backend.get_image_file_thumbnail(os.path.join(directory, filename))
                    # the function get_image_file_thumbnail return the image as base64
                    file['icon'] = f"data:image/png;base64,{img}"
                except:
                    logger(f"Could not get the thumbnail of the image {filename}", 31)
                



            files.append(file)
    logger("Showing the content of the share folder", 35)
    return render_template('file_browser.html', files=files)

    

@app.route('/browser', methods=['POST'])
def open_browser():
    if not is_allowed():
        return Response("Unauthorized", status=401, mimetype="text/plain")
    # We create a popup to ask the user if he wants to open the url in the browser,
    # CAN BE DISABLED BY SETTING AUTO_OPEN_BROWSER=1 IN THE ENV FILE
    # by default, the popup is shown and the user has to click on accept to open the url (for security reasons)
    def show_url_popup(url):
        root = tk.Tk()
        root.withdraw() 

        def open_url():
            logger("Opening the following url in the browser :\n"+url, 35)
            webbrowser.open(url)

        def accept():
            open_url()
            root.destroy()

        def refuse():
            logger("User refused to open the url in the browser", 35)
            root.destroy()

        # Create the popup
        popup = tk.Toplevel(root)
        popup.title("[ShareFall] Browser request")
        label = tk.Label(popup, text=f"The client {request.remote_addr} wants to open the following url in your default browser :\n{url}\n\n\n\nDo you want to accept?")
        label.pack(padx=20, pady=20)

        # Create the buttons
        accept_button = tk.Button(popup, text="Yes", command=accept)
        refuse_button = tk.Button(popup, text="No", command=refuse)
        accept_button.pack(side=tk.LEFT, padx=10, pady=10)
        refuse_button.pack(side=tk.RIGHT, padx=10, pady=10)

        popup.mainloop()
    # Appeler la fonction pour afficher la popup
    if AUTO_OPEN_BROWSER:
        logger("AUTO_OPEN_BROWSER is set to true, bypassing the popup", 35)
        logger("Opening the following url in the browser :\n"+request.form['url'], 35)
        webbrowser.open(request.form['url'])
    else:
        logger("AUTO_OPEN_BROWSER is set to false, asking for user permission", 35)
        show_url_popup(request.form['url'])

    return Response("OK", mimetype="text/plain")



#Redirect / to /share
@app.route('/', methods=['GET'])
def root():
    return redirect("/share")





if __name__ == '__main__':

    flog.default_handler.setFormatter(logging.Formatter("%(message)s")) # We remove the date and the level from the log
    default_values = dotenv_values()


    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="The token to access the server", default=default_values.get("TOKEN"))
    parser.add_argument("--allowed-ip", help="The ip allowed to access the server (separated by a comma)", default=default_values.get("ALLOWED_IP", "127.0.0.1"))
    parser.add_argument("--AUTO_OPEN_SHARE_FOLDER", help="Open the share folder when a file is sent", default=default_values.get("AUTO_OPEN_SHARE_FOLDER", 0), type=int, choices=[1, 0])
    parser.add_argument("--AUTO_OPEN_BROWSER", help="Open the browser when a url is sent", default=default_values.get("AUTO_OPEN_BROWSER", 0), type=int, choices=[1, 0])
    parser.add_argument("--port", help="The port to use", default=default_values.get("PORT", 28080), type=int)
    parser.add_argument("--host", help="The host to use", default=default_values.get("HOST", "127.0.0.1"))
    args = parser.parse_args()

    # Variables globales
    TOKEN = args.token if args.token is not None else logger("TOKEN is not set, please set it in a .env file or as an argument, use -h for help", 31) or exit(1)
    AUTO_OPEN_SHARE_FOLDER = bool(args.AUTO_OPEN_SHARE_FOLDER)
    AUTO_OPEN_BROWSER = bool(args.AUTO_OPEN_BROWSER)
    PORT = args.port
    HOST = args.host

    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", HOST) is None:
        logger(f"HOST : ({HOST}) is syntaxically incorrect. Example of correct syntax: : 127.0.0.1 or 0.0.0.0", 31)
        exit(1)
    
    if re.match(r"^\d{1,5}$", str(PORT)) is None:
        logger(f"PORT : ({PORT}) is syntaxically incorrect. Example of correct syntax: 8080", 31)
        exit(1)
    # Check if all the ip are correct (xxx.xxx.xxx.xxx,xxx.xxx.xxx.xxx)
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(,\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})*$", args.allowed_ip) is None:
        logger(f"ALLOWED_IP : ({args.allowed_ip}) is syntaxically incorrect. Example of correct syntax: 127.0.0.1,192.168.0.1", 31)
        exit(1)
    


    ALLOWED_IP = args.allowed_ip.split(',')

    logger(f"Server started on {HOST}:{PORT}\nToken : {'*' * len(TOKEN)}\nAllowed IP : {ALLOWED_IP}\nAUTO_OPEN_SHARE_FOLDER : {AUTO_OPEN_SHARE_FOLDER}\nAUTO_OPEN_BROWSER : {AUTO_OPEN_BROWSER}", 32)
    app.run(
            host=HOST,
            port=PORT
            )
