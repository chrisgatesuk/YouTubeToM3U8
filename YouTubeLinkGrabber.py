#! /usr/bin/python3
import os
from datetime import datetime, timedelta

import pytz
import requests
from lxml import etree
from bs4 import BeautifulSoup

tz = pytz.timezone('Europe/London')
channels = []


def generate_times(curr_dt: datetime):
    """
Generate 3-hourly blocks of times based on a current date
    :param curr_dt: The current time the script is executed
    :return: A tuple that contains a list of start dates and a list of end dates
    """
    # Floor the last hour (e.g. 13:54:00 -> 13:00:00) and add timezone information
    last_hour = curr_dt.replace(microsecond=0, second=0, minute=0)
    last_hour = tz.localize(last_hour)
    start_dates = [last_hour]

    # Generate start times that are spaced out by three hours
    for x in range(7):
        last_hour += timedelta(hours=3)
        start_dates.append(last_hour)

    # Copy everything except the first start date to a new list, then add a final end date three hours after the last
    # start date
    end_dates = start_dates[1:]
    end_dates.append(start_dates[-1] + timedelta(hours=3))

    return start_dates, end_dates


def build_xml_tv(streams: list) -> bytes:
    """
Build an XMLTV file based on provided stream information
    :param streams: List of tuples containing channel/stream name, ID and category
    :return: XML as bytes
    """
    data = etree.Element("tv")
    data.set("generator-info-name", "youtube-live-epg")
    data.set("generator-info-url", "https://github.com/dp247/YouTubeToM3U8")

    for stream in streams:
        channel = etree.SubElement(data, "channel")
        channel.set("id", stream[1])
        name = etree.SubElement(channel, "display-name")
        name.set("lang", "en")
        name.text = stream[0]

        dt_format = '%Y%m%d%H%M%S %z'
        start_dates, end_dates = generate_times(datetime.now())

        for idx, val in enumerate(start_dates):
            programme = etree.SubElement(data, 'programme')
            programme.set("channel", stream[1])
            programme.set("start", val.strftime(dt_format))
            programme.set("stop", end_dates[idx].strftime(dt_format))

            title = etree.SubElement(programme, "title")
            title.set('lang', 'en')
            title.text = stream[3] if stream[3] != '' else f'LIVE: {stream[0]}'
            description = etree.SubElement(programme, "desc")
            description.set('lang', 'en')
            description.text = stream[4] if stream[4] != '' else 'No description provided'
            icon = etree.SubElement(programme, "icon")
            icon.set('src', stream[5])

    return etree.tostring(data, pretty_print=True, encoding='utf-8')


def grab(url: str):
    """
Grabs the live-streaming M3U8 file
    :param url: The YouTube URL of the livestream
    """
    if '&' in url:
        url = url.split('&')[0]

    requests.packages.urllib3.disable_warnings()
    stream_info = requests.get(url, timeout=15)
    response = stream_info.text
    soup = BeautifulSoup(stream_info.text, features="html.parser")


    if '.m3u8' not in response or stream_info.status_code != 200:
        print(url)
        return
    end = response.find('.m3u8') + 5
    tuner = 100
    while True:
        if 'https://' in response[end - tuner: end]:
            link = response[end - tuner: end]
            start = link.find('https://')
            end = link.find('.m3u8') + 5

            stream_title = soup.find("meta", property="og:title")["content"]
            stream_desc = soup.find("meta", property="og:description")["content"]
            stream_image_url = soup.find("meta", property="og:image")["content"]
            channels.append((channel_name, channel_id, category, stream_title, stream_desc, stream_image_url))

            break
        else:
            tuner += 5
    print(f"{link[start: end]}")


channel_name = ''
channel_id = ''
category = ''

