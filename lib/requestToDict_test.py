import requestToDict
import time

postReq='POST /set HTTP/1.1 \r\n {"heater":1,"taskT":{"max":30,"mid":20,"min":10}}'
getReq='GET /set?taskTmax=30&taskTmid=20 HTTP/1.1'

print("-"*30)
print("POST Request Test")
print("Input Request:"+postReq)
print("Output Dictionary:",requestToDict.parseRequest(postReq))
print("-"*30)
print("GET Request Test")
print("Input Request:"+getReq)
print("Output Dictionary:",requestToDict.parseRequest(getReq))
print("-"*30)

while True:
    time.sleep(1)
    pass

# Keep the script running to view output