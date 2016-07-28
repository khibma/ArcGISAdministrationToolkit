'''
This script will rename an existing service

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
Existing Service (in <serviceName>.<serviceType> format)
New Service name (only string of new service name)
'''

import _commonFunctions
import arcpy


def renameService(handler, service, newName):
    ''' Function to rename a service
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    service = String of existing service with type seperated by a period <serviceName>.<serviceType>
    newName = String of new service name
    '''

    #service = urllib.quote(service.encode('utf8'))

    # Check the service name for a folder:
    if "//" in service:
        serviceName = service.split('.')[0].split("//")[1]
        folderName = service.split('.')[0].split("//")[0] + "/"
    else:
        serviceName = service.split('.')[0]
        folderName = ""

    renameService_dict = { "serviceName": serviceName,
                           "serviceType": service.split('.')[1],
                           "serviceNewName" : newName
                         }

    rename_url = "{}/services/{}renameService".format(handler.baseURL, folderName)
    status = handler.url_request(rename_url, renameService_dict, 'POST')


    if 'success' in status.values():
        arcpy.SetParameter(6, True)
    else:
        arcpy.SetParameter(6, False)
        arcpy.AddError(status)


if __name__ == "__main__":

    # Gather inputs
    server = arcpy.GetParameterAsText(0)
    port = arcpy.GetParameterAsText(1)
    adminUser = arcpy.GetParameterAsText(2)
    adminPass = arcpy.GetParameterAsText(3)
    service = arcpy.GetParameter(4)
    newName = arcpy.GetParameterAsText(5)

    handler = _commonFunctions.connectionHelper(server, port, adminUser, adminPass)

    renameService(handler, service, newName)

