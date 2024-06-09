# LudusSMA

# DEBUG

To debug locally, follow these steps:

1. Launch Docker.
2. Open WSL terminal.

    Do this step only if the `utils` folder has changed.
    1. Run `./scripts/lambda_layer_zipper.sh` in WSL.
    2. In case any error occurs run `sed -i 's/\r$//' ./scripts/lambda_layer_zipper.sh` and then retry with 1.
    
    This will produce a zip file, namely `utils.zip`.
3. Open a powershell terminal.
    1. Run `sam build -t ./template.yml` in the terminal (this can take some minutes to complete).
    2. Run `sam local start-api` in the terminal.
4. Open Ngrok.
    1. Run `ngrok.exe http 3000`. This should return 
        ```
        {
            "ok": true,
            "result": true,
            "description": "Webhook was set"
        }
        ```     
        If that is not the case, refer to @Dani.
5. Send request with Postman to update Telegram webhook using the ulr provided by ngrok.
6. Have fun with your Telegram bot now! :)



## **NOTE**
The first request to the function takes a couple of minutes to complete, because the image has to be built. In the meantime, Telegram resends the message again because it times out. For this reason, the app is likely to process the first message a couple of times, so please start the debug session with a message that does not imply the use of the agent. 

The following requests will take less time to complete..