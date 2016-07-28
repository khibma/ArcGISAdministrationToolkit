'''
This script will upload and register an SOE

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
SOE (file)
'''
import _commonFunctions
import arcpy


def upload(handler, fileinput):
    ''' Function to upload a file to the REST Admin
    fileinput = path to file to upload.
    '''
    upload_url ='{}/uploads/upload'.format(handler.baseURL)
    files = {"itemFile": {"filename": fileinput, "content":open(fileinput, 'rb').read()}}
    params = {'itemFile':fileinput,
              'f':'json',
              'token': handler.token}
    headers, data = _commonFunctions.MultipartFormdataEncoder().encodeForm(params, files)

    response = handler.url_request(upload_url, data, "MULTIPART", headers)

    if "item" in response.keys():
        itemID = response["item"]["itemID"]
        registerSOE(handler, itemID)
    else:
        arcpy.AddMessage(response)

    return


def registerSOE(handler, itemID):
    ''' Function to register the SOE that has been uploaded
    itemID = itemID of an uploaded SOE the server will register.
    '''

    # Registration of an SOE only requires an itemID.
    soeparams = {"id":itemID}
    register_url = "{}/services/types/extensions/register".format(handler.baseURL)
    status = handler.url_request(register_url, soeparams, req_type='POST')


    if 'success' in status.values():
        arcpy.AddMessage("Succesfully registed SOE")
    else:
        arcpy.AddError("Could not register SOE: ")
        arcpy.AddMessage("  {}".format(status))

    return


if __name__ == "__main__":

    # Gather inputs
    server = arcpy.GetParameterAsText(0)
    port = arcpy.GetParameterAsText(1)
    adminUser = arcpy.GetParameterAsText(2)
    adminPass = arcpy.GetParameterAsText(3)
    fileinput = arcpy.GetParameterAsText(4)

    handler = _commonFunctions.connectionHelper(server, port, adminUser, adminPass)

    upload(handler, fileinput)