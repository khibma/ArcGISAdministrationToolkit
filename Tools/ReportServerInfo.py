'''
This script will returned detailed information about a server

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
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
    
    
def getServerInfo(server, port, adminUser, adminPass, token=None):
    ''' Function to get and display a detailed report about a server
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    service = String of existing service with type seperated by a period <serviceName>.<serviceType>
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get tand set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)      
     
    report = ''
    URL = "http://{}:{}/arcgis/admin/".format(server, port)

    report += "*-----------------------------------------------*\n\n"
    
    # Get Cluster and Machine info
    jCluster = getJson(URL, "clusters", token)
    
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
                    jMachine = getJson(URL, "machines/" + machine, token)
                    report += "    Machine: {} is {}. (Platform: {})\n".format(machine, jMachine["configuredState"],jMachine["platform"])                    
        
                    
    # Get Version and Build
    jInfo = getJson(URL, "info", token)    
    report += "\nVersion: {}\nBuild:   {}\n\n".format(jInfo ["currentversion"], jInfo ["currentbuild"])
      

    # Get Log level
    jLog = getJson(URL, "logs/settings", token)    
    report += "Log level: {}\n\n".format(jLog["settings"]["logLevel"])
     
    
    #Get License information
    jLicense = getJson(URL, "system/licenses", token)
    report += "License is: {} / {}\n".format(jLicense["edition"]["name"], jLicense["level"]["name"])    
    if jLicense["edition"]["canExpire"] == True:
        import datetime
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
    
    
def getJson(URL, endURL, token):    
    # Helper function to return JSON for a specific end point
    #
    
    openURL = URL + endURL + "?token={}&f=json".format(token)    
    status = urllib2.urlopen(openURL, '').read()    
    outJson = json.loads(status)   
    
    return outJson       
    
    
if __name__ == "__main__":     
    
    # Gather inputs    
    server = arcpy.GetParameterAsText(0)
    port = arcpy.GetParameterAsText(1)  
    adminUser = arcpy.GetParameterAsText(2) 
    adminPass = arcpy.GetParameterAsText(3) 
    
    getServerInfo(server, port, adminUser, adminPass)