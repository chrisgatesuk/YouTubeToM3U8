# YouTubeToM3U8
This repo automatically converts YouTube live streams into a single .m3u8 playlist and keeps them updated. The stream URLs are stored in a text file, which a Python script parses and builds the .m3u8 file from when a GitHub action is triggered (triggered by a cron job). A direct link can then be used to get the playlist, which can then be used in an IPTV app or xTeVe.

With thanks to [@victorlish](https://github.com/victorlish/YouTubeLinkGrabber) for the original project.

## Usage
1. Open the `youtubeLink.txt` file.
2. Add to the file with the following information for each stream:
```
Channel Name || Channel ID || Category
URL
``` 
- Channel Name - the title of the channel and/or live stream. It will appear in the EPG using this name.
- Channel ID - following popular convention, this should be short and end in '.yt', such as 'ExampleStream.yt'.
- Category - the type of stream. This is used to group the channels in the playlist, so something like 'Music' or 'News' is a good idea.
- URL - the URL of the stream

3. After saving changes, either wait for the cron job to run (this repo's job runs at 00:00, 03:00, 06:00, 09:00, 12:00, 15:00 and 18:00), or start the `LinkGrabber` workflow manually (repo > Actions tab > LinkGrabber > Run workflow).

You can also run the program locally by `python YouTubeLinkGrabber.py > YouTubeLive.m3u` or by `chmod +x exec_grabber.sh && ./exec_grabber.sh`.

4. The .m3u8 file will be generated again.

## Files
- If you want to use this repo as your source, remember to replace the username in the below URLs:
  
|           | Link                                                                       |
|-----------|----------------------------------------------------------------------------|
| M3U8 file | https://raw.githubusercontent.com/username/YouTubeToM3U8/main/youtube.m3u8 |
| EPG       | https://raw.githubusercontent.com/username/YouTubeToM3U8/main/epg.xml      |


## Future additions
- [ ] Add in channel icons
- ~~Support for EPG thumbnails from stream thumbnails~~
- ~~Support for TV guides/EPG matching~~
