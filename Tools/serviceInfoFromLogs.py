import arcpy, urllib, urllib2, json, sys, os


def gentoken(server, port, adminUser, adminPass, expiration=60):
    #Re-usable function to get a token required for Admin changes
    
    query_dict = {'username':   adminUser,
                  'password':   adminPass,
                  'expiration': str(expiration),
                  'client':     'requestip'}
    
    query_string = urllib.urlencode(query_dict)
    url = "http://{}:{}/arcgis/admin/generateToken".format(server, port)
    
    token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())
        
    if "token" not in token:
        arcpy.AddError(token['messages'])
        quit()
    else:
        return token['token']


def getLog(server, port, adminUser, adminPass, service, starttime, endtime):
    
    token = gentoken(server, port, adminUser, adminPass)
    

    logParams = {}
    logParams["token"] = token
    logParams["f"] = "json"
    if len(starttime) > 0:
        logParams["startTime"] = starttime
    if len(endtime) > 0:
        logParams["endTime"] = endtime
    logParams["level"] = "FINE"
    logParams["filterType"] = "json"
    logParams["pageSize"] = 100000
    #logParams["filter"] = {"services":[service]}
    logParams["filter"] = {"services":[service.encode('utf-8')]}

    query_string = urllib.urlencode(logParams)
    url = "http://{}:{}/arcgis/admin/logs/query".format(server, port)
    #print url
    #arcpy.AddMessage(url)    
    
    return json.loads(urllib.urlopen(url, query_string).read())

def logToTable(log, table):
    
    fieldTypes = {"type": "TEXT",
                  "message": "TEXT",
                  "time": "TEXT",
                  "source": "TEXT",
                  "machine": "TEXT",
                  "user": "TEXT",
                  "code": "LONG",
                  "elapsed": "DOUBLE",
                  "process": "TEXT",
                  "thread": "TEXT",
                  "methodName": "TEXT"}

    outpath = os.path.dirname(table)
    outname = os.path.basename(table)

    arcpy.CreateTable_management(outpath, outname)
    #print table
    #arcpy.AddMessage(table)
    
    logMessages = log["logMessages"]
    rowIndex = 0
    fields = []
                       
    for message in logMessages:
        if rowIndex == 0:
            for field in message.keys():
                fields.append(field)
                fieldType = fieldTypes[field]
                arcpy.AddField_management(table, field, fieldType)
            tablerows = arcpy.da.InsertCursor(table, fields)
                    
        row = []
        for field in fields:
            fieldType = fieldTypes[field]
            if fieldType == "LONG":
                row.append(int(message[field]))
            elif fieldType == "DOUBLE":
                if len(str(message[field])) == 0:
                    row.append(0)
                else:
                    row.append(float(message[field]))
            else:
                row.append(str(message[field]))
            
        tablerows.insertRow(row)
        rowIndex = rowIndex + 1



if __name__ == "__main__":     
    
    # Gather inputs    
    server = arcpy.GetParameterAsText(0)  
    port = arcpy.GetParameterAsText(1)  
    adminUser = arcpy.GetParameterAsText(2) 
    adminPass = arcpy.GetParameterAsText(3) 
    service = arcpy.GetParameterAsText(4) 
    table = arcpy.GetParameterAsText(5)    
    
    starttime = ""
    endtime = ""
    
    log = getLog(server, port, adminUser, adminPass, service, starttime, endtime)
    
    logToTable(log, table)    
    

     
    