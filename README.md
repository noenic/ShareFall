# Welcome to ShareFall!
What is ShareFall ? ShareFall is an application that aims to give a lot of the untouchable features of Airdrop to Windows users. 

You will need this shortcut :
- ✔ The latest shortcut can be downloaded 🟩[here](https://www.icloud.com/shortcuts/b08169c668154fdf84d153b5f71674b8)🟩 (v1.5)
- 🇩🇪 Thanks to [@Soljanka](https://github.com/Soljanka) for a German translation of the shortcut and can be downloaded 🟩[here](https://www.icloud.com/shortcuts/32b8421080d6413bb2353cb14934215b)🟩 (v1.5)

# Why ShareFall ?
Some people like the Apple ecosystem but are not attracted by MacOS.
Content sharing between IOS and other operating systems is always annoying.  Snapdrop was a good alternative but doesn't offer as good integration as I hope ShareFall will, plus snapdrop doesn't work all the time. 


# What can it do ?

 

 - [x] Exchange Clipboards between iOS and Windows <br>
		 - 💻->📱Files stored in Windows's clipboard can be transfered to iOS devices (Image, Video, PDF, Text, Zip, ect..)<br>
		 - 📱->💻For now only text and Images can be transfered from iOS devices to Windows computers clipboards

 - [x] File transfert <br>
		 - 💻 The Windows computer hosts an HTTP server, you can access the files stored in the **Share** folder by going to the website of the machine with its IP address, Or by storing the file in the clipboard and send it to the iOS device.<br>
		 - 📱iOS devices send the file with a POST request to the HTTP server and are saved in the **Share** folder.
	
- [x] Urls <br>
	     - 💻->📱copy the URL to the clipboard on the computer and retrieve it on the iOS device. The shortcut will detect the URL and display a prompt to open it in Safari.<br>
	     - 📱->💻a prompt will ask you if you want to copy the URL to the computer's clipboard or open it in its default browser.
- [ ] Good **GUI** <br>
		- 📱it is only a shortcut in the shortcut application, and can be accessed from the share sheet or by running the shortcut.<br>
		- 💻I have for project to create a HTML page allowing to visualize easily all the files in the folder **share** and to download and upload files. it remains a WIP
	
## Some Screenshots
Default prompt when launching the shortcut from the shortcut app
![default prompt](https://github.com/noenic/ShareFall/blob/main/images/generic_prompt.jpeg?raw=true)

When you retrieve the clipboard from the computer and its a URL
![received url](https://github.com/noenic/ShareFall/blob/main/images/is_that_a_url.jpeg?raw=true)

When you retrieve the clipboard from the computer and its an Image<br>
![received url](https://github.com/noenic/ShareFall/blob/main/images/get_image_from_PC_clipboard.png?raw=true)
![clipboard_share](https://github.com/noenic/ShareFall/blob/main/images/clipboard_share.gif?raw=true)

**More screenshots coming later**

## How does it work ?

it's simply a python program hosting an [http server](https://github.com/Densaugeo/uploadserver) on your computer 💻 with the possibility to upload files (<i>the python code is sourced from the linked repo with the addition of specific code to use ShareFall. The application uses all the backend of the uploadserver module, so it inherits all the other characteristics.</i>).
To be honest the my side of the code is far from excellent and not the most optimized, any suggestion for improvement will be  highly appreciated.

On the iOS device📱 it is a  shortcut of a hundred blocks long that does almost all the actions. This shortcut file is not the most optimized either but it's really hard to do something clean with an application that crashes randomly after 40 blocks and that has no real if-else statement and true variable management. One day I will switch some parts to scriptable 



## Any drawbacks?

 - A bug with the shortcut application that asks for authorization all the time even though you have already given it

- You can't directly send data to the iOS device, at least not with a shortcut, the device must always request it first and then the server will send the requested content, a bit stupid in some situations.

- The shortcut application can determine the type of file received (pdf, zip, etc...) and place it in the clipboard. But I have not yet found a way to determine the binary file received by the python program and place it in the windows clipboard, for the moment only text and image files can be placed in windows clipboard

- The IP system needs to be reworked, the goal is that everything works regardless of the network.
	(Added a workaround, see below in the configuration section) 

- Some parts of the shortcut are based on text in an entry, normally it should work with English and French language devices.
If you ever use another language you will have to modify the text comparison

- it looks like https doesn't want to work properly because the shortcut request action doesn't allow self-signed certificates. Another dumb thing since certificates can be accepted on safari. 

- ⚠️ **Be aware that the requests are made in http and not https. The traffic is clear on the network. The token allows to prevent easy  manipulation of the server. However it is possible to see the token in clear if a http snitch is present.
I advise you to use this method only on trusted network or personal connection hotspot from your iPhone.
some features can be used for bad purposes.
Still working on it** ⚠️


## Configuration 
There is not much configuration.
if you don't have all the necessary dependencies, run : **pip install -r requirements.txt**

you can change the listening port and the token of the HTTP server in **ShareFallServer.bat** by default 80 and "token".

In the iOS shortcut add the IP of your machine and the listening port of the HTTP server.
In the dictionary add the IP, The network name will be the key and the computer ip will be the value.
The network name must be exactly the same.
One of the keys is empty, it is the case where your device is not connected to a WIFI network already filled, here put the address of your computer when it is in hotspot 

Don't forget to add the shortcut in the favorite tab of your Sharesheet
