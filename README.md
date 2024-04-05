![image](https://github.com/forxxin/Arknights_recruitment_tag/assets/165651451/d48e148c-3a14-491c-ae74-3eed0b0e807a)




## Install
Install Python 3.12.2 or ...

Install tesseract https://github.com/UB-Mannheim/tesseract/wiki

```pip install pywin32 pytesseract opencv-python```

edit code:   ```anhrtags.pyw```:```pytesseract.pytesseract.tesseract_cmd = r'your path/tesseract.exe'```

add adb.exe to PATH https://developer.android.com/tools/releases/platform-tools

## Usage
### draw roi example:
draw1 Enter draw2 Enter ... draw6 Enter Esc
![image](https://github.com/forxxin/Arknights_recruitment_tag/assets/165651451/83db558f-c286-4b61-88ea-8da3c033f089)


### to use wireless adb:
  ```adb pair 192.168.0.39:15468 314692```
  
## bug
   click OCR button will change ui scaling (fixed)
   
