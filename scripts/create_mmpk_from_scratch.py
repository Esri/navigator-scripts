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
import argparse
import ast
import traceback
from arcgis.gis import GIS
import arcpy
import logging
import logging.handlers
import sys
import os
import arcgis

def create_mmpk(map, args):
    """
    function for creating and sharing the mmpk
    :param mmpk_parameter_list: list of all the prepared mmpk parameters
    """
    logger = logging.getLogger()
    logger.info("Creating MMPK...")
    # TODO area_of_interest types
    # TODO extent types
    output_file = os.path.abspath("./%s.mmpk" % args.title)
    arcpy.CreateMobileMapPackage_management(in_map=map, output_file=output_file,
                                            in_locator=args.in_locator, area_of_interest=args.area_of_interest,
                                            extent=args.extent, clip_features=args.clip_features,
                                            title=args.title, summary=args.summary,
                                            description=args.description, tags=args.tags,
                                            credits=args.credits, use_limitations=args.use_limitations,
                                            anonymous_use=args.anonymous_use)
    return output_file

def share_mmpk(output_file, args):
    """
    Share mmpk to Portal
    :param args: the args parsed from command line
    """
    logger = logging.getLogger()
    _file_exists(output_file)
    logger.info("Sharing MMPK '%s'..." % args.title)
    gis = GIS(url=args.url, username=args.username, password=args.password)
    existing_items = gis.content.search('title:%s type:\'Mobile Map Package\'' % args.title)
    mmpk_properties = {'title': args.title,
                       'tags': args.tags,
                       'type': 'Mobile Map Package'}
    if not existing_items:
        gis.content.add(mmpk_properties, data=output_file)
    else:
        existing_item = existing_items[0]
        existing_item.update(mmpk_properties, data=output_file)

def _initialize_logging(logFile):
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

def _file_exists(filePath):
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
        logging.getLogger().debug("File not found: {}".format(filePath))
        return False
    else:
        return True

def _add_layers_to_map(layers, map):
    logger = logging.getLogger()
    logger.info("Adding layers to map")
    for layer_name in layers:
        _file_exists(layer_name)
        layer = arcpy.mp.LayerFile(layer_name)
        map.addLayer(layer)

def _reset_project(args, aprx=None):
    """
    Reset project back to normal state after program runs
    :param args: the args parsed from command line
    """
    logger = logging.getLogger()
    if aprx is None: aprx = arcpy.mp.ArcGISProject(args.aprx_file)
    for map in aprx.listMaps():
        logger.debug("Resetting map: ")
        for lyr in map.listLayers():
            print("  Remove layer: ")
            map.removeLayer(lyr)
    logger.debug("Save project")
    aprx.save()
    del aprx

def _validate_arguements(args):
    """
    Validates command line args
    :param args: the args parsed from command line
    """
    logger = logging.getLogger()
    logger.debug("Validating arguments")
    if not _file_exists(args.aprx_file): raise Exception('Project file does not exist')
    if args.share_map == "True" and (args.url is None or args.username is None or args.password is None):
        parser.error("Sharing map requires -url, -u, and -p.")

def main(args):
    logger = logging.getLogger()
    logger.info("Starting program...")
    # open project
    logger.debug("Connecting to project...")
    aprx = arcpy.mp.ArcGISProject(args.aprx_file)
    # add basemap layers
    basemap = aprx.listMaps(args.in_basemap)[0]
    _add_layers_to_map(args.basemap_layers, basemap)
    # add basemap to map
    map = aprx.listMaps(args.in_map)[0]
    map.addBasemap(basemap)
    # add operational layers
    _add_layers_to_map(args.operational_layers, map)
    # create mmpk
    output_file = create_mmpk(map, args)
    # share mmpk
    if args.share_map == "True": share_mmpk(output_file, args)
    # remove map / basemap layers
    logger.info("Completed - resetting project back to original state")
    _reset_project(args, aprx)

# cmd usage:
# cd "C:\Users\joel8641\Documents\GitHub\navigator-scripts\data\PortlandFirestations"
# python ../../scripts/create_mmpk_from_scratch.py -aprx "PortlandFirestations.aprx" -bl "./PortlandBasemap.lyrx" -ol "./PortlandFireEMS.lyrx" -t "PortlandFirestations" -sm "True" -u "username" -p "password"
# python ../../scripts/create_mmpk_from_scratch.py -aprx "PortlandFirestations.aprx" -bl "./PortlandBasemap.lyrx" "./Routing_ND.lyrx" -ol "./PortlandFireEMS.lyrx" -t "PortlandFirestations" -sm "True" -u "username" -p "password"
if __name__ == "__main__":
    # get all of the commandline arguments
    parser = argparse.ArgumentParser("Build MMPK from scratch and share with Online")
    # required
    parser.add_argument('-aprx', dest='aprx_file', help=":class:`String` -- Full location of the project file", required=True)
    parser.add_argument('-b', dest='in_basemap', help=":class:`String` -- Basemap name in project", default="Basemap")
    parser.add_argument('-bl', dest='basemap_layers', help=":class:`List` -- List of basemap layers", nargs="+", required=True)
    parser.add_argument('-m', dest='in_map', help=":class`String` -- Map name in project", default="Map")
    parser.add_argument('-ol', dest='operational_layers', help=":class`List` -- List of operational layers", nargs="+", required=True)
    parser.add_argument('-t', dest='title', help=":class`String` -- Output title and file name", required=True)
    # optionals
    parser.add_argument('-l', dest='in_locator', help=":class`String` -- List of locators", nargs="+", default=None)
    parser.add_argument('-aoi', dest='area_of_interest', help=":class`String` -- Layer name to define area of interest", default=None)
    parser.add_argument('-e', dest='extent', help=":class:`String` -- Keyword, bounding box, or layer name for extent", default="DISPLAY")
    parser.add_argument('-cf', dest='clip_features', help=":class:`String` -- CLIP or SELECT for unaltered", default="CLIP")
    parser.add_argument('-s', dest='summary', help=":class:`String` -- Add summary information to package", default="Sample summary")
    parser.add_argument('-d', dest='description', help=":class:`String` -- Add description information to package", default="Sample description")
    parser.add_argument('-ts', dest='tags', help=":class:`String` -- Add tag information to package", nargs="+", default="MMPK")
    parser.add_argument('-c', dest='credits', help=":class:`String` -- Add credit information to package", default=None)
    parser.add_argument('-ul', dest='use_limitations', help=":class:`String` -- Add use limitation information to package", default=None)
    parser.add_argument('-au', dest='anonymous_use', help=":class:`String` -- ANONYMOUS_USE or STANDARD", default="STANDARD")
    # sharing
    parser.add_argument('-sm', dest='share_map', help=":class:`String` -- Username to authenticate with", default="False")
    parser.add_argument('-url', dest='url', help=":class:`String` -- URL of the org/portal to use", default="https://arcgis.com")
    parser.add_argument('-u', dest='username', help=":class:`String` -- Username to authenticate with", default=None)
    parser.add_argument('-p', dest='password', help=":class:`String` -- Password to authenticate with", default=None)
    # logFile
    parser.add_argument('-log', dest='logFile', help='The log file to use', default="log.txt")
    args = parser.parse_args()
    _initialize_logging(args.logFile)
    _validate_arguements(args)
    try:
        main(args)
    except Exception as e:
        _reset_project(args)
        logging.getLogger().critical("Exception detected, script exiting - resetting project back to original state")
        print(e)
        print(arcpy.GetMessages())
        logging.getLogger().critical(e)
        logging.getLogger().critical(traceback.format_exc().replace("\n"," | "))