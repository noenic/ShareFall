<?php
// Here put the IP adress of your iPhone or other device 
// It can be different IPs if you have more than one device or if you use your device on different networks
$authorized_ips = array("127.0.0.1",'192.168.0.1',"yyy.yyy.yyy.yyy","192.168.45.23");
//Here put the secret token
$token = "LovelyToken";



$headers = getallheaders();


if(!in_array($_SERVER['REMOTE_ADDR'],$authorized_ips)){
    phperror("request denied for Unauthorized IP: ".$_SERVER['REMOTE_ADDR']);
    header('HTTP/1.0 403 Forbidden');
    die("Unauthorized IP : ".$_SERVER['REMOTE_ADDR']);
    exit;
    
}

include 'mime_type.php';
set_time_limit(0); // unlimited max execution time

header('allow : GET, POST');
$method = $_SERVER['REQUEST_METHOD']; 
$headers = getallheaders(); 

switch ($method) {
    case 'GET':

        #---------      clipboard      ---------#
        /*
        Will send what is in the clipboard to the client
        It can be a file, a text, an image, etc...
        */

        if (isset($headers['clipboard'])){
            check_token();
            $output=shell_exec("py tools.py get_clipboard");
            //if the output begins with "aXRzYWZpbGVwYXRo" it means that the clipboard is a file 
            //Or you are extremely unlucky and the text you copied begins with this string
            if (substr($output,0,16) == "aXRzYWZpbGVwYXRo"){
                $filename=substr($output,16);
                $filename=substr($filename,0,-1);
                $filename=str_replace("\\", "/", $filename);
                if (!isset($mime_types[pathinfo($filename, PATHINFO_EXTENSION)])){
                    $mime_types[pathinfo($filename, PATHINFO_EXTENSION)]="application/octet-stream";
                }
                header('Content-Type:'.$mime_types[pathinfo($filename, PATHINFO_EXTENSION)]);
                header('Content-Disposition: attachment; filename='.basename($filename));
                header('Content-Length: ' . filesize($filename));
                phplog("The file ".$filename." will be sent to the client");
                    if (filesize($filename) > 50000000){ //if the file is bigger than 50MB
                        $taille = round(filesize($filename)/1000000,2)." MB";
                        if (filesize($filename) > 1000000000){  //if the file is bigger than 1GB
                            $taille = round(filesize($filename)/1000000000,2)." GB";
                        }
                        phplog("Its a big file you got there ! : ".$taille);
                    }
                    $handle = fopen($filename, "rb");
                    $status=0;
                    $i=0;
                    while (!feof($handle)) {
                        $i++;
                        if (round(ftell($handle)/filesize($filename)*100,0) % 20 == 0){
                            if (round(ftell($handle)/filesize($filename)*100,0) != $status){
                                $status = round(ftell($handle)/filesize($filename)*100,0);
                                phplog("file sending  : ".$status."%");

                            }
                        }
                        $buffer = fread($handle, 2048);
                        echo $buffer;
                        ob_flush();
                        flush();
                    }
                    fclose($handle);

                    //if the file sent was the temp image we delete it
                    if ($filename == "./temp/capture.bmp"){
                        unlink($filename);
                    }
                                   
            }
            
            else{
                //On recupere le contenu du fichier
                $filename="./temp/outclipboard.txt";
                $content = file_get_contents($filename);
                



                $taille=strlen($content);
                if ($taille > 200){
                    //on prend que le debut du texte
                    phplog("Text coming from the clipboard will be sent to the client:\n".substr($content,0,200)."...");
                }
                else{
                    phplog("Text coming from the clipboard will be sent to the client:\n".$content);
                }
                header('Location: ./temp/outclipboard.txt');

                /*We delete the file using python because PHP will delete it before the client can access it
                using python we wait 3 seconds before deleting the file
                */
                pclose(popen("start /B py tools.py delete_temp_files ".$filename, "r"));
                die();
                
                

                
                
                

                
            }
        }
                
            
        #---------      END  clipboard      ---------#
        #---------      Directory            ----------#
        /*
        Will send the content of the /share directory
        So the client can take a look at the files
        */
        else{
            if (isset($_GET['file'])){
                $file = ".\\share\\".$_GET['file'];
                //On regarde si le fichier existe
                if (file_exists($file)){
                    header('Location: '.$file);
                    //let the client browser open the file
                    
                }


            }
            else{
            //collect the content of the directory
            $content=scandir("./share");
            //we remove the "." and ".." directories
            unset($content[0]);unset($content[1]);
            //print the content of the directory in a html table
            echo "<html><head><title>Directory</title></head><body><h1 style=\"Text-Align: center\" >Directory</h1><ul>";

            foreach ($content as $file){
                echo "<li><a href='?file=".$file."'>".$file."</a></li>";
                }   
            echo "</ul></body></html>";
            }   
        }   
        break;

    case 'POST':
        check_token();
        if (isset($headers['clipboard'])){
            //If $_FILES is not empty then it's a file (duh)
            if (!empty($_FILES)){
                $file = $_FILES['file']['name'];
                phplog("File received : ".$file);
                move_uploaded_file($_FILES['file']['tmp_name'], "./temp/tempfile.".pathinfo($file, PATHINFO_EXTENSION));
                $output=shell_exec("py tools.py sendto_clipboard_as_file ./temp/tempfile.".pathinfo($file,PATHINFO_EXTENSION));
                if (strlen($output) == 5 ){
                    phplog("file sent to the clipboard");
                }

                else{
                    phperror("Error while sending the file to the clipboard");
                    phperror("It is currently impossible to send a file that is not an image or text in the clipboard");
                    pylog($output);
                    phperror("The file has been saved in the share directory");
                    //Move the file to the share directory 
                    rename("./temp/tempfile.".pathinfo($file, PATHINFO_EXTENSION), "./share/".$file);

                    //open the file in the file explorer
                    exec("start .\share");
                


                }
            }
        
            //It's text
            if (isset($_POST['text'])){
                $file = fopen("./temp/inclipboard.txt","w");
                fwrite($file,$_POST['text']);
                fclose($file);
                $taille=strlen($_POST['text']);
                if ($taille > 200){
                    phplog("Text received to be sent in the paper press\n".substr($_POST['text'],0,200)."...");
                }
                else{
                    phplog("Text received to be sent in the paper press\n".$_POST['text']);
                }
                $output=shell_exec("py tools.py sendto_clipboard_as_text ./temp/inclipboard.txt");
                
            }
            break;
        }
        
        if (isset($headers['save'])){
            if (!empty($_FILES)){
                $file = $_FILES['file']['name'];
                phplog("Fichier reçu : ".$file);
                move_uploaded_file($_FILES['file']['tmp_name'], "./share/".$file);
                phplog("File saved in the ./share folder");
                exec("start .\share");
            }
            
            
           break; 
        }

        else if (isset($headers['browser'])){
            phplog("the following link will be openned in the default browser:\n".$headers['browser']);

            //We write the link in a file to avoid executing malicious code sent by the client
            $file = fopen("./temp/browser.txt","w");
            fwrite($file,$headers['browser']);
            fclose($file);

            $output=shell_exec("py tools.py open_url ./temp/browser.txt");
            if (strlen($output) != 5 ){
                phplog("Error while opening the link in the browser");
                phperror($output);
            }
            break;
        }

        break;

    default:
        header('HTTP/1.1 405 Method Not Allowed');
        die('HTTP/1.1 405 Method Not Allowed');
        break;
}





