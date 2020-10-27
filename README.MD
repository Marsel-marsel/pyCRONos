# pyCRONos
Sends messages to telegram contacts. Period is set 
using crontab syntax. This project is a kind of tribute to Mark Lutz's "Learning Python".

## Usage

1. [Get](https://docs.telethon.dev/en/latest/basic/signing-in.html) your telegram account _api_hash_ and _api_id_ and
save them into ```secrets/api_hash``` and ```secrets/api_id``` 

1. Add user id, message and cron to ```pyCRONos.yml```
    ```
   telegram:
     subscribers:
       '@user_name':  # @ symbol can be omitted
         message: "don't forget ur pills"
         cron: '29 0 * * *'  # At 00:29 UTC every day
    ```
1. Run _pyCRONos.py_ 
    ```
    nohup python pyCRONos.py &> /dev/null & 
    ```

1. Message will send repeatedly to user according to ```pyCRONos.yml```

    ![screenshot](doc/screenshot.jpg)
