'''
This script will clear all log files and modify the log level settings

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
LogLevel
'''

import _commonFunctions
import arcpy


def modifyLogs(handler, clearLogs, logLevel):
    ''' Function to clear logs and modify log settings.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    clearLogs = True|False
    logLevel = SEVERE|WARNING|INFO|FINE|VERBOSE|DEBUG
    '''

    # Clear existing logs
    if clearLogs:
        clearLogs_url = "{}/logs/clean".format(handler.baseURL)
        status = handler.url_request(clearLogs_url, req_type='POST')
        if 'success' in status.values():
            arcpy.AddMessage ("Cleared log files")

    # Get the current logDir, maxErrorReportsCount and maxLogFileAge as we dont want to modify those
    currLogSettings_url = "{}/logs/settings".format(handler.baseURL)
    logSettingProps = handler.url_request(currLogSettings_url, req_type='GET')['settings']

    # Place the current settings, along with new log setting back into the payload

    logLevel_dict = {"logDir": logSettingProps['logDir'],
                     "logLevel": logLevel.upper(),
                     "maxErrorReportsCount": logSettingProps['maxErrorReportsCount'],
                     "maxLogFileAge": logSettingProps['maxLogFileAge']
                     }

    # Modify the logLevel
    logLevel_url = "{}/logs/settings/edit".format(handler.baseURL)
    logStatus = handler.url_request(logLevel_url, logLevel_dict, 'POST')

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

    handler = _commonFunctions.connectionHelper(server, port, adminUser, adminPass)

    modifyLogs(handler, clearLogs, logLevel)
