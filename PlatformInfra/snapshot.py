#!/usr/bin/python

from azure.storage.blob import BlockBlobService
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("container", help="the blob container")
parser.add_argument("blob", help="the blob name")
parser.add_argument("-s", "--snapshot", help="take a new snapshot", action="store_true")
parser.add_argument("-d", "--delete", help="delete a snapshot")
parser.add_argument("-c", "--copy", help="copy a snapshot")
args = parser.parse_args()

# To use the storage services, you need to set the AZURE_STORAGE_ACCOUNT
# and the AZURE_STORAGE_ACCESS_KEY environment variables to the storage
# account name and primary access key you obtain from the Azure Portal.

AZURE_STORAGE_ACCOUNT='mpdevtestsa'
AZURE_STORAGE_ACCESS_KEY='mshBqDHBQwfKz8KETrRZfg7NKfBjyPniOK7TOXWI8nkRvJ+xXSNru0T4Apl8C24W1D2YtoAWF9iyv+gtFG/Y6g=='

blob_service = BlockBlobService(AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_ACCESS_KEY)

if args.snapshot == True:
  print('# Taking new snapshot...')
  blob_service.snapshot_blob(args.container, args.blob)
  print('OK.')

if args.delete:
  print('# Deleting snapshot...')
  blob_service.delete_blob(args.container, args.blob, snapshot=args.delete)
  print("Deleted".format(args.delete))

if args.copy:
  print('# Copying snapshot...')
  src = "https://" + AZURE_STORAGE_ACCOUNT + ".blob.core.windows.net/" + args.container + "/" + args.blob + "?snapshot=" + args.copy
  dst = args.blob + "_restore"
  blob_service.copy_blob(args.container, dst, src)
  print("Copied {} to {}".format(src, dst))

print('# List of snapshots:')

for blob in blob_service.list_blobs(args.container, include='snapshots'):
  if blob.name == args.blob:
    print(blob.name)
    print(blob.snapshot)
