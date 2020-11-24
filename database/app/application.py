from states import States
import time

states = States()
def main():
    currentState = None
    stateChange = False
    while True:
        previousState = currentState
        if states.timeToUpload is True:
            currentState = "uploadingToCloud"
        elif states.braceletTimeout >= 20:
            currentState = "downloadingFromCloud"
        else:
            currentState = "readingFromBracelet"

        if currentState != previousState:
            stateChange = True
        else:
            stateChange = False

        if currentState == "readingFromBracelet":
            states.readingFromBracelet(stateChange)
        elif currentState == "uploadingToCloud":
            states.uploadingToCloud(stateChange)
        elif currentState == "downloadingFromCloud":
            states.downloadingFromCloud(stateChange)

        time.sleep(0.5)


if __name__ == "__main__":
    main()
    states.stop()
