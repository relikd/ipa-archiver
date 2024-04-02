# IPA Archiver

Scripts to download and unlock `.ipa` files for historical preservation. Every version of all the apps you ever purchased.

Personal usage only. This is not intended for piracy. Apple anounced they will shutdown older software and this is my attempt at preserving what I have bought and be able to run it even if Apple decides to delete everything.


## Requirements

You'll need:

- Windows 7 PC (I have not tested a VM but if it detects your iDevice via USB then it should be ok)
- macOS device (to run the main scripts, maybe it can be done with Windows alone, haven't tested)
- iDevice (jailbroken)


### Windows

- Install iTunes 12.6.5.3 [64bit](https://secure-appldnld.apple.com/itunes12/091-87819-20180912-69177170-B085-11E8-B6AB-C1D03409AD2A6/iTunes64Setup.exe)
(for completeness: [32bit](https://secure-appldnld.apple.com/itunes12/091-87820-20180912-69177170-B085-11E8-B6AB-C1D03409AD2A5/iTunesSetup.exe) though not needed)
- Install Python 3.8
- Clone [NyaMisty/actions-iTunes-header](https://github.com/NyaMisty/actions-iTunes-header) or use the one provided with this repo.
- Compile [libimobiledevice](https://github.com/libimobiledevice/libimobiledevice) or download [iFred09/libimobiledevice-windows](https://github.com/iFred09/libimobiledevice-windows) or use the one provided with this repo.
- In your firewall, open TCP ports `8117` (step 5, below) and `9000` (step 4, below).
- Enable network sharing on your home directory (this is how macOS will access the files)


Instructions:

1. Copy the `src_win` folder to windows.
2. If you have not done so already, patch iTunes with `src_win/actions-iTunes-header/workflow_helper/iTunesInstall/patch_itunes.py`
3. Start `iTunes`
4. Start `src_win/actions-iTunes-header/workflow_helper/iTunesDownload/get_header.py`
5. Start `src_win/win_server.py`
6. Connect your iDevice with Windows via USB


### iOS

- Apply a jailbreak corresponding to your iOS version
- Install SSH & change password
- Generate and copy an SSH key file (without password) to the device


### macOS

- Clone [NyaMisty/ipatool-py](https://github.com/NyaMisty/ipatool-py) or use the one provided with this repo.
- Connect to your network share (in Finder `Cmd+K` on `smb://your-pc`)
- Adjust your `config.ini` accordingly (see below)
- Edit your `~/.ssh/config` and add the iPad destination:

```
Host ipad
 HostName 192.168.0.0
 User root
 PreferredAuthentications publickey
 IdentityFile ~/.ssh/ipad.private-key
```

You should be able to connect to the iPad just by typing `ssh ipad` (without password prompt).


## Config.ini

- `itunes_server` & `win_server` should point to your Windows machine (with corresponding IP port)
- `ssh_cmd_crack`: the command used to launch the cracking (e.g. `Clutch`). Notice that we first remove all previous cracks.
- `ssh_cmd_sync`: Used to download the cracked apps. Notice that both commands just use "ipad" to connect to the device.
- `max_os`: most likely the iOS version running on your iDevice.
- `convert_binary_plist`: Turn this only on, if the Plist is somehow broken. We dont want to modify the app if we can avoid it.
- `sync_in`: same folder as `ssh_cmd_sync` will download into
- `sync_out`: network folder on your windows machine, same place where you copied your `src_win/queued` folder.
- `complete`: folder used to query new app ids. This is constantly updated before and after each app. E.g., `_versions.json` in each bundle-id dir.
- `download_fix`: download folder for IPA files. They remain there until they have been cracked.
- `download_tmp`: temporary folder for `ipatool-py`. Once an app is fully downloaded, the app moved to `download_fix` 


## Usage

1. You need to generate a history version list. Each app you download from iTunes has its history attached. You can, for example, download the latest version of an app via iTunes (Win) and run `./src_mac/extract_versions.py -m network-dir/to/*.ipa`. This will read all versions and extract them to the `done` directory. Note: the `-m` flag will move some of the IPA files if they are within the `max_os` range. Omit the flag if you want to keep the source files as is.
2. Your `complete` folder should now have a bunch of folders (one per app), each with a `_versions.json` file. Run `src_mac/download.py` to download all historic versions up until the last compatible iOS version as defined per config.
3. Run `src_mac/crack.py` to start the cracking process. You can run this in parallel to step 2.


## Known issues

Both, the cracking and the download script will fail once in a while.

`crack.py` fails:

1. Most likely due to an (un)install timeout. I assume `libimobiledevice` to be the culprit. Just run the script again. (PS: In theory it should be fine to call the script in a while-true loop, though I wouldn't want to do it unsupervised.)

2. If it fails with "no apps to crack", then the install probably failed. This can happen if you are not authorized to install the ipa. For example, if the `.sinf` is missing. Check you file or re-download it.


`download.py` can fail for many reasons:

1. The most common one: one of the files inside the zip has unicode characters. Python will raise a `File name in directory X and header Y differ` exception. Where both are nearly identical except for some unprintable chars. As long as the filename is not ending on `/Info.plist`, you can unzip it manually, for example with [Keka](https://github.com/aonez/Keka). Duplicate the `.ipa` file and double click to extract it. This should create a folder which ends on either " 2" or " copy" (depending on how you copy the file). Then run repack manually: `./src_mac/repack_ipa.py download/*\ 2` (or " copy")

2. If the file indeed ends on `/Info.plist`, then the unicode char is in the app name. Unzip as before, but before running repack, you have to move the `SC_Info/*.sinf` from the weird looking `Payload/*.app` to the non-broken app bundle. Right-click and "Show Package Contents". After you copied the file (there should be two now, `.sinf` and `.supp`), you can delte the weird looking app and continue with repack.

3. In very rare cases, the previous error also breaks the whole download process. You may have to wait until the IPA is cracked or temporarily exclude it in the `download.py` script. Most likely you will need to manually update the `_versions.json`.
