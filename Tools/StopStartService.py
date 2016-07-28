'''
This script will stop or start all selected services

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
Stop or Start
Service(s) (multivalue list)
'''

import _commonFunctions
import arcpy


def stopStartServices(handler, stopStart, serviceList):
    ''' Function to stop, start or delete a service.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    stopStart = Stop|Start|Delete
    serviceList = List of services. A service must be in the <name>.<type> notation
    '''

    # Getting services from tool validation creates a semicolon delimited list that needs to be broken up
    services = serviceList.split(';')

    #modify the services(s)
    for service in services:
        op_service_url = "{}/services/{}/{}".format(handler.baseURL, service, stopStart)
        status = handler.url_request(op_service_url, req_type='POST')

        if 'success' in status.values():
            arcpy.AddMessage(str(service) + " ==> " + str(stopStart))
        else:
            arcpy.AddWarning(status)

    return


if __name__ == "__main__":

    # Gather inputs
    server = arcpy.GetParameterAsText(0)
    port = arcpy.GetParameterAsText(1)
    adminUser = arcpy.GetParameterAsText(2)
    adminPass = arcpy.GetParameterAsText(3)
    stopStart = arcpy.GetParameter(4)
    serviceList = arcpy.GetParameterAsText(5)

    handler = _commonFunctions.connectionHelper(server, port, adminUser, adminPass)

    stopStartServices(handler, stopStart, serviceList)