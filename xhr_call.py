import urllib.request, datetime
import json

i=4
try:
 while(i>3):
  currDate=datetime.datetime.now()
  #currDateTime=currDate.strftime("%m/%d/%Y,%H:%M:%S.")
  currDateTime= currDate.strftime('%Y-%m-%d,%H:%M:%S.%f')[:-3]
  myUrl="https://www.broadcom.com/api/getjsonbyurl?vanityurl=&locale=avg_en&updateddate="+ str(currDateTime) +"&ctype=Page&cid=1421089852253"
  webUrl= urllib.request.urlopen(myUrl)
  if(webUrl.getcode()==200):
   data =webUrl.read().decode('utf-8')
   jsonData=json.loads(data)
   f = open("E:/pythonpgms/demofile.txt", "a")
   f.write(myUrl)
   f.write(currDateTime)
   f.write("Success"+str(webUrl.getcode())+"\n")
  #f.write(json.dumps(jsonData))
   f.close()
  else:
     print("Error receiving data", webUrl.getcode())
  i+=1
except:
    print("Exception ocurred ")
