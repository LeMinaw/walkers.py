#!/usr/local/bin/python3

import cv2
import os

def assemble(images_paths, output='video.mp4', factor=1, show=False):
    """Builds video from image files."""
    out = None
    for image_path in images_paths:
        print("Reading %s" % image_path)
        frame = cv2.imread(image_path)
        frame = cv2.resize(frame, None, fx=1/factor, fy=1/factor, interpolation=cv2.INTER_AREA)

        if out is None:
            # Defines video shape from first frame
            height, width, channels = frame.shape

            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Be sure to use lower case
            out = cv2.VideoWriter(output, fourcc, 20.0, (width, height))

        out.write(frame) # Write out frame to video

        if show:
            cv2.imshow('video', frame)
            if (cv2.waitKey(1) & 0xFF) == ord('q'): # Hit `q` to exit
                break

    out.release() # Release everything if job is finished
    cv2.destroyAllWindows()
    print("Done {}".format(output))
    return


def paths_from_extension(extension='png', dir='.'):
    """Returns all filenames matching the provided extension in dir."""
    filenames = [f for f in os.listdir(dir) if f.endswith(ext)]
    return tuple([os.path.join(dir, name) for name in filenames])


if __name__ == '__main__':
    import argparse

    # Construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-ext", "--extension", required=False, default='png',       help="extension name. default is 'png'.")
    ap.add_argument("-o",   "--output",    required=False, default='video.mp4', help="output video file")
    ap.add_argument("-f",   "--factor",    required=False, default=1,           help="size reduction factor")
    ap.add_argument("-s",   "--show",      required=False, default=0,           help="show video")
    args = vars(ap.parse_args())

    # Arguments
    dir_path = '.'
    ext    = args['extension']
    output = args['output']
    factor = args['factor']
    show   = args['show']

    images_paths = paths_from_extension(ext, dir_path)
    assemble(images_paths, output, factor, show)
