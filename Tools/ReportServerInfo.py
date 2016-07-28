'''
This script will returned detailed information about a server

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
'''

import _commonFunctions
import arcpy
import datetime


def getServerInfo(handler):
    ''' Function to get and display a detailed report about a server
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    service = String of existing service with type seperated by a period <serviceName>.<serviceType>
    '''

    report = "*-----------------------------------------------*\n\n"

    # Get Cluster and Machine info
    cluster_url = "{}/clusters".format(handler.baseURL)
    jCluster = handler.url_request(cluster_url)

    if len(jCluster["clusters"]) == 0:
        report += "No clusters found\n\n"
    else:
        for cluster in jCluster["clusters"]:
            report += "Cluster: {} is {}\n".format(cluster["clusterName"], cluster["configuredState"])
            if len(cluster["machineNames"])     == 0:
                report += "    No machines associated with cluster\n"
            else:
                # Get individual Machine info
                for machine in cluster["machineNames"]:
                    machine_url = "{}/machines/{}".format(handler.baseURL, machine)
                    jMachine = handler.url_request(machine_url)
                    report += "    Machine: {} is {}. (Platform: {})\n".format(machine, jMachine["configuredState"],jMachine["platform"])


    # Get Version and Build
    info_url = "{}/info".format(handler.baseURL)
    jInfo = handler.url_request(info_url)
    report += "\nVersion: {}\nBuild:   {}\n\n".format(jInfo ["currentversion"], jInfo ["currentbuild"])


    # Get Log level
    log_url = "{}/logs/settings".format(handler.baseURL)
    jLog = handler.url_request(log_url)
    report += "Log level: {}\n\n".format(jLog["settings"]["logLevel"])


    #Get License information
    license_url = "{}/system/licenses".format(handler.baseURL)
    jLicense = handler.url_request(license_url)
    report += "License is: {} / {}\n".format(jLicense["edition"]["name"], jLicense["level"]["name"])
    if jLicense["edition"]["canExpire"] == True:
        d = datetime.date.fromtimestamp(jLicense["edition"]["expiration"] // 1000) #time in milliseconds since epoch
        report += "License set to expire: {}\n".format(datetime.datetime.strftime(d, '%Y-%m-%d'))
    else:
        report += "License does not expire\n"


    if len(jLicense["extensions"]) == 0:
        report += "No available extensions\n"
    else:
        report += "Available Extenstions........\n"
        for name in jLicense["extensions"]:
            report += "extension:  {}\n".format(name["name"])


    report += "\n*-----------------------------------------------*\n"

    arcpy.AddMessage(report)


if __name__ == "__main__":

    # Gather inputs
    server = arcpy.GetParameterAsText(0)
    port = arcpy.GetParameterAsText(1)
    adminUser = arcpy.GetParameterAsText(2)
    adminPass = arcpy.GetParameterAsText(3)

    handler = _commonFunctions.connectionHelper(server, port, adminUser, adminPass)

    getServerInfo(handler)