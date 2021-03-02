import argparse
import traceback
from arcgis.gis import GIS
import arcpy
import logging
import logging.handlers
import sys
import os

def create_mmpk(map, args):
    """
    function for creating mmpk
    :param map: list of all the prepared mmpk parameters
    :param args: the args parsed from command line
    """
    logger = logging.getLogger()
    logger.info("Creating MMPK...")
    # TODO area_of_interest types
    # TODO extent types
    output_file = os.path.abspath("./%s" % args.output_file)
    arcpy.CreateMobileMapPackage_management(in_map=map, output_file=output_file,
                                            in_locator=args.in_locator, area_of_interest=args.area_of_interest,
                                            extent=args.extent, clip_features=args.clip_features,
                                            title=args.title, summary=args.summary,
                                            description=args.description, tags=args.tags,
                                            credits=args.credits, use_limitations=args.use_limitations,
                                            anonymous_use=args.anonymous_use)

def share_mmpk(args):
    """
    share mmpk to portal
    :param args: the args parsed from command line
    """
    logger = logging.getLogger()
    logger.info("Sharing MMPK '%s'..." % args.title)
    gis = GIS(url=args.url, username=args.username, password=args.password)
    existing_items = gis.content.search('title:%s type:\'Mobile Map Package\' owner:%s' %(args.title, args.username))
    mmpk_properties = {'title': args.title,
                       'tags': args.tags,
                       'type': 'Mobile Map Package'}
    # update portal item if already exists
    output_file = os.path.abspath("./%s" % args.output_file)
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

def main(args):
    logger = logging.getLogger()
    logger.info("Starting program...")
    # load project
    aprx = arcpy.mp.ArcGISProject(args.aprx_file)
    # find map in project
    in_map = aprx.listMaps(args.in_map)[0]
    create_mmpk(in_map, args)
    # share mmpk
    if args.share_map == "True": share_mmpk(args)
    logger.info("Completed...")

# cmd usage:
# python ../../scripts/create_mmpk_basic.py -p "PortlandFirestations.aprx" -m "Map" -o "Map.mmpk" -t "Map Name"
# python ../../scripts/create_mmpk_basic.py -p "PortlandFirestations.aprx" -m "Map" -o "Map.mmpk" -t "Map_Name" -sm "True" -user "username" -pass "password"
if __name__ == "__main__":
    # get all of the commandline arguments
    parser = argparse.ArgumentParser("Build MMPK from scratch and share with Online")
    # required
    parser.add_argument('-p', dest='aprx_file', help=":class:`String` -- Full location of the project file", required=True)
    parser.add_argument('-m', dest='in_map', help=":class`String` -- Map name in project", default="Map")
    parser.add_argument('-o', dest='output_file', help=":class`String` -- Output file name", required=True)
    parser.add_argument('-t', dest='title', help=":class`String` -- Output title", required=True)
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
    parser.add_argument('-user', dest='username', help=":class:`String` -- Username to authenticate with", default=None)
    parser.add_argument('-pass', dest='password', help=":class:`String` -- Password to authenticate with", default=None)
    # logFile
    parser.add_argument('-log', dest='logFile', help='The log file to use', default="log.txt")
    args = parser.parse_args()
    _initialize_logging(args.logFile)
    try:
        main(args)
    except Exception as e:
        logging.getLogger().critical("Exception detected, script exiting")
        logging.getLogger().critical(e)
        logging.getLogger().critical(traceback.format_exc().replace("\n"," | "))