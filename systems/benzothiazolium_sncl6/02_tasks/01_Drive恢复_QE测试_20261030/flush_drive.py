from google.colab import drive
print('Flushing Google Drive writes...',flush=True)
drive.flush_and_unmount()
print('DRIVE_FLUSH_AND_UNMOUNT_COMPLETED',flush=True)