"""
COPYRIGHT 2016 ESRI

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
import ast
import os
import traceback
import arcpy
import collections
from arcpy import env, mp
import logging
import logging.handlers
import argparse
import csv
import sys
import datetime
from time import sleep
import arcrest
from arcresthelper import securityhandlerhelper
import argparse

def initialize_logging(logFile):
    """
    setup the root logger to print to the console and log to file
    :param logFile: the log file to write to
    """
    formatter = logging.Formatter("[%(asctime)s] [%(filename)30s:%(lineno)4s - %(funcName)30s()]\
         [%(threadName)5s] [%(name)10.10s] [%(levelname)8s] %(message)s")  # The format for the logs
    logger = logging.getLogger()  # Grab the root logger
    logger.setLevel(logging.DEBUG)  # Set the root logger logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    # Create a handler to print to the console
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    sh.setLevel(logging.DEBUG)
    # Create a handler to log to the specified file
    rh = logging.handlers.RotatingFileHandler(logFile, mode='a', maxBytes=10485760)
    rh.setFormatter(formatter)
    rh.setLevel(logging.DEBUG)
    # Add the handlers to the root logger
    logger.addHandler(sh)
    logger.addHandler(rh)


def verify_file_path(filePath):
    """
    verify file exists
    :param filePath: the joined directory and file name
    :return: Boolean: True if file exists
    """
    logger = logging.getLogger()
    ospath = os.path.abspath(filePath)
    ospath = ospath.replace("\\","\\\\")
    logger.debug("Evaluating if {} exists...".format(ospath))
    if not os.path.isfile(str(ospath)):
        logging.getLogger().critical("File not found: {}".format(filePath))
        return False
    else:
        return True


def update_layer_style(aprx, mapx, opLyrName, lyrFile):
    """
    update layer style
    :param aprx: the project file object
    :param mapx: the Map object we're interested in changing lyr style for
    :param opLyrName: the name for the operational layer in the Map
    :param lyrFile: the path and name of the lyrx file being used
    """
    logger = logging.getLogger()
    # iterate over layers for
    for lyr in mapx.listLayers():
        if lyr.name == opLyrName:
            logger.info("Updating layer style...")
            arcpy.ApplySymbologyFromLayer_management(lyr, lyrFile)
    aprx.save()


def create_and_share_mmpk(mmpk_parameter_dictionary, args):
    """
    function for creating and sharing the mmpk
    :param mmpk_parameter_list: list of all the prepared mmpk parameters
    """
    logger = logging.getLogger()
    # create mmpk
    logger.info("Creating MMPK...")
    arcpy.management.CreateMobileMapPackage(in_map=mmpk_parameter_dictionary['in_map'], output_file=mmpk_parameter_dictionary['output_file'],
                                            in_locator=mmpk_parameter_dictionary['in_locator'], area_of_interest=mmpk_parameter_dictionary['area_of_interest'],
                                            extent=mmpk_parameter_dictionary['extent'], clip_features=mmpk_parameter_dictionary['clip_features'],
                                            title=mmpk_parameter_dictionary['title'], summary=mmpk_parameter_dictionary['summary'],
                                            description=mmpk_parameter_dictionary['description'], tags=mmpk_parameter_dictionary['tags'],
                                            credits=mmpk_parameter_dictionary['credits'], use_limitations=mmpk_parameter_dictionary['use_limitations'])
    user = str(args.username)
    password = str(args.password)
    logger.info("Sharing MMPK '{}'".format(mmpk_parameter_dictionary['output_file']))
    arcpy.SharePackage_management(in_package=mmpk_parameter_dictionary['output_file'], username=user, password=password,
                                  summary=mmpk_parameter_dictionary['summary'], tags=mmpk_parameter_dictionary['tags'], organization="MYORGANIZATION")
    # move agol item to appropiate directory
    agol_directory = mmpk_parameter_dictionary['agol_directory']
    move_item = mmpk_parameter_dictionary['title']
    move_agol_item(args, move_item, agol_directory)


def cleanup(args):
    """
    function to reset project back to normal state after program runs
    :param args: the args parsed from command line
    """
    aprx = arcpy.mp.ArcGISProject(args.aprxLocation)  # first step is to connect to project file
    # iterate over each mapx in project
    for mapx in aprx.listMaps():
        # iterate over layers for each mapx
        for lyr in mapx.listLayers():
            if lyr.name == str(args.opLyrName):
                standardLyrFile = str(args.styleDir) + "standard.lyrx"
                arcpy.ApplySymbologyFromLayer_management(lyr, standardLyrFile)  # apply standard.lyrx to op lyr
    aprx.save()  # save project after all maps have been through
    del aprx


def move_agol_item(args, item_title, agol_directory):
    """
    this function finds the item ids for the map and directory to place map and then moves the item
    :param args:
    :param itemTitle:
    :param agol_directory:
    :return:
    """
    securityinfo = {}
    securityinfo['security_type'] = args.security_type
    securityinfo['username'] = args.username
    securityinfo['password'] = args.password
    securityinfo['org_url'] = args.org_url
    securityinfo['proxy_url'] = args.proxy_url
    securityinfo['proxy_port'] = args.proxy_port
    securityinfo['referer_url'] = args.referer_url
    securityinfo['token_url'] = args.token_url
    securityinfo['certificatefile'] = args.certificate_file
    securityinfo['keyfile'] = args.keyfile
    securityinfo['client_id'] = args.client_id
    securityinfo['secret_id'] = args.secret_id
    try:
        # Authenticate
        shh = securityhandlerhelper.securityhandlerhelper(securityinfo)
        if not shh.valid:
            print(shh.message)
        else:
            # Get portal instance
            portal_admin = arcrest.manageorg.Administration(securityHandler=shh.securityhandler)
            # Get item_id by title
            destination_folder = agol_directory
            item_title = item_title
            # Initialize objects for validation purposes
            item_object, destination_folder_id = "", ""
            try:
                user = portal_admin.content.users.user(args.username)
                # Retrieve item object from AGOL
                for item in user.items:
                    if item.title == item_title:
                        move_item = item
                        # Get item
                        item_object = portal_admin.content.getItem(itemId=move_item.id).userItem
                        # Retrieve folder id
                        try:
                            for folder in user.folders:
                                if folder['title'] == destination_folder:
                                    dest_folder = folder
                                    destination_folder_id = dest_folder['id']
                        except Exception as e:
                            print(e)
                            print("Cannont find folder...")
                        # Move the item to the destination_folder_id
                        try:
                            print("Moving {} to folder {}...".format(move_item.title, dest_folder['title']))
                            item_object.moveItem(folder=destination_folder_id)
                            datetimenow = datetime.datetime.now()
                            print("Successfully Moved Map Item Id: {}\nModified at: {}".format(move_item.title, datetimenow))
                        except Exception as e:
                            print(e)
                            print("Cannot move item to folder...")
                    else:
                        raise Exception("Cannont find item...")
            except Exception as e:
                print("Error Moving item '{}' to '{}' folder".format(item_title, destination_folder))
                print(e)
    except Exception as e:
        print(e)



def convert_dictionary_datatypes(mmpk_parameter_dictionary):
    """
    supporting function for prepare_for_mmpk() that converts dictionary items to the proper datatype
    :param mmpk_parameter_dictionary: dictionary full of string items read from csv
    :return: mmpk_parameter_dictionary: with updated items to represent their true data type
    """
    for parameter in mmpk_parameter_dictionary:
        if parameter == 'in_map':
            pass
        else:
            mmpk_parameter_dictionary[parameter] = get_python_type(mmpk_parameter_dictionary[parameter])
    return mmpk_parameter_dictionary


def prepare_for_mmpk(args, row):
    """
    updates lyr style in project and builds an ordered dictionary of parameters based on csv file
    :param args: the args parsed from command line
    :param row: the row from the csv file to be processed
    :param aprx: the project file that the Maps exist in
    :param output_file: the place to save the mmpk
    :return: mmpk_parameter_list: list of all parameters
    """
    logger = logging.getLogger()
    aprx = arcpy.mp.ArcGISProject(args.aprxLocation)  # the project file
    projectVersion = str('Pro' + aprx.version)
    filenameVerion = projectVersion.replace(".", "")
    outname = str(row[args.outnameIndex])
    outputDir = str(args.outDir)  # get the output directory from the cmd line args
    output_file = str(outputDir + outname)  # combine output directory and mmpk file name
    output_file.replace("VER", filenameVerion)
    title = str(row[args.titleIndex])
    title.replace("VER", filenameVerion)
    opLyrName = str(args.opLyrName)  # get the operational layer from the cmd line args
    styleDir = str(args.styleDir)  # get the style directory from the cmd line args
    lyrx = str(row[args.lyrxNameIndex])
    logger.debug("Assign the row values to variables...")
    # get information from rows
    mmpk_parameters = (('in_map', str(row[args.basemapNameIndex])), ('output_file', output_file), # might be able to call get_python_type for each one here based on above
                       ('in_locator', str(row[args.locatorIndex])), ('area_of_interest', str(row[args.areaInterestIndex])),
                       ('extent', str(row[args.extentIndex])), ('clip_features', str(row[args.clipFeaturesIndex])),
                       ('title', title), ('summary', str(row[args.summaryIndex])), ('description', str(row[args.descriptionIndex])),
                       ('tags', str(row[args.tagsIndex])), ('credits', str(row[args.creditsIndex])),
                       ('limitations', str(row[args.limitationsIndex])), ('agol_directory', str(row[args.agolDirIndex])))
    logger.debug("Build the ordered dictionary...")
    mmpk_parameter_dictionary = collections.OrderedDict(mmpk_parameters)
    logger.debug("Grab mapx object from project and replace the str name...")
    mmpk_parameter_dictionary['in_map'] = aprx.listMaps(mmpk_parameter_dictionary['basemapName'])[0]
    logger.debug("Add Pro version number to tags...")
    mmpk_parameter_dictionary['tags'] = "\'" + projectVersion + "\'" if mmpk_parameter_dictionary['tags'] == '' else \
        mmpk_parameter_dictionary['tags'][:-2] + ", " + projectVersion + "]\'"
    # figure out locator path and name or None
    if mmpk_parameter_dictionary['locator'] != '':
        mmpk_parameter_dictionary['locator'] = str(args.locatorDir) + mmpk_parameter_dictionary['locator']
        if not verify_file_path(mmpk_parameter_dictionary['locator']): raise Exception('Locator file (.loc) does not exist')
    lyrx = styleDir + lyrx  # combine style directory and lyr file name
    if not verify_file_path(mmpk_parameter_dictionary['lyrx']): raise Exception('Layer file (.lyrx) does not exist')
    #  update the layer style
    logger.debug("Updated layer style...")
    update_layer_style(aprx, mmpk_parameter_dictionary['in_map'], opLyrName, lyrx)  # update the layer style
    logger.debug("Take the dictionary and build list...")
    mmpk_parameter_dictionary = convert_dictionary_datatypes(mmpk_parameter_dictionary)
    return mmpk_parameter_dictionary


def get_python_type(value):
    """
    try to get the correct data type. Especially for None and Boolean's
    :param value: Pass in the string value
    :return: valueType: in, hopefully, correct data type
    """
    logger = logging.getLogger()
    logger.debug("Try to convert to proper Python data type (None, Bool, etc.")
    try:
        valueType = ast.literal_eval(value)
    except Exception as e:
        logger.debug(str("Error: {}. Leave value as is...").format(e))
        valueType = value
    return valueType


def main(args):
    logger = logging.getLogger()
    logger.info("Starting program...")
    logger.debug("Connecting to project...")
    if not verify_file_path(args.aprxLocation): raise Exception('Project file does not exist')
    if not verify_file_path(args.csvFile): raise Exception('CSV file does not exist')
    aprx = arcpy.mp.ArcGISProject(args.aprxLocation)  # the project file
    csvFilePath = os.path.abspath(str(args.csvFile))
    logger.debug("Reading CSV file: {}...".format(csvFilePath))
    with open(csvFilePath) as csvFile:
        readCSV = csv.reader(csvFile)
        # read header file
        logger.debug("Reading CSV Headers...")
        next(readCSV, None)
        # iterate over csv file
        for row in readCSV:
            logger.info("Reading CSV Row " + str(readCSV.line_num))
            outname = str(row[args.outnameIndex])
            outputDir = str(args.outDir)  # get the output directory from the cmd line args
            output_file = outputDir + outname  # combine output directory and mmpk file name
            #  if mmpk already exists, skip mmpk creation
            if not verify_file_path(output_file):
                # update layer symbology and get list of parameters
                mmpk_parameter_dictionary = prepare_for_mmpk(args, row, aprx)
                # create mmpk and share package to AGOL
                create_and_share_mmpk(mmpk_parameter_dictionary, args)
            else:
                logger.info("MMPK already exists..Skipping CSV Row " + str(readCSV.line_num))
    del aprx
    csvFile.close()
    logger.info("Completed - resetting project back to original state")
    cleanup(args)  # after all rows of csv have been read cleanup the project


# Pro python cmd usage:
# cd "/Users/joel8641/Dropbox/Esri Material/CustomMMPKs/CustomMMPKLibrary/"
# python custom_mmpk_styles_from_csv.py -aprx "../CustomMMPKData/CustomMMPKDirectory.aprx" -opLyrName "SD_Fire_Hydrants" -csvFile "custom_mmpk_styles_list.csv"
if __name__ == "__main__":
    # get all of the commandline arguments
    parser = argparse.ArgumentParser("Build custom MMPKs from CSV and Share with AGOL")
    # required parameters
    parser.add_argument('-aprx', dest='aprxLocation', help="The full location of the custom mmpk Pro project file", required=True)
    parser.add_argument('-opLyrName', dest='opLyrName', help="The operational layer name in Pro project", required=True)
    parser.add_argument('-csvFile', dest='csvFile', help="The path/name of the csv file to read", required=True)
    # optional style directory
    parser.add_argument('-styleDir', dest='styleDir', help="The directory for styles", default="../CustomMMPKData/styles/")
    parser.add_argument('-locatorDir', dest='locatorDir', help="The directory for locators", default="../CustomMMPKData/locators/")
    parser.add_argument('-outDir', dest='outDir', help="The directory for generated MMPKs", default="../CustomMMPKData/generatedMMPKs/")
    # optional csv file mmpk parameters
    parser.add_argument('-lyrxNameIndex', dest='lyrxNameIndex', help="Index of layer file in csv file", default=1)
    parser.add_argument('-basemapNameIndex', dest='basemapNameIndex', help="Index of basemapName in csv file", default=2)
    parser.add_argument('-outnameIndex', dest='outnameIndex', help="Index of file output name in csv file", default=3)
    parser.add_argument('-locatorIndex', dest='locatorIndex', help="Index of locator in csv file", default=4)
    parser.add_argument('-areaInterestIndex', dest='areaInterestIndex', help="Index of area of interest parameter in csv file", default=5)
    parser.add_argument('-extentIndex', dest='extentIndex', help="Index of extent parameter in csv file", default=6)
    parser.add_argument('-clipFeaturesIndex', dest='clipFeaturesIndex', help="Index of clip features parameter in csv file", default=7)
    parser.add_argument('-titleIndex', dest='titleIndex', help="Index of title parameter in csv file", default=8)
    parser.add_argument('-summaryIndex', dest='summaryIndex', help="Index of summary parameter in csv file", default=9)
    parser.add_argument('-descriptionIndex', dest='descriptionIndex', help="Index of description parameter in csv file", default=10)
    parser.add_argument('-tagsIndex', dest='tagsIndex', help="Index of tags parameter in csv file", default=11)
    parser.add_argument('-creditsIndex', dest='creditsIndex', help="Index of credits parameter in csv file", default=12)
    parser.add_argument('-limitationsIndex', dest='limitationsIndex', help="Index of limitations parameter in csv file", default=13)
    parser.add_argument('-agolDirIndex', dest='agolDirIndex', help="Index of AGOL directory to store MMPK", default=14)

    # AGOL stuff
    parser.add_argument('-st', dest="security_type", help="The security of the portal/org (Portal, LDAP, NTLM, OAuth, PKI)", default="Portal")
    parser.add_argument('-u', dest='username', help="The username to authenticate with", default="ar_mmpk")
    parser.add_argument('-p', dest='password', help="The password to authenticate with", default="esri1234")
    parser.add_argument('-url', dest='org_url', help="The url of the org/portal to use", default="http://appsregression.maps.arcgis.com")
    parser.add_argument('-purl', dest='proxy_url', help="The proxy url to use", default=None)
    parser.add_argument('-pport', dest='proxy_port', help="The proxy port to use", default=None)
    parser.add_argument('-rurl', dest='referer_url', help="The referer url to use", default=None)
    parser.add_argument('-turl', dest='token_url', help="The token url to use", default=None)
    parser.add_argument('-cert', dest='certificate_file', help="The certificate to use", default=None)
    parser.add_argument('-kf', dest='keyfile', help="The key file to use", default=None)
    parser.add_argument('-cid', dest='client_id', help="The client id", default=None)
    parser.add_argument('-sid', dest='secret_id', help="The secret id", default=None)
    parser.add_argument('-ids', dest='item_ids', help="The ids of the items to configure", nargs="+", required=True)

    # required logFile
    parser.add_argument('-logFile', dest='logFile', help='The log file to use', default="log.txt")
    args = parser.parse_args()
    initialize_logging(args.logFile)
    try:
        main(args)
    except Exception as e:
        cleanup(args)
        logging.getLogger().critical("Exception detected, script exiting - resetting project back to original state")
        print(e)
        logging.getLogger().critical(e)
        logging.getLogger().critical(traceback.format_exc().replace("\n"," | "))