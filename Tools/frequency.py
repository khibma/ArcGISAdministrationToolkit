import arcpy, os


def doFrequency(inputTable, outputTable, freqFields):

    # create the output table and add appropraite fields
    outpath = os.path.dirname(outputTable)
    outname = os.path.basename(outputTable)

    arcpy.CreateTable_management(outpath, outname)
    arcpy.AddField_management(outputTable, "FREQUENCY", "LONG")

    for fields in arcpy.ListFields(inputTable):
        if fields.name in freqFields:
            name = fields.name
            fType = fields.type
            arcpy.AddField_management(outputTable, name, fType)


    # do frequency stuff

    fCur = ['OID@']
    for f in freqFields.split(';'):
        fCur.append(f)

    arcpy.AddMessage(fCur)

    dValues = {}

    numFields = len(fCur)
    with arcpy.da.SearchCursor(inputTable, fCur) as cursor:
        for index, row in enumerate(cursor):
            i=1
            while i <= numFields-1:
                if i == 1:
                    dValues[index] = str(row[i])
                else:
                    dValues[index] = (dValues[index] + ', ' + str(row[i]))
                i+=1


    from collections import Counter
    countedVal = Counter(dValues.itervalues())

    fCur.append("FREQUENCY")

    inCur = arcpy.da.InsertCursor(outputTable, fCur)

    for index, inRows in enumerate(countedVal):
        #arcpy.AddMessage(tuple(inRows.split(',')) + (countedVal[inRows],))
        inCur.insertRow((index,) + tuple(inRows.split(',')) + (countedVal[inRows],) )

    del inCur



if __name__ == "__main__":

    # Gather inputs
    inputTable = arcpy.GetParameterAsText(0)
    outputTable = arcpy.GetParameterAsText(1)
    freqFields = arcpy.GetParameterAsText(2)

    doFrequency(inputTable, outputTable, freqFields)
