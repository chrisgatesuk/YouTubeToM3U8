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
    print('#EXTINF:-1 tvg-id="Sky Q Lounge" tvg-logo="https://static.skyassets.com/contentstack/assets/bltdc2476c7b6b194dd/bltf7399d70ccccacbd/616942290d172d03af6210c1/SKY-Q-.jpg" group-title="Video Capture", Sky Q Lounge')
    print('rtmp://213.123.132.37:1936/')
    print('#EXTINF:-1 tvg-id="Sky Q Attic" tvg-logo="https://static.skyassets.com/contentstack/assets/bltdc2476c7b6b194dd/bltf7399d70ccccacbd/616942290d172d03af6210c1/SKY-Q-.jpg" group-title="Video Capture", Sky Q Attic')
    print('rtmp://213.123.132.37:1935/')
    print('#EXTINF:-1 tvg-id="Just Add Power Source Local" tvg-logo="https://avation.co.nz/wp-content/uploads/2017/06/Just_Add_Power.jpg" group-title="Video Capture", Just Add Power Source Local')
    print('rtmp://10.1.2.117:1935')
    print('#EXTINF:-1 tvg-id="Just Add Power Source Remote" tvg-logo="https://avation.co.nz/wp-content/uploads/2017/06/Just_Add_Power.jpg" group-title="Video Capture", Just Add Power Source Remote')
    print('rtmp://116.251.193.171:1935')
    print('#EXTINF:-1 tvg-id="House Shield Local" tvg-logo="https://www.nvidia.com/content/dam/en-zz/Solutions/about-nvidia/logo-and-brand/01-nvidia-logo-horiz-500x200-2c50-d.png" group-title="Video Capture", House Shield Local')
    print('rtmp://10.1.2.142:1935')
    print('#EXTINF:-1 tvg-id="House Shield Remote"  tvg-logo="https://www.nvidia.com/content/dam/en-zz/Solutions/about-nvidia/logo-and-brand/01-nvidia-logo-horiz-500x200-2c50-d.png" group-title="Video Capture", House Shield Remote')
    print('rtmp://125.236.206.239:1935')
    print('#EXTINF:-1 tvg-id="Sky TV NZ Local" tvg-logo="https://res.cloudinary.com/soar-communications-group-ltd/images/f_auto,q_auto/v1653672364/stoppress.co.nz/sky_image/sky_image.jpg" group-title="Video Capture", Sky TV NZ Local')
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
    print('#EXTINF:-1 tvg-name="L BBC One HD" tvg-id="BBC1HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrXvSHr9IagKkIzvw6fDn0pjCECoFrFXWEY7JfJVcg8h5UrORdvxghyQco_fsVwaW5A.png" group-title="UK Entertainment", L BBC One HD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViXn-YqrcicW1wyQBcCXAfM')
    print('#EXTINF:-1 tvg-name="L BBC One SD" tvg-id="bbc1.uk" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrTyNIvjGSoxS4X4W2wFRGMInhR0ClBfD4cbgFg5oIvcUnOc6CU8vvr55vsK__LbFoQ.png" group-title="UK Entertainment", L BBC One SD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViXn-YqrcicW1wyQBcCXAfM')
    print('#EXTINF:-1 tvg-name="F BBC One HD" tvg-id="bbc1.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_Bbc1/bbc%201.png" group-title="UK Entertainment", F BBC One HD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/8015')
    print('#EXTINF:-1 tvg-name="F BBC One SD" tvg-id="bbc1.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_Bbc1/bbc%201.png" group-title="UK Entertainment", F BBC One SD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/394')
    print('#EXTINF:-1 tvg-name="A BBC One HD" tvg-id="bbc1.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/6614baa8b02c78a779e3ea40eb893bab.png" group-title="UK Entertainment", A BBC One HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8HaOGiSJ43UIXo0nZetz6Z/ts')
    print('#EXTINF:-1 tvg-name="A BBC One SD" tvg-id="BBC1" tvg-logo="https://wedontlikepubliceyes22.me:443/images/b64518bcfd225959ee7f0fb42069cf81.png" group-title="UK Entertainment", A BBC One SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P-BiaMI_Vxc_DG-9DT5Z2Cr/ts')
    print('#EXTINF:-1 tvg-name="L BBC Two HD" tvg-id="BBC2HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrWgJBUgjo8iBFHw83-qp0lV9PY97YNSsLQ82-_oZ0OvfVcuCc3yULyqqsS6RQBIINA.png" group-title="UK Entertainment", L BBC Two HD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VlMKmJhqR3e5QXoRs3cX4vQ')
    print('#EXTINF:-1 tvg-name="L BBC Two SD" tvg-id="bbc2.uk" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrTyNIvjGSoxS4X4W2wFRGMIXGc7D7gHMBE1UE99RFFE0HrP8U9aBAQGoveUcIPUhfQ.png" group-title="UK Entertainment", L BBC Two SD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1Vsu3jaCq8Wa3Mw_rDQakNvvhDdkDwy_DQME3UjoY5PHH')
    print('#EXTINF:-1 tvg-name="F BBC Two HD" tvg-id="bbc2.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_Bbc2/bbc%202.jpg" group-title="UK Entertainment", F BBC Two HD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/8016')
    print('#EXTINF:-1 tvg-name="F BBC Two SD" tvg-id="bbc2.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_Bbc2/bbc%202.jpg" group-title="UK Entertainment", F BBC Two SD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/3')
    print('#EXTINF:-1 tvg-name="A BBC Two HD" tvg-id="bbc2.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/2aafdea532f55fb40c07c7da443c892f.png" group-title="UK Entertainment", A BBC Two HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_NgPjGcqqOtsstEZqpngiV/ts')
    print('#EXTINF:-1 tvg-name="A BBC Two SD" tvg-id="bbc2.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/045e89185ec288f6c6c13d413b2df49f.png" group-title="UK Entertainment", A BBC Two SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P-ZDL_sEBkR8YJwY_EpYF_Y/ts')
    print('#EXTINF:-1 tvg-name="L ITV HD" tvg-id="ITVMNF" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrWgJBUgjo8iBFHw83-qp0lUZ2DtjevWl1WJpWQspHO9N3i3W14zQeq6doeCHEE72TQ.png" group-title="UK Entertainment", L ITV HD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VpRzO3gSJOEjIXMBz95d_-I')
    print('#EXTINF:-1 tvg-name="L ITV SD" tvg-id="itv1.uk" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrWgJBUgjo8iBFHw83-qp0lUZ2DtjevWl1WJpWQspHO9N3i3W14zQeq6doeCHEE72TQ.png" group-title="UK Entertainment", L ITV SD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VkmeHzATiccTjwVCI8Y25wjB2hIzFnXmq_JVQDDrePyr')
    print('#EXTINF:-1 tvg-name="F ITV HD" tvg-id="itv.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_Itv1/itv%201.png" group-title="UK Entertainment", F ITV HD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/7900')
    print('#EXTINF:-1 tvg-name="F ITV SD" tvg-id="itv.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_Itv1/itv%201.png" group-title="UK Entertainment", F ITV SD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/637')  
    print('#EXTINF:-1 tvg-name="A ITV HD" tvg-id="itv1.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/f2e6971d7d94bd7076e1708d07a2ee48.png" group-title="UK Entertainment", A ITV HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P-bIQHxgfYrwCyANhbPnRQ5/ts')
    print('#EXTINF:-1 tvg-name="A ITV SD" tvg-id="itv1.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/4c565c7d5405218c014cdeac0def81a9.png" group-title="UK Entertainment", A ITV SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_7WpNNU8dnIT-X4-zxD6uZ/ts')
    print('#EXTINF:-1 tvg-name="L Channel 4 HD" tvg-id="C4HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrWgJBUgjo8iBFHw83-qp0lU_8wQicGoXcqeGvzlg3hjbIG-Me1sBHiFlIISdCF699g.png" group-title="UK Entertainment", L Channel 4 HD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VkOwCU241i-5Ad-CVYjMheo')
    print('#EXTINF:-1 tvg-name="L Channel 4 SD" tvg-id="C4HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrWgJBUgjo8iBFHw83-qp0lU_8wQicGoXcqeGvzlg3hjbIG-Me1sBHiFlIISdCF699g.png" group-title="UK Entertainment", L Channel 4 SD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VkmeHzATiccTjwVCI8Y25wgse_FBvAR6xBLm3LW2DYZB')
    print('#EXTINF:-1 tvg-name="F Channel 4 HD" tvg-id="channel4.uk" tvg-logo="https://archive.org/download/Channel4_201708/channel%204.png" group-title="UK Entertainment", F Channel 4 HD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/7890')
    print('#EXTINF:-1 tvg-name="F Channel 4 SD" tvg-id="channel4.uk" tvg-logo="https://archive.org/download/Channel4_201708/channel%204.png" group-title="UK Entertainment", F Channel 4 SD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/651')  
    print('#EXTINF:-1 tvg-name="A Channel 4 HD" tvg-id="C4HD" tvg-logo="https://wedontlikepubliceyes22.me:443/images/d28ed7fc8ca474a7f424d5d2ee791b0e.png" group-title="UK Entertainment", A Channel 4 HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8YKIpSb1vvZCy5RSogWGhW/ts')
    print('#EXTINF:-1 tvg-name="A Channel 4 SD" tvg-id="C4HD" tvg-logo="https://wedontlikepubliceyes22.me:443/images/d4a7ebe8eb8d6e93e55556c21f6d271f.png" group-title="UK Entertainment", A Channel 4 SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_B-bA5V82N5MbGUG5ECBkW/ts')
    print('#EXTINF:-1 tvg-name="L Channel 5 HD" tvg-id="CH5HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrWgJBUgjo8iBFHw83-qp0lUlKR6NEw3GJxXzZ50N3Zd9D7wUqVGhHnFTjorwAq9eJg.png" group-title="UK Entertainment", L Channel 5 HD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1Vubmv3kYkpGM_2X_rN1fm5takhM7y8kqHuC646tsOSOv')
    print('#EXTINF:-1 tvg-name="L Channel 5 SD" tvg-id="CH5HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrWgJBUgjo8iBFHw83-qp0lUlKR6NEw3GJxXzZ50N3Zd9D7wUqVGhHnFTjorwAq9eJg.png" group-title="UK Entertainment", L Channel 5 SD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VkmeHzATiccTjwVCI8Y25wi08ojhPZ5VHy9oOuYP8ryV')
    print('#EXTINF:-1 tvg-name="F Channel 5 HD" tvg-id="channel5.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_5/5.png" group-title="UK Entertainment", F Channel 5 HD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/8017')
    print('#EXTINF:-1 tvg-name="F Channel 5 SD" tvg-id="channel5.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_5/5.png" group-title="UK Entertainment", F Channel 5 SD')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/6')  
    print('#EXTINF:-1 tvg-name="A Channel 5 HD" tvg-id="channel5.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/112b75c1636c5e6ec4b6a534e4dfdcc5.png" group-title="UK Entertainment", A Channel 5 HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P9vG-AFjMffn_pKUq7EuSkG/ts')
    print('#EXTINF:-1 tvg-name="A Channel 5 SD" tvg-id="channel5.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/2c031c8b597335e4886c0c98c895f275.png" group-title="UK Entertainment", A Channel 5 SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8WGwoNYkLoep49J9o7_38K/ts')    
    print('#EXTINF:-1 tvg-name="L Sky News HD" tvg-id="skynews.uk" tvg-logo="https://archive.org/download/SkyNewsHd/sky%20news%20hd.png" group-title="News", L Sky News HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VlmmbDZkqyK4Z3subfwAcqehTTXOUR99Ekk2ur92--RV")
    print('#EXTINF:-1 tvg-name="L Sky News SD" tvg-id="skynews.uk" tvg-logo="https://archive.org/download/SkyNews_201708/sky%20news.png" group-title="News", L Sky News SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViUcZAZ_ieDXXG_oAM3Goq8")
    print('#EXTINF:-1 tvg-name="A Sky News HD" tvg-id="skynews.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/b091192b55c667f6f6a3003034ae4c3e.png" group-title="News", A Sky News HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_GVrZLxYUzKIGIe9XUdqdG/ts')
    print('#EXTINF:-1 tvg-name="A Sky News SD" tvg-id="skynews.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/3e1415be0afb239a78e2861d73ea0eb4.png" group-title="News", A Sky News SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P9eRBIKjfMZCLGBgmjz-rJv/ts')
    print('#EXTINF:-1 tvg-name="F Sky News HD" tvg-id="skynews.uk" tvg-logo="https://archive.org/download/SkyNewsHd/sky%20news%20hd.png" group-title="News", F Sky News HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/267')
    print('#EXTINF:-1 tvg-name="F Sky News SD" tvg-id="skynews.uk" tvg-logo="https://archive.org/download/SkyNews_201708/sky%20news.png" group-title="News", F Sky News SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/270')
    print('#EXTINF:-1 tvg-name="YT Sky News Audio Feed" tvg-id="skynews.uk" tvg-logo="https://archive.org/download/SkyNews_201708/sky%20news.png" group-title="News", Sky News Audio Feed')
    print('https://linear021-gb-hls1-prd-ak.cdn.skycdp.com/Content/HLS_001_sd/Live/channel(skynews)/09_hd30.m3u8')
    print('#EXTINF:-1 tvg-name="L BBC News HD" tvg-id="BBCNWHD" tvg-logo="http://80.82.76.70:80/images/SvlCE3pU-C0TyF1rEXMsrbnNqbgSmPjNUZqJQsU6xJFeoKkXT9h1Nrv1T74HQEbK_VXReq1lSG0Cfcp97LbTBg.png" group-title="News", L BBC News HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VoLqBQkUBKVjMpVsHC0Vd5PSr5pMQ7xE6ENGoWvQ52Po")
    print('#EXTINF:-1 tvg-name="L BBC News SD" tvg-id="BBCNEWS" tvg-logo="http://80.82.76.70:80/images/SvlCE3pU-C0TyF1rEXMsrTyNIvjGSoxS4X4W2wFRGMLrbpn9qFUC7YFSDLMkVKTwnn-1rNjQMYxmEqC3AnFqAQ.png" group-title="News", L BBC News SD')
    print('http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VlrhzospQYsoYZr4U6PCTu8')
    print('#EXTINF:-1 tvg-name="A BBC News HD" tvg-id="bbcnews.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/b9b3b82193b3008b23bc3d1a70eb8783.png" group-title="News", A BBC News HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P-nIH7f1zUPeNGeatH1tK3J/ts')
    print('#EXTINF:-1 tvg-name="A BBC News SD" tvg-id="bbcnews.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/3ca498c10344e1d56572b6cc307652d5.png" group-title="News", A BBC News SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P9mMvfe51wfTPmfw4O0x5NC/ts')
    print('#EXTINF:-1 tvg-name="F BBC News HD" tvg-name="bbcnews.uk" tvg-logo="https://archive.org/download/bbc_news_201711/bbc_news.png" group-title="News", F BBC News HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/603')
    print('#EXTINF:-1 tvg-name="F BBC News SD" tvg-name="bbcnews.uk" tvg-logo="https://archive.org/download/bbc_news_201711/bbc_news.png" group-title="News", F BBC News SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/688')
    print('#EXTINF:-1 tvg-id="bbcworldnews.us" tvg-logo="https://seeklogo.com/images/B/bbc-world-news-logo-10255C2E3B-seeklogo.com.png" group-title="News", BBC World News NZ Feed')
    print('http://10.1.3.202:8001/1:0:16:402:1:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="L CNN HD" tvg-id="cnn.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_Cnn/cnn.png" group-title="News", L CNN HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VtcZ4bOOo39NZxsHUyI9X1vKavHfKdJebGWQui8c_QoV")
    print('#EXTINF:-1 tvg-name="L CNN SD" tvg-id="cnn.uk" tvg-logo= "https://archive.org/download/stevechatfield27_gmail_Cnn/cnn.png" group-title="News", L CNN SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1Vl4E7kPY1rmnIICM6HtoJSY")
    print('#EXTINF:-1 tvg-name="A CNN HD" tvg-id="cnn.uk" tvg-logo="https://wedontlikepubliceyes22.me:443/images/9f3465cc11d8c754ffd0f3424726a9f3.png" group-title="News", A CNN HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8Vj10AUju_nCFXONaJK_Q5/ts')
    print('#EXTINF:-1 tvg-name="A CNN SD" tvg-id="cnn.uk" tvg-logo=https://wedontlikepubliceyes22.me:443/images/9f3465cc11d8c754ffd0f3424726a9f3.png" group-title="News", A CNN SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P89pD2KjujBfBZuo8Xmpino/ts')
    print('#EXTINF:-1 tvg-name="A CNN US HD" tvg-id="cnn.us" tvg-logo="https://wedontlikepubliceyes22.me:443/images/9f3465cc11d8c754ffd0f3424726a9f3.png" group-title="News", A CNN US HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8wxd3_upyi0U1Njlc-nx9t/ts')
    print('#EXTINF:-1 tvg-name="F CNN HD" tvg-id="cnn.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_Cnn/cnn.png" group-title="News", F CNN HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/284')
    print('#EXTINF:-1 tvg-name="F CNN SD" tvg-id="cnn.uk" tvg-logo="https://archive.org/download/stevechatfield27_gmail_Cnn/cnn.png" group-title="News", F CNN SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/662')
    print('#EXTINF:-1 tvg-name="CNN NZ Feed" tvg-id="cnn.us" tvg-logo="https://seeklogo.com/images/C/CNN-logo-8DA6D1FC28-seeklogo.com.png" group-title="News", CNN NZ Feed')
    print('http://10.1.3.199:8001/1:0:16:3F7:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-name="Al Jazeera NZ Feed" tvg-id="aljazeera.uk" tvg-logo="https://archive.org/download/AlJazeera_201708/al%20jazeera.png" group-title="News" , Al Jazeera NZ Feed')
    print('http://10.1.3.204:8001/1:0:16:4BC:D:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="sky.news.nz" tvg-logo="https://seeklogo.com/images/S/sky-news-australia-logo-252ABF9816-seeklogo.com.png" group-title="News", Sky News Australia')
    print('http://10.1.3.202:8001/1:0:16:3F9:1:A9:6400000:0:0:0:')
    print('http://0a895194.indifferent-project.net:2086/chrisgatesuk@hotmail.com/46dQ8dMl8e/662')
    print('#EXTINF:-1 tvg-name="L Sky Sports News HD" tvg-id="SSPONED" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrXvSHr9IagKkIzvw6fDn0pi8MPxojb_5AIFaAx8tJ7QDElXMLO5FSgA_NcI_U1tcRw.png" group-title="News", L Sky Sports News HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViZx7W0M4RpOMy7Ulmon0xr3XBQeX3NFoC_RgQ_jgzcr")
    print('#EXTINF:-1 tvg-name="L Sky Sports News SD" tvg-id="SSPONE" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrXvSHr9IagKkIzvw6fDn0pi8MPxojb_5AIFaAx8tJ7QDElXMLO5FSgA_NcI_U1tcRw.png" group-title="News", L Sky Sports News SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViZx7W0M4RpOMy7Ulmon0xp1NhcJz0nI_s0Sr_Wbemrn")
    print('#EXTINF:-1 tvg-name="A Sky Sports News HD" tvg-id="skysportsnews.uk" tv-logo="https://archive.org/download/SkySportsNewsHqNew_201708/sky%20sports%20news%20hq%20new.png" group-title="News", A Sky Sports News HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P-9SbkIk1Loup_qbAtc1ny6/ts')
    print('#EXTINF:-1 tvg-name="A Sky Sports News SD" tvg-id="skysportsnews.uk" tv-logo+"https://ia800806.us.archive.org/29/items/SkySportsNewsHqNew_201708/sky%20sports%20news%20hq%20new.png" group-title="News", A Sky Sports News SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_hMjQQOB9zp1IvuECQ2YOv/ts')
    print('#EXTINF:-1 tvg-name="F Sky Sports News HD" tvg-id="skysportsnews.uk" tv-logo="https://wedontlikepubliceyes22.me:443/images/CW4yR2X6FDejrPybenYCwDtQJz2Z7HyNavwwzdNtsx-ekbSRQiQvvs_ixMlqipzmBCJvmplaeCXbu2xl9oOO5k_C5eVqD-mdxIlOzDuw_Cg.jpg" group-title="News", F Sky Sports News HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:2086/chrisgatesuk@hotmail.com/46dQ8dMl8e/31')
    print('#EXTINF:-1 tvg-name="F Sky Sports News SD" tvg-id="skysportsnews.uk" tv-logo="https://wedontlikepubliceyes22.me:443/images/CW4yR2X6FDejrPybenYCwDtQJz2Z7HyNavwwzdNtsx-ekbSRQiQvvs_ixMlqipzmBCJvmplaeCXbu2xl9oOO5k_C5eVqD-mdxIlOzDuw_Cg.jpg" group-title="News", F Sky Sports News SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/29')
    print('#EXTINF:-1 tvg-name="L Sky Sports Main Event HD" tvg-id="SSPOMEH" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrfpplR_B_AZdYsIrHm-vf-scrgf7onwMqFn3yh6iZLMKm1Jhn0Ye0vs9t319FIiH8Q.png" group-title="UK Sports", L Sky Sports Main Event HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViAQBoNUsIsy_s1E_-s5ECN5cqo0T07GCem-qOUPyU_b")
    print('#EXTINF:-1 tvg-name="L Sky Sports Main Event SD" tvg-id="SSPOME" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrTyNIvjGSoxS4X4W2wFRGMLULxkKn23DA2WMB_zghNp6AR35l5t88ONQqZE9aUUmYw.png" group-title="UK Sports", L Sky Sports Main Event SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViAQBoNUsIsy_s1E_-s5ECNvclja7nueTNJ3BJQnxdKL")  
    print('#EXTINF:-1 tvg-name="A Sky Sports Main Event HD" tvg-id="SSPOMEH" tvg-logo="https://archive.org/download/SkySportsMainEvent_201708/sky%20sports%20main%20event.png" group-title="UK Sports", A Sky Sports Main Event HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P9wz-1phFF69w7tUCbYBbZz/ts')
    print('#EXTINF:-1 tvg-name="A Sky Sports Main Event SD" tvg-id="skysportsmainevent.uk" tvg-logo="https://archive.org/download/SkySportsMainEvent_201708/sky%20sports%20main%20event.png" group-title="UK Sports", A Sky Sports Main Event SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P-KbAv6b6ID3ZRpFAkVUUYY/ts')
    print('#EXTINF:-1 tvg-name="F Sky Sports Main Event HD" tvg-id="skysportsmainevent.uk" tvg-logo="https://archive.org/download/SkySportsMainEvent_201708/sky%20sports%20main%20event.png" group-title="UK Sports", F Sky Sports Main Event HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/11243')
    print('#EXTINF:-1 tvg-name="F Sky Sports Main Event SD" tvg-id="skysportsmainevent.uk" tvg-logo="https://archive.org/download/SkySportsMainEvent_201708/sky%20sports%20main%20event.png" group-title="UK Sports", F Sky Sports Main Event SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/11246')
    print('#EXTINF:-1 tvg-name="L TNT Sport 1 HD" tvg-id="BTSP1HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrbnNqbgSmPjNUZqJQsU6xJEl8nXIj9hgV_jBkVIM8_CKsxaXcMSjH1ImqJHHzfmLzg.png" group-title="UK Sports", L TNT Sport 1 HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VvqpXRFv0d1E1z1IS4FNHTp6AryAuClwMDCUt_EMfJAT")
    print('#EXTINF:-1 tvg-name="L TNT Sport 1 SD" tvg-id="BTSP1HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrSVAsUUCjWaNU9TO0iH5v-0cO74ZLYU9_TBgXYEJGguHPFY3sKODQM1eUsC4JNYFWQ.png" group-title="UK Sports", L TNT Sport 1 SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViZx7W0M4RpOMy7Ulmon0xoid37aP7LO50bT_iFltnsi")  
    print('#EXTINF:-1 tvg-name="A TNT Sport 1 HD" tvg-id="BTSP1HD" tvg-logo="https://wedontlikepubliceyes22.me:443/images/QIJDGRUBUEYTs6O3My3Uydj3CtEXyP8qEdsMa7VRLj_llgLaYojXGGHcTC6nOwfbGf6MDzrE_fjNRdUqyIEnoQkwzdct8vpHp2p0snIMVah8mC7HFrYtMKgjKq7aeyGCL1WuefIuopyaVrErGm0bL_mMfmVFJSr-uFiLVbpTaN4QVOLqJcLX9PFvWxald_w2.jpg" group-title="UK Sports", A TNT Sport 1 HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_ASp9muTDQMyC2e-g8vmKO/ts')
    print('#EXTINF:-1 tvg-name="A TNT Sport 1 SD" tvg-id="BTSP1HD" tvg-logo="https://wedontlikepubliceyes22.me:443/images/QIJDGRUBUEYTs6O3My3Uydj3CtEXyP8qEdsMa7VRLj_llgLaYojXGGHcTC6nOwfbGf6MDzrE_fjNRdUqyIEnoQkwzdct8vpHp2p0snIMVah8mC7HFrYtMKgjKq7aeyGCL1WuefIuopyaVrErGm0bL_mMfmVFJSr-uFiLVbpTaN4QVOLqJcLX9PFvWxald_w2.jpg" group-title="UK Sports", A TNT Sport 1 SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8uM6ju1H33nIDdf-ioMURu/ts')
    print('#EXTINF:-1 tvg-name="F TNT Sport 1 HD" tvg-id="btsport1.uk" tvg-logo="https://archive.org/download/BtSport1Hd_201708/bt%20sport%201%20hd.png" group-title="UK Sports", F TNT Sport 1 HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/11243')
    print('#EXTINF:-1 tvg-name="F TNT Sport 1 SD" tvg-id="btsport1.uk" tvg-logo="https://archive.org/download/BtSport1/bt%20sport%201.png" group-title="UK Sports", F TNT Sport 1 SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/11246')
    print('#EXTINF:-1 tvg-name="L TNT Sport 2 HD" tvg-id="BTSP2HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrbnNqbgSmPjNUZqJQsU6xJGcTkj5dv73TAwSF9YmMUkAgW2kYSplgXgiVzd6TANOQQ.png" group-title="UK Sports", L TNT Sport 2 HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VvqpXRFv0d1E1z1IS4FNHTp6AryAuClwMDCUt_EMfJAT")
    print('#EXTINF:-1 tvg-name="L TNT Sport 2 SD" tvg-id="BTSPOR2" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrSVAsUUCjWaNU9TO0iH5v-1L_v7O7kmtNMA80uFTPaH9kkMy-Lj07B1hc46nEzd1FQ.png" group-title="UK Sports", L TNT Sport 2 SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViZx7W0M4RpOMy7Ulmon0xoid37aP7LO50bT_iFltnsi")  
    print('#EXTINF:-1 tvg-name="A TNT Sport 2 HD" tvg-id="BTSP2HD" tvg-logo="https://wedontlikepubliceyes22.me:443/images/QIJDGRUBUEYTs6O3My3Uydj3CtEXyP8qEdsMa7VRLj_llgLaYojXGGHcTC6nOwfbGf6MDzrE_fjNRdUqyIEnoQkwzdct8vpHp2p0snIMVah8mC7HFrYtMKgjKq7aeyGCL1WuefIuopyaVrErGm0bL_mMfmVFJSr-uFiLVbpTaN4QVOLqJcLX9PFvWxald_w2.jpg" group-title="UK Sports", A TNT Sport 2 HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_ASp9muTDQMyC2e-g8vmKO/ts')
    print('#EXTINF:-1 tvg-name="A TNT Sport 2 SD" tvg-id="BTSPOR2" tvg-logo="https://wedontlikepubliceyes22.me:443/images/QIJDGRUBUEYTs6O3My3Uydj3CtEXyP8qEdsMa7VRLj_llgLaYojXGGHcTC6nOwfbGf6MDzrE_fjNRdUqyIEnoQkwzdct8vpHp2p0snIMVah8mC7HFrYtMKgjKq7aeyGCL1WuefIuopyaVrErGm0bL_mMfmVFJSr-uFiLVbpTaN4QVOLqJcLX9PFvWxald_w2.jpg" group-title="UK Sports", A TNT Sport 2 SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8uM6ju1H33nIDdf-ioMURu/ts')
    print('#EXTINF:-1 tvg-name="F TNT Sport 2 HD" tvg-id="btsport2.uk" tvg-logo="https://archive.org/download/BtSport2Hd/bt%20sport%202%20hd.png" group-title="UK Sports", F TNT Sport 2 HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/11243')
    print('#EXTINF:-1 tvg-name="F TNT Sports 2 SD" tvg-id="btsport2.uk" tvg-logo="https://archive.org/download/BtSport2_201708/bt%20sport%202.png" group-title="UK Sports", F TNT Sport 2 SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/11246')
    print('#EXTINF:-1 tvg-name="L TNT Sport 3 HD" tvg-id="BTSP3HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrSVAsUUCjWaNU9TO0iH5v-17IauvwrBP1QWi3A3y609RVSouYmZArCyA7n9z3IJBcg.png" group-title="UK Sports", L TNT Sport 3 HD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1VvqpXRFv0d1E1z1IS4FNHTp6AryAuClwMDCUt_EMfJAT")
    print('#EXTINF:-1 tvg-name="L TNT Sport 3 SD" tvg-id="BTSP3HD" tvg-logo="http://tv.st:80/images/SvlCE3pU-C0TyF1rEXMsrSVAsUUCjWaNU9TO0iH5v-17IauvwrBP1QWi3A3y609RVSouYmZArCyA7n9z3IJBcg.png" group-title="UK Sports", L TNT Sport 3 SD')
    print("http://litespeed.one:80/play/LGO1T4U-pLMTDDIkXXA1ViZx7W0M4RpOMy7Ulmon0xoid37aP7LO50bT_iFltnsi")  
    print('#EXTINF:-1 tvg-name="A TNT Sport 3 HD" tvg-id="BTSP3HD" tvg-logo="https://wedontlikepubliceyes22.me:443/images/QIJDGRUBUEYTs6O3My3Uydj3CtEXyP8qEdsMa7VRLj_llgLaYojXGGHcTC6nOwfbGf6MDzrE_fjNRdUqyIEnoQkwzdct8vpHp2p0snIMVah8mC7HFrYtMKgjKq7aeyGCL1WuefIuopyaVrErGm0bL_mMfmVFJSr-uFiLVbpTaN4QVOLqJcLX9PFvWxald_w2.jpg" group-title="UK Sports", A TNT Sport 3 HD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P_ASp9muTDQMyC2e-g8vmKO/ts')
    print('#EXTINF:-1 tvg-name="A TNT Sport 3 SD" tvg-id="BTSP3HD" tvg-logo="https://wedontlikepubliceyes22.me:443/images/QIJDGRUBUEYTs6O3My3Uydj3CtEXyP8qEdsMa7VRLj_llgLaYojXGGHcTC6nOwfbGf6MDzrE_fjNRdUqyIEnoQkwzdct8vpHp2p0snIMVah8mC7HFrYtMKgjKq7aeyGCL1WuefIuopyaVrErGm0bL_mMfmVFJSr-uFiLVbpTaN4QVOLqJcLX9PFvWxald_w2.jpg" group-title="UK Sports", A TNT Sport 3 SD')
    print('https://anovanatho.com:443/play/_dthI68MGlV5BHpeZGSotCwC0zpR3ee9XHJX2T6k8P8uM6ju1H33nIDdf-ioMURu/ts')
    print('#EXTINF:-1 tvg-name="F TNT Sport 3 HD" tvg-id="btsport3.uk" tvg-logo="https://archive.org/download/BtSport3Hd/bt%20sport%203%20hd.png" group-title="UK Sports", F TNT Sport 3 HD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/11243')
    print('#EXTINF:-1 tvg-name="F TNT Sport 3 SD" tvg-id="btsport3.uk" tvg-logo="https://archive.org/download/BtSport3/bt%20sport%203.png" group-title="UK Sports", F TNT Sport 3 SD')
    print('#EXTVLCOPT:network-caching=1000')
    print('http://0a895194.indifferent-project.net:80/chrisgatesuk@hotmail.com/46dQ8dMl8e/11246')  
    print('#EXTINF:-1 channel-id="mjh-trackside-1" tvg-id="mjh-trackside-1" tvg-logo="https://i.mjh.nz/.images/trackside-1.png" tvg-chno="62" group-title="NZ Sport" , TAB Trackside 1')
    print('https://i.mjh.nz/trackside-1.m3u8')
    print('#EXTINF:-1 channel-id="mjh-trackside-2" tvg-id="mjh-trackside-2" tvg-logo="https://i.mjh.nz/.images/trackside-2.png" tvg-chno="63" group-title="NZ Sport" , TAB Trackside 2')
    print('https://i.mjh.nz/trackside-2.m3u8')    
    print('#EXTINF:-1 tvg-id="mtv.nz" tvg-logo="https://seeklogo.com/images/M/mtv-music-television-logo-B016199701-seeklogo.com.png" group-title="Music", MTV NZ')
    print('http://10.1.3.199:8001/1:0:19:40F:B:A9:6400000:0:0:0:')
    print('#EXTINF:-1 tvg-id="mtv.music.nz" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/8/8e/MTV_80s_2022.png" group-title="Music", MTV 80s NZ')
    print('http://10.1.3.199:8001/1:0:16:498:B:A9:6400000:0:0:0:')
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
    print('#EXTINF:-1 tvg-id="Crown Hill Swimming Pool Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Crown Hill Swimming Pool Alt')
    print('rtsp://admin:Fnys0644@10.10.2.127')
    print('#EXTINF:-1 tvg-id="Minden Main Gate" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Main Gate')
    print('http://10.1.2.38:10000/h264/MindenMainGate/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Main Gate Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Main Gate Alt')
    print('rtsp://10.1.2.127:554/h264_stream')
    print('#EXTINF:-1 tvg-id="Minden PTZ" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden PTZ')
    print('http://10.1.2.38:10000/h264/PTZ/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden PTZ Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden PTZ Alt')
    print('rtsp://admin:Fnys0644@10.1.2.195:554')
    print('#EXTINF:-1 tvg-id="Minden Back Gate" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Back Gate')
    print('http://10.1.2.38:10000/h264/BackGate/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Back Gate Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Back Gate Alt')
    print('rtsp://admin:Fnys0644@10.1.2.159:554/main')
    print('#EXTINF:-1 tvg-id="Minden Front Door" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Front Door')
    print('http://10.1.2.38:10000/h264/FrontDoor/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Front Door Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Front Door Alt')
    print('rtsp://10.1.2.130:554/h264_stream')
    print('#EXTINF:-1 tvg-id="Minden Top Driveway" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Top Driveway')
    print('http://10.1.2.38:10000/h264/MindenTopDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Top Driveway Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Top Driveway Alt')
    print('rtsp://admin:Fnys0644@10.1.2.132:554/main')
    print('#EXTINF:-1 tvg-id="Minden Upper Driveway" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Upper Driveway')
    print('http://10.1.2.38:10000/h264/UpperDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Upper Driveway Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Upper Driveway Alt')
    print('rtsp://admin:Fnys0644@10.1.2.153:554')
    print('#EXTINF:-1 tvg-id="Minden Lower Driveway" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Lower Driveway')
    print('http://10.1.2.38:10000/h264/LowerDrive/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Lower Driveway Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Lower Driveway Alt')
    print('rtsp://admin:Fnys0644@10.1.2.154:554')
    print('#EXTINF:-1 tvg-id="Minden Side Lawn" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Side Lawn')
    print('http://10.1.2.38:10000/h264/SideLawn/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Side Lawn Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Side Lawn Alt')
    print('rtsp://admin:Fnys0644@10.1.2.83:554')
    print('#EXTINF:-1 tvg-id="Minden Swimming Pool" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Swimming Pool')
    print('http://10.1.2.38:10000/h264/SwimPool/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Swimming Pool Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Swimming Pool Alt')
    print('rtsp://admin:Fnys0644@10.1.2.84:554')
    print('#EXTINF:-1 tvg-id="Minden Garage" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Garage')
    print('http://10.1.2.38:10000/h264/MindenGarage/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Garage Alt" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Garage Alt')
    print('rtsp://Xm472C7UZWMr:Od8LVeobA3to@10.1.2.196/live0')
    print('#EXTINF:-1 tvg-id="Minden Keira Room" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Keira Room')
    print('http://10.1.2.38:10000/h264/Keira/temp.ts')
    print('#EXTINF:-1 tvg-id="Minden Alex Room" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Minden Alex Room')
    print('http://10.1.2.38:10000/h264/Alex/temp.ts')
    print('#EXTINF:-1 tvg-id="Weather" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", Weather')
    print('http://10.1.2.38:10000/h264/Weather/temp.ts')
    print('#EXTINF:-1 tvg-id="All Cameras" tvg-logo="https://seeklogo.com/images/C/cctv-logo-D5D8D6E4E2-seeklogo.com.png" group-title="CCTV", All Cameras')
    print('http://10.1.2.38:10000/h264/AllCameras/temp.ts')
    print('#EXTINF:-1 tvg-id="WG" group-title="Other", Other')
    print('http://80.82.76.70:80/play/LGO1T4U-pLMTDDIkXXA1VqBc2PMOIjfa3LkIYKDSdvE1C6zE-cbeikmb4WCk4jhA')
    print('#EXTINF:-1 tvg-id="Rick Astley Mash Up" group-title="Music", Rick Astley Mash Up')
    print('https://www.youtube.com/watch?v=oT3mCybbhf0&list=RDQMjViamB7LlcY&start_radio=1')
    print('#EXTINF:-1 tvg-id="Eye Of The Tiger Rolling In The Deep" group-title="Music", Eye Of The Tiger Rolling In The Deep')
    print('https://www.youtube.com/watch?v=JyQtmPmX0c0')
    print('#EXTINF:-1 tvg-id="Fat Bottommed Girls Sweet Home Alabama" group-title="Music", Fat Bottommed Girls Sweet Home Alabama')
    print('https://www.youtube.com/watch?v=IsKfdrWqW08')
    print('#EXTINF:-1 tvg-id="Avicii Men At Work" group-title="Music", Avicii Men At Work')
    print('https://www.youtube.com/watch?v=byl0BLtO7UE')
    print('#EXTINF:-1 tvg-id="Laurel And Hardy Mix 1" group-title="Music", Laurel And Hardy Mix 1')
    print('https://www.youtube.com/watch?v=If9qQ4XgabY')
    print('#EXTINF:-1 tvg-id="Laurel And Hardy Mix 2" group-title="Music", Laurel And Hardy Mix 2')
    print('https://www.youtube.com/embed/BXp5HAqRaxI?si=LcdAJGtBM-M23ERa')
    f.close()

# Remove temp files from project dir
if 'temp.txt' in os.listdir():
    os.system('rm temp.txt')
    os.system('rm watch*')

