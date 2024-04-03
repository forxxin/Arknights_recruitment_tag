![image](https://github.com/forxxin/Arknights_recruitment_tag/assets/165651451/230936b2-7130-4798-8415-f99a3978b446)

# install
Python 3.12.2

Install tesseract https://github.com/UB-Mannheim/tesseract/wiki

```pip install pywin32 pytesseract opencv-python```

edit code:   ```pytesseract.pytesseract.tesseract_cmd = r'your path/tesseract.exe'```

add adb to PATH https://developer.android.com/tools/releases/platform-tools

# bug
   click OCR button will change ui scaling
   
# hint
    draw roi example:
    draw1 Enter draw2 Enter ... draw6 Enter Esc
![image](https://github.com/forxxin/Arknights_recruitment_tag/assets/165651451/83db558f-c286-4b61-88ea-8da3c033f089)


  to use wireless adb:
  ```adb pair 192.168.0.39:15468 314692```
  