//Function to be use in this script

function check_token(){;
    global $headers,$token;
    if (isset($headers['token']) && $token == $headers['token']){
        return true;
    }
    else{
        phperror("The client ".$_SERVER['REMOTE_ADDR']." tried to access the server with an invalid token (".$headers['token'].")\n his request has been denied, please check your token");
        header('HTTP/1.0 403 Forbidden');
        die("HTTP/1.0 403 Forbidden");
    }
}



function phplog($msg){
    //logs will be violet
    $color = "\033[0;35m";
    $colorreset = "\033[0m";

    if (is_array($msg) || is_object($msg)){
        error_log($color.print_r($msg,true).$colorreset);

    } else {
        error_log($color.$msg.$colorreset);
    }
}
function phperror($msg){
    //error will be red 
    $color = "\033[0;31m";
    $colorreset = "\033[0m";

    if (is_array($msg) || is_object($msg)){
        error_log($color.print_r($msg,true).$colorreset);

    } else {
        error_log($color.$msg.$colorreset);
    }
}


function pylog($msg){
    /*pylogs will be yellow
    and only visible if not to long
    */
    if (strlen($msg) > 10000){
        $msg="The output is too long to be displayed, it was probably binary data";
    }
    error_log("\033[0;93mPython LOGS \n".$msg."\033[0m");
}

?>