# Open text file and parse stream information and URL
with open('./youtubeLink.txt', encoding='utf-8') as f:
    print("#EXTM3U")
    for line in f:
        line = line.strip()
        if not line or line.startswith('##'):
            continue
        if not line.startswith('https:'):
            line = line.split('||')
            channel_name = line[0].strip()
            channel_id = line[1].strip()
            category = line[2].strip().title()
            print(
                f'\n#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" group-title="{category}", {channel_name}')
        else:
            grab(line)

# Time to build an XMLTV file based on stream data
channel_xml = build_xml_tv(channels)
with open('epg.xml', 'wb') as f:
    f.write(channel_xml)
    print('#EXTINF:-1 channel-id="mjh-tvnz-1" tvg-id="mjh-tvnz-1" tvg-logo="https://i.mjh.nz/.images/tvnz-1.png" tvg-chno="1" group-title="NZ FTA" , TVNZ 1 1080p')
    print('http://10.1.3.199:8001/1:0:19:493:8:A9:6400000:0:0:0:')
    print('#EXTINF:-1 channel-id="mjh-tvnz-1" tvg-id="mjh-tvnz-1" tvg-logo="https://i.mjh.nz/.images/tvnz-1.png" tvg-chno="1" group-title="NZ FTA" , TVNZ 1 720p')
    print('https://i.mjh.nz/tvnz-1.m3u8')
    print('#EXTINF:-1 channel-id="mjh-tvnz-2" tvg-id="mjh-tvnz-2" tvg-logo="https://i.mjh.nz/.images/tvnz-2.png" tvg-chno="2" group-title="NZ FTA" , TVNZ 2 1080p')
    print('http://10.1.3.199:8001/1:0:19:494:8:A9:6400000:0:0:0:')
    print('#EXTINF:-1 channel-id="mjh-tvnz-2" tvg-id="mjh-tvnz-2" tvg-logo="https://i.mjh.nz/.images/tvnz-2.png" tvg-chno="2" group-title="NZ FTA" , TVNZ 2 720p')
    print('https://i.mjh.nz/tvnz-2.m3u8')
    print('#EXTINF:-1 channel-id="mjh-three" tvg-id="mjh-three" tvg-logo="https://i.mjh.nz/.images/three.png" tvg-chno="3" group-title="NZ FTA" , Three 1080p')
    print('http://10.1.3.199:8001/1:0:19:48D:8:A9:6400000:0:0:0:')
    print('#EXTINF:-1 channel-id="mjh-three" tvg-id="mjh-three" tvg-logo="https://i.mjh.nz/.images/three.png" tvg-chno="3" group-title="NZ FTA" , Three 720p')
    print('https://i.mjh.nz/three.m3u8')
    print('#EXTINF:-1 channel-id="mjh-tvnz-duke" tvg-id="mjh-tvnz-duke" tvg-logo="https://i.mjh.nz/.images/tvnz-duke.png" tvg-chno="6" group-title="NZ FTA" , DUKE 1080p')
    print('http://10.1.3.199:8001/1:0:19:3F3:8:A9:6400000:0:0:0:')
    print('#EXTINF:-1 channel-id="mjh-tvnz-duke" tvg-id="mjh-tvnz-duke" tvg-logo="https://i.mjh.nz/.images/tvnz-duke.png" tvg-chno="6" group-title="NZ FTA" , DUKE 720p')
    print('https://i.mjh.nz/tvnz-duke.m3u8')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport 1" tvg-id="NZ: SKY SPORT 1" tvg-logo="https://static.sky.co.nz/sky/channel-logos/051_sky_sport_1_logo_stack_rgb.png" group-title="NZ Sport", NZ Sky Sport 1')
    print('http://10.1.3.201:8001/1:0:19:489:7:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport 2" tvg-id="NZ: SKY SPORT 2" tvg-logo="https://static.sky.co.nz/sky/channel-logos/051_sky_sport_2_logo_stack_rgb.png" group-title="NZ Sport", NZ Sky Sport 2')
    print('http://10.1.3.201:8001/1:0:19:48A:7:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport 3" tvg-id="NZ: SKY SPORT 3" tvg-logo="https://static.sky.co.nz/sky/channel-logos/051_sky_sport_3_logo_stack_rgb.png" group-title="NZ Sport", NZ Sky Sport 3')
    print('http://10.1.3.205:8001/1:0:19:496:9:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport 4" tvg-id="NZ: SKY SPORT 4" tvg-logo="https://static.sky.co.nz/sky/channel-logos/051_sky_sport_4_logo_stack_rgb.png" group-title="NZ Sport", NZ Sky Sport 4')
    print('http://10.1.3.205:8001/1:0:19:4B1:9:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport 5" tvg-id="NZ: SKY SPORT 5" tvg-logo="https://static.sky.co.nz/sky/channel-logos/051_sky_sport_5_logo_stack_rgb.png" group-title="NZ Sport", NZ Sky Sport 5')
    print('http://10.1.3.206:8001/1:0:19:4B2:A:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport 6" tvg-id="NZ: SKY SPORT 6" tvg-logo="https://static.sky.co.nz/sky/channel-logos/051_sky_sport_6_logo_stack_rgb.png" group-title="NZ Sport", NZ Sky Sport 6')
    print('http://10.1.3.206:8001/1:0:19:4B3:A:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport 7" tvg-id="NZ: SKY SPORT 7" tvg-logo="https://static.sky.co.nz/sky/channel-logos/051_sky_sport_7_logo_stack_rgb.png" group-title="NZ Sport", NZ Sky Sport 7')
    print('http://10.1.3.202:8001/1:0:19:4B7:1:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport Premier League" tvg-id="NZ: SKY SPORT PREMIER LEAGUE" tvg-logo="https://static.sky.co.nz/sky/channel-logos/Sky_Sport_Premier_League_Channel_Logo.png" group-title="NZ Sport", NZ Sky Sport Premier League')
    print('http://10.1.3.206:8001/1:0:19:4B4:A:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport 9" tvg-id="NZ: SKY SPORT 9" tvg-logo="https://static.sky.co.nz/sky/channel-logos/051_sky_sport_9_logo_stack_rgb.png" group-title="NZ Sport", NZ Sky Sport 9')
    print('http://10.1.3.203:8001/1:0:19:4C1:2:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="NZ: Sky Sport Select" tvg-id="NZ: SKY SPORT SELECT" tvg-logo="https://static.sky.co.nz/sky/channel-logos/051_sky_sport_news.png" group-title="NZ Sport", NZ Sky Sport Select')
    print('http://10.1.3.199:8001/1:0:19:4DC:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="sky.sport.popup.1.nz" tvg-logo="https://icdb.tv/images/490e8bd314a2b6fb3b0d4fea0351b61a.jpg" group-title="NZ Sport", NZ Sky Sport Pop-Up 1 *')
    print('http://10.1.3.202:8001/1:0:19:3F1:4:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="sky.sport.popup.2.nz" tvg-logo="https://icdb.tv/images/490e8bd314a2b6fb3b0d4fea0351b61a.jpg" group-title="NZ Sport", NZ Sky Sport Pop-Up 2')
    print('http://10.1.3.202:8001/1:0:19:418:1:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="sky.sport.popup.3.nz" tvg-logo="https://icdb.tv/images/490e8bd314a2b6fb3b0d4fea0351b61a.jpg" group-title="NZ Sport", NZ Sky Sport Pop-Up 3')
    print('http://10.1.3.203:8001/1:0:19:3F0:2:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="espn.us" tvg-logo="https://seeklogo.com/images/E/espn-logo-BC988A9422-seeklogo.com.png" group-title="NZ Sport", NZ ESPN')
    print('http://10.1.3.199:8001/1:0:19:497:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="YT Sky News Audio Feed" tvg-id="skynews.uk" tvg-logo="https://archive.org/download/SkyNews_201708/sky%20news.png" group-title="News", Sky News Audio Feed')
    print('https://ukradiolive.com/ldblncr/sky-news-radio/sky-news-radio')
    print('#EXTINF:-1 tvg-id="bbcworldnews.us" tvg-logo="https://seeklogo.com/images/B/bbc-world-news-logo-10255C2E3B-seeklogo.com.png" group-title="News", BBC World News NZ Feed')
    print('http://10.1.3.202:8001/1:0:16:402:1:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="CNN NZ Feed" tvg-id="cnn.us" tvg-logo="https://seeklogo.com/images/C/CNN-logo-8DA6D1FC28-seeklogo.com.png" group-title="News", CNN NZ Feed')
    print('http://10.1.3.199:8001/1:0:16:3F7:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="Al Jazeera NZ Feed" tvg-id="aljazeera.uk" tvg-logo="https://archive.org/download/AlJazeera_201708/al%20jazeera.png" group-title="News" , Al Jazeera NZ Feed')
    print('http://10.1.3.204:8001/1:0:16:4BC:D:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="sky.news.nz" tvg-logo="https://seeklogo.com/images/S/sky-news-australia-logo-252ABF9816-seeklogo.com.png" group-title="News", Sky News Australia')
    print('http://10.1.3.202:8001/1:0:16:3F9:1:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="abc.news.buffalo" tvg-logo="https://nyheritage.org/sites/default/files/styles/collection_cover_extra/public/content/collection/covers/AnnualReport2.png_0.jpg" group-title="News", ABC News Buffalo')
    print('https://content.uplynk.com/channel/7a8b777a12f646f7b38d917ec0301595.m3u8')
    print('#EXTINF:-1 channel-id="mjh-trackside-1" tvg-id="mjh-trackside-1" tvg-logo="https://i.mjh.nz/.images/trackside-1.png" tvg-chno="62" group-title="NZ Sport" , TAB Trackside 1')
    print('https://i.mjh.nz/trackside-1.m3u8')
    print('#EXTINF:-1 channel-id="mjh-trackside-2" tvg-id="mjh-trackside-2" tvg-logo="https://i.mjh.nz/.images/trackside-2.png" tvg-chno="63" group-title="NZ Sport" , TAB Trackside 2')
    print('https://i.mjh.nz/trackside-2.m3u8')    
    print('#EXTINF:-1 tvg-id="mtv.nz" tvg-logo="https://seeklogo.com/images/M/mtv-music-television-logo-B016199701-seeklogo.com.png" group-title="Music", MTV NZ')
    print('http://10.1.3.199:8001/1:0:19:40F:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="mtv.music.nz" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/8/8e/MTV_80s_2022.png" group-title="Music", MTV 80s NZ')
    print('http://10.1.3.199:8001/1:0:16:498:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="Everyday Astronaut" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/e/ea/Everyday_Astronaut_logo.png" group-title="Live", Everyday Astronaut')
    print('https://manifest.googlevideo.com/api/manifest/hls_variant/expire/1717683677/ei/fXFhZrGsJ8a8juMPo_vo0Q4/ip/116.251.193.171/id/8VESowgMbjA.1/source/yt_live_broadcast/requiressl/yes/xpc/EgVo2aDSNQ%3D%3D/tx/51181296/txs/51181296%2C51181297%2C51181298/hfr/1/playlist_duration/30/manifest_duration/30/maxh/4320/maudio/1/siu/1/spc/UWF9fylp6UgaC-DIlrb57sNV1cQMDYBrtE9L9ya03l-I15AokUpbXkjDxTFQP7UOaaijkIPYPKOx/vprv/1/go/1/rqh/5/pacing/0/nvgoi/1/keepalive/yes/dover/11/itag/0/playlist_type/DVR/sparams/expire%2Cei%2Cip%2Cid%2Csource%2Crequiressl%2Cxpc%2Ctx%2Ctxs%2Chfr%2Cplaylist_duration%2Cmanifest_duration%2Cmaxh%2Cmaudio%2Csiu%2Cspc%2Cvprv%2Cgo%2Crqh%2Citag%2Cplaylist_type/sig/AJfQdSswRQIhAIllUwMARJuLh2KNOVFDMpzxzqlQE9Stmtb-HUcrn3QPAiAlnRR2jwQLRdyZpomc6kXflDYG3tQaGJgzGYNAfOo5kw%3D%3D/file/index.m3u8')
    print('#EXTINF:-1 tvg-name="Crown Hill Driveway" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Crown Hill Driveway')
    print('http://10.1.2.38:10000/h264/CHCDriveway/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Cottage Driveway" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Crown Hill Cottage Driveway')
    print('http://10.1.2.38:10000/h264/CHCFront/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Garden" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Crown Hill Garden')
    print('http://10.1.2.38:10000/h264/CHCGarden/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Kitchen Camera" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Crown Hill Kitchen Camera')
    print('http://10.1.2.38:10000/h264/CHCDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Alex Bedroom" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Crown Hill Alex Bedroom')
    print('http://10.1.2.38:10000/h264/CHCAlex/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Swimming Pool" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Crown Hill Swimming Pool')
    print('http://10.1.2.38:10000/h264/CHSwimPool/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Main Gate" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Main Gate')
    print('http://10.1.2.38:10000/h264/MindenMainGate/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden PTZ" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden PTZ')
    print('http://10.1.2.38:10000/h264/PTZ/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Back Gate" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Back Gate')
    print('http://10.1.2.38:10000/h264/BackGate/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Front Door" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Front Door')
    print('http://10.1.2.38:10000/h264/FrontDoor/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Top Driveway" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Top Driveway')
    print('http://10.1.2.38:10000/h264/MindenTopDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Upper Driveway" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Upper Driveway')
    print('http://10.1.2.38:10000/h264/UpperDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Lower Driveway" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Lower Driveway')
    print('http://10.1.2.38:10000/h264/LowerDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Side Lawn" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Side Lawn')
    print('http://10.1.2.38:10000/h264/SideLawn/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Swimming Pool" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Swimming Pool')
    print('http://10.1.2.38:10000/h264/SwimPool/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Garage" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Garage')
    print('http://10.1.2.38:10000/h264/MindenGarage/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Garage 2" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Garage 2')
    print('http://10.1.2.38:10000/h264/Garage2/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Keira Room" tvg-logo="https://drive.google.com/uc?export=download&id=1nolttZektZfoVrr53cYTGW-AEd5Q3xxG" group-title="CCTV", Minden Keira Room')
    print('http://10.1.2.38:10000/h264/Keira/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Alex Room" tvg-logo="https://drive.google.com/uc?export=download&id=1zkAucxHpzlkPCckxx_ZDs_Ofgsjl6qR5" group-title="CCTV", Minden Alex Room')
    print('http://10.1.2.38:10000/h264/Alex/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Pool Room" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Pool Room')
    print('http://10.1.2.38:10000/h264/PoolRoom/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Landing" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Landing')
    print('http://10.1.2.38:10000/h264/Landing/temp.ts')
    print('#EXTINF:-1 tvg-id="Weather" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Weather')
    print('http://10.1.2.38:10000/h264/Weather/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden')
    print('http://10.1.2.38:10000/h264/Minden/temp.ts')
    print('#EXTINF:-1 tvg-id="CrownHill" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Crown Hill')
    print('http://10.1.2.38:10000/h264/CrownHill/temp.ts')
    print('#EXTINF:-1 tvg-id="All Cameras" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", All Cameras')
    print('http://10.1.2.38:10000/h264/AllCameras/temp.ts')
    f.close()

# Remove temp files from project dir
if 'temp.txt' in os.listdir():
    os.system('rm temp.txt')
    os.system('rm watch*')

