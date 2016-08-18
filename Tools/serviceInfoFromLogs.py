'''
This script will export the logs from a service to a table

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
Service(s) (multivalue list)
Output table
'''

import _commonFunctions
import arcpy
import sys, os


def getLog(handler, service, starttime, endtime):

    service = service.strip("--[STOPPED]")
    service = service.strip("--[STARTED]")

    logParams = {}
    if len(starttime) > 0:
        logParams["startTime"] = starttime
    if len(endtime) > 0:
        logParams["endTime"] = endtime
    logParams["level"] = "FINE"
    logParams["filterType"] = "json"
    logParams["pageSize"] = 100000
    #logParams["filter"] = {"services":[service]}
    logParams["filter"] = {"services":[service.encode('utf-8')]}

    url = "{}/logs/query".format(handler.baseURL)

    return handler.url_request(url, logParams, req_type='POST')


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

    handler = _commonFunctions.connectionHelper(server, port, adminUser, adminPass)
    log = getLog(handler, service, starttime, endtime)

    logToTable(log, table)

