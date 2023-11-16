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
    print('#EXTINF:-1 tvg-id="Sky Q Lounge" group-title="Video Capture", Sky Q Lounge')
    print('rtmp://213.123.132.37:1936/')
    print('#EXTINF:-1 tvg-id="Sky Q Attic" group-title="Video Capture", Sky Q Attic')
    print('rtmp://213.123.132.37:1935/')
    print('#EXTINF:-1 tvg-id="Just Add Power Source Local" group-title="Video Capture", Just Add Power Source Local')
    print('rtmp://10.1.2.117:1935')
    print('#EXTINF:-1 tvg-id="Just Add Power Source Remote" group-title="Video Capture", Just Add Power Source Remote')
    print('rtmp://116.251.193.171:1935')
    print('#EXTINF:-1 tvg-id="House Shield Local" group-title="Video Capture", House Shield Local')
    print('rtmp://10.1.2.142:1935')
    print('#EXTINF:-1 tvg-id="House Shield Remote" group-title="Video Capture", House Shield Remote')
    print('rtmp://125.236.206.239:1935')
    print('#EXTINF:-1 tvg-id="Sky TV NZ Local" group-title="Video Capture", Sky TV NZ Local')
    print('rtmp://10.1.2.146:1935')
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
    print('#EXTINF:-1 tvg-id="SKY SPORT 1" group-title="NZ Sport", NZ Sky Sport 1')
    print('http://10.1.3.201:8001/1:0:19:489:7:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="SKY SPORT 2" group-title="NZ Sport", NZ Sky Sport 2')
    print('http://10.1.3.201:8001/1:0:19:48A:7:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="SKY SPORT 3" group-title="NZ Sport", NZ Sky Sport 3')
    print('http://10.1.3.205:8001/1:0:19:496:9:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="SKY SPORT 4" group-title="NZ Sport", NZ Sky Sport 4')
    print('http://10.1.3.205:8001/1:0:19:4B1:9:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="SKY SPORT 5" group-title="NZ Sport", NZ Sky Sport 5')
    print('http://10.1.3.206:8001/1:0:19:4B2:A:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="SKY SPORT 6" group-title="NZ Sport", NZ Sky Sport 6')
    print('http://10.1.3.206:8001/1:0:19:4B3:A:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="SKY SPORT 7" group-title="NZ Sport", NZ Sky Sport 7')
    print('http://10.1.3.202:8001/1:0:19:4B7:1:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="SKY SPORT PREMIER LEAGUE" group-title="NZ Sport", NZ Sky Sport Premier League')
    print('http://10.1.3.206:8001/1:0:19:4B4:A:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="SKY SPORT 9" group-title="NZ Sport", NZ Sky Sport 9')
    print('http://10.1.3.203:8001/1:0:19:4C1:2:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="SKY SPORT SELECT" group-title="NZ Sport", NZ Sky Sport Select')
    print('http://10.1.3.199:8001/1:0:19:4DC:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="sky.sport.popup.1.nz" group-title="NZ Sport", NZ Sky Sport Pop-Up 1 *')
    print('http://10.1.3.202:8001/1:0:19:3F1:4:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="sky.sport.popup.2.nz" group-title="NZ Sport", NZ Sky Sport Pop-Up 2')
    print('http://10.1.3.202:8001/1:0:19:418:1:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="sky.sport.popup.3.nz" group-title="NZ Sport", NZ Sky Sport Pop-Up 3')
    print('http://10.1.3.203:8001/1:0:19:3F0:2:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="espn.nz" group-title="NZ Sport", NZ ESPN')
    print('http://10.1.3.199:8001/1:0:19:497:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="Sky News" group-title="News", L Sky News HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VlmmbDZkqyK4Z3subfwAcqehTTXOUR99Ekk2ur92--RV")
    print('#EXTINF:-1 tvg-name="Sky News" group-title="News", L Sky News SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViUcZAZ_ieDXXG_oAM3Goq8")
    print('#EXTINF:-1 tvg-name="UK: SKY NEWS FHD" group-title="News", A Sky News HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_GVrZLxYUzKIGIe9XUdqdG/ts')
    print('#EXTINF:-1 tvg-name="UK: SKY NEWS FHD" group-title="News", A Sky News SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P9eRBIKjfMZCLGBgmjz-rJv/ts')
    print('#EXTINF:-1 tvg-name="UK: SKY NEWS" group-title="News", F Sky News HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/267')
    print('#EXTINF:-1 tvg-name="UK: SKY NEWS" group-title="News", F Sky News SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/270')
    print('#EXTINF:-1 tvg-name="UK: SKY NEWS" group-title="News", Sky News Audio Feed')
    print('https://linear021-gb-hls1-prd-ak.cdn.skycdp.com/Content/HLS_001_sd/Live/channel(skynews)/09_hd30.m3u8')
    print('#EXTINF:-1 tvg-id="BBCNEWS" group-title="News", L BBC News HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VoLqBQkUBKVjMpVsHC0Vd5PSr5pMQ7xE6ENGoWvQ52Po")
    print('#EXTINF:-1 tvg-id="BBCNEWS" group-title="News", L BBC News SD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VlrhzospQYsoYZr4U6PCTu8')
    print('#EXTINF:-1 tvg-name="UK: BBC NEWS HD" group-title="News", A BBC News HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P-nIH7f1zUPeNGeatH1tK3J/ts')
    print('#EXTINF:-1 tvg-name="UK: BBC NEWS HD" group-title="News", A BBC News SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P9mMvfe51wfTPmfw4O0x5NC/ts')
    print('#EXTINF:-1 tvg-name="UK: BBC NEWS FHD" group-title="News", F BBC News HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:2086/chrisgatesuk@hotmail.com/46dQ8dMl8e/603')
    print('#EXTINF:-1 tvg-name="UK: BBC NEWS SD" group-title="News", F BBC News SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:2086/chrisgatesuk@hotmail.com/46dQ8dMl8e/688')
    print('#EXTINF:-1 tvg-id="bbc.world.nz" group-title="News", BBC World News NZ Feed')
    print('http://10.1.3.202:8001/1:0:16:402:1:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="CNN International FHD" group-title="News", L CNN HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VtcZ4bOOo39NZxsHUyI9X1vKavHfKdJebGWQui8c_QoV")
    print('#EXTINF:-1 tvg-name="CNN International FHD" group-title="News", L CNN SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1Vl4E7kPY1rmnIICM6HtoJSY")
    print('#EXTINF:-1 tvg-name="UK: CNN NEWS HD" group-title="News", A CNN HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8Vj10AUju_nCFXONaJK_Q5/ts')
    print('#EXTINF:-1 tvg-name="UK: CNN NEWS HD" group-title="News", A CNN SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P89pD2KjujBfBZuo8Xmpino/ts')
    print('#EXTINF:-1 tvg-name="USA/CA: CNN HD" group-title="News", A CNN US HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8wxd3_upyi0U1Njlc-nx9t/ts')
    print('#EXTINF:-1,tvg-name="UK: CNN INTERNATIONAL FHD" group-title="News", F CNN HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:2086/chrisgatesuk@hotmail.com/46dQ8dMl8e/284')
    print('#EXTINF:-1,tvg-name="UK: CNN INTERNATIONAL SD" group-title="News", F CNN SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('#EXTINF:-1 tvg-id="cnn.international.nz" group-title="News", CNN NZ Feed')
    print('http://10.1.3.199:8001/1:0:16:3F7:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 channel-id="mjh-al-jazeera" tvg-id="mjh-al-jazeera" tvg-logo="https://i.mjh.nz/.images/al-jazeera.png" tvg-chno="20" group-title="News" , Al Jazeera NZ Feed')
    print('http://10.1.3.204:8001/1:0:16:4BC:D:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="sky.news.nz" group-title="News", Sky News Australia')
    print('http://10.1.3.202:8001/1:0:16:3F9:1:A9:6400000:0:0:0:')
    print('http://0a895194.indifferent-project.net:2086/chrisgatesuk@hotmail.com/46dQ8dMl8e/662')
    print('#EXTINF:-1 tvg-name="Sky Sports News HD" group-title="News", L Sky Sports News HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViZx7W0M4RpOMy7Ulmon0xr3XBQeX3NFoC_RgQ_jgzcr")
    print('#EXTINF:-1 tvg-name="Sky Sports News HD" group-title="News", L Sky Sports News SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViZx7W0M4RpOMy7Ulmon0xp1NhcJz0nI_s0Sr_Wbemrn")  
    print('#EXTINF:-1 tvg-name="UK: SKY SPORTS NEWS FHD" group-title="News", A Sky Sports News HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P-9SbkIk1Loup_qbAtc1ny6/ts')
    print('#EXTINF:-1 tvg-name="UK: SKY SPORTS NEWS FHD" group-title="News", A Sky Sports News SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_hMjQQOB9zp1IvuECQ2YOv/ts')
    print('#EXTINF:-1,tvg-name="UK: SKY SPORTS NEWS HD" group-title="News", F Sky Sports News HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:2086/chrisgatesuk@hotmail.com/46dQ8dMl8e/31')
    print('#EXTINF:-1,tvg-name="UK: SKY SPORTS NEWS SD" group-title="News", F Sky Sports News SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:2086/chrisgatesuk@hotmail.com/46dQ8dMl8e/29')
    print('#EXTINF:-1 channel-id="mjh-trackside-1" tvg-id="mjh-trackside-1" tvg-logo="https://i.mjh.nz/.images/trackside-1.png" tvg-chno="62" group-title="NZ Sport" , TAB Trackside 1')
    print('https://i.mjh.nz/trackside-1.m3u8')
    print('#EXTINF:-1 channel-id="mjh-trackside-2" tvg-id="mjh-trackside-2" tvg-logo="https://i.mjh.nz/.images/trackside-2.png" tvg-chno="63" group-title="NZ Sport" , TAB Trackside 2')
    print('https://i.mjh.nz/trackside-2.m3u8')    
    print('#EXTINF:-1 tvg-id="mtv.nz" group-title="Music", MTV NZ')
    print('http://10.1.3.199:8001/1:0:19:40F:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="mtv.music.nz" group-title="Music", MTV 80s NZ')
    print('http://10.1.3.199:8001/1:0:16:498:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="Crown Hill Driveway" group-title="CCTV", Crown Hill Driveway')
    print('http://10.1.2.38:10000/h264/CHCDriveway/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Cottage Driveway" group-title="CCTV", Crown Hill Cottage Driveway')
    print('http://10.1.2.38:10000/h264/CHCFront/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Garden" group-title="CCTV", Crown Hill Garden')
    print('http://10.1.2.38:10000/h264/CHCGarden/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Kitchen Camera" group-title="CCTV", Crown Hill Kitchen Camera')
    print('http://10.1.2.38:10000/h264/CHCDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Alex Bedroom" group-title="CCTV", Crown Hill Alex Bedroom')
    print('http://10.1.2.38:10000/h264/CHCAlex/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Swimming Pool" group-title="CCTV", Crown Hill Swimming Pool')
    print('http://10.1.2.38:10000/h264/CHSwimPool/temp.ts')
    print('#EXTINF:-1 tvg-id="Crown Hill Swimming Pool Alt" group-title="CCTV", Crown Hill Swimming Pool Alt')
    print('rtsp://admin:Fnys0644@10.10.2.127')
    print('#EXTINF:-1 tvg-id="Minden Main Gate" group-title="CCTV", Minden Main Gate')
    print('http://10.1.2.38:10000/h264/MindenMainGate/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Main Gate Alt" group-title="CCTV", Minden Main Gate Alt')
    print('rtsp://10.1.2.127:554/h264_stream')
    print('#EXTINF:-1 tvg-id="Minden PTZ" group-title="CCTV", Minden PTZ')
    print('http://10.1.2.38:10000/h264/PTZ/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden PTZ Alt" group-title="CCTV", Minden PTZ Alt')
    print('rtsp://admin:Fnys0644@10.1.2.195:554')
    print('#EXTINF:-1 tvg-id="Minden Back Gate" group-title="CCTV", Minden Back Gate')
    print('http://10.1.2.38:10000/h264/BackGate/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Back Gate Alt" group-title="CCTV", Minden Back Gate Alt')
    print('rtsp://admin:Fnys0644@10.1.2.159:554/main')
    print('#EXTINF:-1 tvg-id="Minden Front Door" group-title="CCTV", Minden Front Door')
    print('http://10.1.2.38:10000/h264/FrontDoor/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Front Door Alt" group-title="CCTV", Minden Front Door Alt')
    print('rtsp://10.1.2.130:554/h264_stream')
    print('#EXTINF:-1 tvg-id="Minden Top Driveway" group-title="CCTV", Minden Top Driveway')
    print('http://10.1.2.38:10000/h264/MindenTopDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Top Driveway Alt" group-title="CCTV", Minden Top Driveway Alt')
    print('rtsp://admin:Fnys0644@10.1.2.132:554/main')
    print('#EXTINF:-1 tvg-id="Minden Upper Driveway" group-title="CCTV", Minden Upper Driveway')
    print('http://10.1.2.38:10000/h264/UpperDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Upper Driveway Alt" group-title="CCTV", Minden Upper Driveway Alt')
    print('rtsp://admin:Fnys0644@10.1.2.153:554')
    print('#EXTINF:-1 tvg-id="Minden Lower Driveway" group-title="CCTV", Minden Lower Driveway')
    print('http://10.1.2.38:10000/h264/LowerDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Lower Driveway Alt" group-title="CCTV", Minden Lower Driveway Alt')
    print('rtsp://admin:Fnys0644@10.1.2.154:554')
    print('#EXTINF:-1 tvg-id="Minden Side Lawn" group-title="CCTV", Minden Side Lawn')
    print('http://10.1.2.38:10000/h264/SideLawn/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Side Lawn Alt" group-title="CCTV", Minden Side Lawn Alt')
    print('rtsp://admin:Fnys0644@10.1.2.83:554')
    print('#EXTINF:-1 tvg-id="Minden Swimming Pool" group-title="CCTV", Minden Swimming Pool')
    print('http://10.1.2.38:10000/h264/SwimPool/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Swimming Pool Alt" group-title="CCTV", Minden Swimming Pool Alt')
    print('rtsp://admin:Fnys0644@10.1.2.84:554')
    print('#EXTINF:-1 tvg-id="Minden Garage" group-title="CCTV", Minden Garage')
    print('http://10.1.2.38:10000/h264/MindenGarage/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Garage Alt" group-title="CCTV", Minden Garage Alt')
    print('rtsp://Xm472C7UZWMr:Od8LVeobA3to@10.1.2.196/live0')
    print('#EXTINF:-1 tvg-id="Minden Keira Room" group-title="CCTV", Minden Keira Room')
    print('http://10.1.2.38:10000/h264/Keira/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Alex Room" group-title="CCTV", Minden Alex Room')
    print('http://10.1.2.38:10000/h264/Alex/temp.ts')
    print('#EXTINF:-1 tvg-id="Weather" group-title="CCTV", Weather')
    print('http://10.1.2.38:10000/h264/Weather/temp.ts')
    print('#EXTINF:-1 tvg-id="All Cameras" group-title="CCTV", All Cameras')
    print('http://10.1.2.38:10000/h264/AllCameras/temp.ts')
    f.close()

# Remove temp files from project dir
if 'temp.txt' in os.listdir():
    os.system('rm temp.txt')
    os.system('rm watch*')

