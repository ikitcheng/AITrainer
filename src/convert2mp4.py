import moviepy.editor as moviepy

def convertToMp4(origVidFile, finalVidFile):
    clip = moviepy.VideoFileClip(origVidFile)
    clip.write_videofile(finalVidFile)
    print("Video converted to MP4 successfully.")

if __name__ == '__main__':
    origVidFile = "./output/pullups.avi"
    finalVidFile = "./output/pullups.mp4"
    convertToMp4(origVidFile, finalVidFile)