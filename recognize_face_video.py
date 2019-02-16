# importing all necessary packages
import argparse
import pickle
import time
import cv2
import face_recognition
import imutils
from imutils.video import VideoStream

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-e", "--encodings", required=True, help="path to serialized db of facial encodings")
ap.add_argument("-o", "--output", type=str, help="path to output video")
ap.add_argument("-y", "--display", type=int, default=1, help="whether or not to display output frame to screen")
ap.add_argument("-d", "--detection_method", type=str, default="hog", help="face detection model to use: either `hog` or `cnn`")
args = vars(ap.parse_args())

# load the faces and embedings
print("[INFO] loading encodings...")
data = pickle.loads(open(args["encodings"], "rb").read())

# initialize video stream and pointer to output file
print("[INFO] starting video stream")
stream = VideoStream(src=0).start()
writer = None
time.sleep(2.0)

# loop over frames from the stream
while True:
    frame = stream.read()  # read frames
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # correct the color ordering to RGB
    #  flip the frame to show correctly
    frame = cv2.flip(frame, 1)
    frame = imutils.resize(frame, width=700)
    r = frame.shape[1] / float(rgb_frame.shape[1])
    # detect the face locations and comput face embedings
    rectangle = face_recognition.face_locations(rgb_frame, model=args["detection_method"])
    encodings = face_recognition.face_encodings(rgb_frame, rectangle)
    names = []
    # loop over the facial embeddings
    for encoding in encodings:
        # attempt to match each face in the input image to our known
        # encodings
        matches = face_recognition.compare_faces(data["encodings"],
                                                 encoding)
        name = "Unknown"

        # check to see if we have found a match
        if True in matches:
            # find the indexes of all matched faces then initialize a
            # dictionary to count the total number of times each face
            # was matched
            matchIndexes = [i for (i, b) in enumerate(matches) if b]
            counts = {}

            # loop over the matched indexes and maintain a count for
            # each recognized face face
            for i in matchIndexes:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1

            # determine the recognized face with the largest number
            # of votes (note: in the event of an unlikely tie Python
            # will select first entry in the dictionary)
            name = max(counts, key=counts.get)

        # update the list of names
        names.append(name)

    # loop over the recognized faces
    for ((top, right, bottom, left), name) in zip(rectangle, names):
        # rescale the face coordinates
        top = int(top * r)
        right = int(right * r)
        bottom = int(bottom * r)
        left = int(left * r)

        # draw the predicted face name on the image
        cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 0), 2)
    # code for writing video output to disk
    if writer is None and args["output"] is not None:
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(args["output"], fourcc, 15, (frame.shape[1], frame.shape[0]), True)
    # if writer is not none, write the frame with recognized faces
    # to disk
    if writer is not None:
        writer.write(frame)
    # check the display argument
    # if it's greater than zero then display frame on screen
    if args["display"] > 0:
        cv2.imshow("Output", frame)
        key = cv2.waitKey(1) & 0xFF
        # if escape key is pressed break the loop
        if key == 27:
            break
# release the resources
cv2.destroyAllWindows()
stream.stop()
# check if writer is need to released
if writer is not None:
    writer.release()
