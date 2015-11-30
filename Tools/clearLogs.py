'''
This script will clear all log files and modify the log level settings

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
LogLevel
'''

import urllib, urllib2, json
import arcpy


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


def modifyLogs(server, port, adminUser, adminPass, clearLogs, logLevel, token=None):
    ''' Function to clear logs and modify log settings.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    clearLogs = True|False
    logLevel = SEVERE|WARNING|INFO|FINE|VERBOSE|DEBUG
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get tand set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)
    
    # Clear existing logs
    if clearLogs:
        clearLogs = "http://{}:{}/arcgis/admin/logs/clean?token={}&f=json".format(server, port, token)
        status = urllib2.urlopen(clearLogs, ' ').read()  
        if 'success' in status:
            arcpy.AddMessage("Cleared log files")    
     
    # Get the current logDir, maxErrorReportsCount and maxLogFileAge as we dont want to modify those
    currLogSettings_url = "http://{}:{}/arcgis/admin/logs/settings?f=pjson&token={}".format(server, port, token)
    logSettingProps = json.loads(urllib2.urlopen(currLogSettings_url, ' ').read())['settings'] 
    
    # Place the current settings, along with new log setting back into the payload
    logLevel_dict = {      "logDir": logSettingProps['logDir'],
                           "logLevel": logLevel,
                           "maxErrorReportsCount": logSettingProps['maxErrorReportsCount'],
                           "maxLogFileAge": logSettingProps['maxLogFileAge']
                    }
   
    # Modify the logLevel
    log_encode = urllib.urlencode(logLevel_dict)     
    logLevel_url = "http://{}:{}/arcgis/admin/logs/settings/edit?f=json&token={}".format(server, port, token)
    logStatus = json.loads(urllib.urlopen(logLevel_url, log_encode).read())
    
    
    if logStatus['status'] == 'success':
        arcpy.AddMessage("Succesfully changed log level to {}".format(logLevel))
        arcpy.SetParameter(6, True)
    else:
        arcpy.AddWarning("Log level not changed")
        arcpy.AddMessage(logStatus)
        arcpy.SetParameter(6, False)

        
        
if __name__ == "__main__": 
    
    # Gather inputs    
    server = arcpy.GetParameterAsText(0)
    port = arcpy.GetParameterAsText(1)
    adminUser = arcpy.GetParameterAsText(2)
    adminPass = arcpy.GetParameterAsText(3)
    clearLogs = arcpy.GetParameter(4)
    logLevel = arcpy.GetParameterAsText(5)
    
    modifyLogs(server, port, adminUser, adminPass, clearLogs, logLevel)
        