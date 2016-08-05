from __future__ import print_function

import sys
import urllib2
import re
import os
import argparse


def print_error_msg(msg):

    """
    prints an error message to stderr
    """

    print(msg, file=sys.stderr)


def download_image(url, path, mode):

    """
    downloads an image from a given URL and stores it in the given path

    mode = 'default': skip file if it exists on local disk
    mode = 'force':   overwrite existing files
    mode = 'rename':  rename downloaded file if file exists locally
    """

    ## append trailing slash to path
    if path[-1] != "/":
        path += "/"

    ## remove trailing CR or LF from URL
    url = re.sub(r'[\r\n]+$', '', url)

    ## check if URL is in format "<protocol>://..."
    if not re.match('^[a-z]+://.+', url.lower()):
        print_error_msg("Skipping URL %s: malformed URL" % url)
        return

    ## only HTTP and HTTPS protocols are allowed
    if not re.match('^https?://', url.lower()):
        print_error_msg("Skipping URL %s: invalid protocol (only HTTP and "
                        "HTTPS allowed)" % url)
        return

    ## extract filename from URL
    ## (file name must have an extension containing characters only)
    m = re.search('/([^/]+\.[a-zA-Z]+)$', url)
    if m:
        filename = m.group(1)
    else:
        print_error_msg("Skipping URL %s: invalid filename" % url)
        return

    ## download image URL
    try:
        result = urllib2.urlopen(url)

    ## HTTP error (e.g. 404 not found): print HTTP error code and message
    except urllib2.HTTPError, e:
        print_error_msg("Skipping URL %s: HTTP error %s (%s)"
                        % (url, e.code, e.msg))
        return

    ## non-HTTP error (e.g. connection refused): print error message
    except urllib2.URLError, e:
        print_error_msg("Skipping URL %s: %s" % (url, e.reason))
        return

    image_data = result.read()

    ## if file already exists locally, decide how to proceed
    if os.path.isfile(path + filename):

        ## default mode: skip downloading
        if mode == 'default':
            print_error_msg("Skipping URL %s: file already exists" % url)
            return

        ## rename mode: rename downloaded file by adding a number
        if mode == 'rename':
            counter = 2
            target_filename = filename
            m = re.match("^(.*)\.([^\.]+)$", filename)
            while os.path.isfile(path + target_filename):
                target_filename = "%s_%d.%s" % (m.group(1), counter, m.group(2))
                counter += 1
            filename = target_filename

        ## force mode: overwrite file
        if mode == 'force':
            pass

    print("Downloading %s to %s" % (url, filename))

    ## store file on disk
    try:
        with open(path + filename, 'wb') as f:
            f.write(image_data)
    except IOError, e:
        print_error_msg("Error: cannot write file '%s', reason: %s"
                        % (path + filename, str(e)))


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("filename",
                        help="file containing list of image URLs to download")
    parser.add_argument("-p", "--path",
                        help="path to store downloaded images in")
    overwrite_behavior = parser.add_mutually_exclusive_group(required=False)
    overwrite_behavior.add_argument("-f", "--force",
                                    help="overwrite existing files",
                                    action="store_true")
    overwrite_behavior.add_argument("-r", "--rename",
                                    help="rename existing downloaded file if file already exists",
                                    action="store_true")
    args = parser.parse_args()

    filename = args.filename

    ## use current path to download images if -p switch was not given
    if args.path:
        path = args.path
    else:
        path = os.getcwd()

    ## check if target path exists
    if not os.path.exists(path):
        print_error_msg("Error: path '%s' does not exist" % path)
        return

    ## check if URL file exists
    if not os.path.isfile(filename):
        print_error_msg("Error: file '%s' does not exist" % filename)
        return

    ## open URL file and read lines into list
    try:
        with open(filename) as f:
            image_urls = f.readlines()
    except IOError, e:
        print_error_msg("Error: cannot read from file '%s', reason: %s" % (filename, str(e)))
        return

    ## mode = default: skip file if it exists on local disk
    ## mode = force: overwrite existing files
    ## mode = rename: rename downloaded files if file exists locally
    mode = 'default'
    if args.force:
        mode = 'force'
    elif args.rename:
        mode = 'rename'

    for url in image_urls:
        download_image(url, path, mode)

if __name__ == "__main__":
    main()
