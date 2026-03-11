import json
import time
import logging
import random
import requests
from urllib.parse import urlparse
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

API_KEY = os.getenv("SOCIALDATA_API_KEY")
COMMUNITY_ID = "1965795131186954572"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}

ALL_TWEETS_FILE = "all_tweets.json"
LEADERBOARD_FILE = "leaderboard.json"

LINK_TWEETS = [
    "https://twitter.com/miketwinks/status/2009228460464521593",
    "https://twitter.com/jacks12300711/status/1990711670499385494",
    "https://twitter.com/jacks12300711/status/1991123841674846261",
    "https://twitter.com/jacks12300711/status/1991600494406684714",
    "https://twitter.com/jacks12300711/status/1992326454005428606",
    "https://twitter.com/jacks12300711/status/1993051269750239722",
    "https://twitter.com/jacks12300711/status/1993792499434037318",
    "https://twitter.com/jacks12300711/status/1995083592066793944",
    "https://twitter.com/jacks12300711/status/1996480946216874462",
    "https://twitter.com/jacks12300711/status/1997238765493145988",
    "https://twitter.com/sterjke/status/1998399545173065737",
    "https://twitter.com/sterjke/status/1995806817977303262",
    "https://twitter.com/sterjke/status/1995113365790732463",
    "https://twitter.com/sterjke/status/1994332535438930429",
    "https://twitter.com/sterjke/status/1993256776318304368",
    "https://twitter.com/sterjke/status/1992590589376778719",
    "https://twitter.com/sterjke/status/1992126672762736752",
    "https://twitter.com/sterjke/status/1991493055099154573",
    "https://twitter.com/alextropilo/status/1978732024144826429",
    "https://twitter.com/alextropilo/status/1979231076372414871",
    "https://twitter.com/alextropilo/status/1979554040036966435",
    "https://twitter.com/alextropilo/status/1979839348284817629",
    "https://twitter.com/alextropilo/status/1980618935121650012",
    "https://twitter.com/alextropilo/status/1980918661658403076",
    "https://twitter.com/alextropilo/status/1981729400505720903",
    "https://twitter.com/alextropilo/status/1982365798560895342",
    "https://twitter.com/alextropilo/status/1983234513477026225",
    "https://twitter.com/alextropilo/status/1983808605787689238",
    "https://twitter.com/alextropilo/status/1984692225020747811",
    "https://twitter.com/alextropilo/status/1985375634822991957",
    "https://twitter.com/alextropilo/status/1986377496267194517",
    "https://twitter.com/alextropilo/status/1987171300540924081",
    "https://twitter.com/alextropilo/status/1987814118980731347",
    "https://twitter.com/alextropilo/status/1988582002153693256",
    "https://twitter.com/alextropilo/status/1989640924805435712",
    "https://twitter.com/alextropilo/status/1990469666092007518",
    "https://twitter.com/alextropilo/status/1991125412982772130",
    "https://twitter.com/alextropilo/status/1992641888348938691",
    "https://twitter.com/alextropilo/status/1993589280778928422",
    "https://twitter.com/alextropilo/status/1994736114536456239",
    "https://twitter.com/alextropilo/status/1995890637221105818",
    "https://twitter.com/alextropilo/status/1996956279038730365",
    "https://twitter.com/alextropilo/status/1998077772686631081",
    "https://twitter.com/alextropilo/status/1999081356610138392",
    "https://twitter.com/alextropilo/status/2000157429791957324",
    "https://twitter.com/alextropilo/status/2001258613361504742",
    "https://twitter.com/alextropilo/status/2002357699573338620",
    "https://twitter.com/alextropilo/status/2003441876041691342",
    "https://twitter.com/alextropilo/status/2004472619748516189",
    "https://twitter.com/nofelonyx/status/1983913742690652659",
    "https://twitter.com/Vikki_arts/status/1992932553096044805",
    "https://twitter.com/Vikki_arts/status/1993651266187309295",
    "https://twitter.com/Vikki_arts/status/1993998155600576528",
    "https://twitter.com/Vikki_arts/status/1994767841631871418",
    "https://twitter.com/Vikki_arts/status/1995480606008807721",
    "https://twitter.com/Vikki_arts/status/1996502675220033915",
    "https://twitter.com/Dannnnnok/status/2003835160295621057",
    "https://twitter.com/Dannnnnok/status/2001362597107687790",
    "https://twitter.com/Dannnnnok/status/2000313860327150011",
    "https://twitter.com/Dannnnnok/status/1998854094132535494",
    "https://twitter.com/Dannnnnok/status/1997690658484547856",
    "https://twitter.com/Dannnnnok/status/1997036599440560214",
    "https://twitter.com/Dannnnnok/status/1995519293963035130",
    "https://twitter.com/Dannnnnok/status/1994151619748081742",
    "https://twitter.com/Dannnnnok/status/1993378980053856647",
    "https://twitter.com/Dannnnnok/status/1992684194695197060",
    "https://twitter.com/Dannnnnok/status/1990845915775541483",
    "https://twitter.com/Dannnnnok/status/1990799743174529164",
    "https://twitter.com/Dannnnnok/status/1990504947675263294",
    "https://twitter.com/Dannnnnok/status/1990140558908547549",
    "https://twitter.com/Dannnnnok/status/1989349397361271263",
    "https://twitter.com/Dannnnnok/status/1988689478731673725",
    "https://twitter.com/Dannnnnok/status/1987961987242864935",
    "https://twitter.com/Dannnnnok/status/1987236079427256812",
    "https://twitter.com/Dannnnnok/status/1986465394463310215",
    "https://twitter.com/Dannnnnok/status/1985772685327286770",
    "https://twitter.com/Dannnnnok/status/1985053903717532039",
    "https://twitter.com/Dannnnnok/status/1983966373417250846",
    "https://twitter.com/dannnnnok/status/1983484402186555840",
    "https://twitter.com/Dannnnnok/status/1982908128346984599",
    "https://twitter.com/Dannnnnok/status/1980329556864057443",
    "https://twitter.com/dannnnnok/status/1979959995979514044",
    "https://twitter.com/Dannnnnok/status/1979606915157024975",
    "https://twitter.com/Dannnnnok/status/1979206201477915129",
    "https://twitter.com/Dannnnnok/status/1978830474605727851",
    "https://twitter.com/1Asgore1/status/2005532478061105459",
    "https://twitter.com/1Asgore1/status/1998842830098411670",
    "https://twitter.com/1Asgore1/status/1998117623842906205",
    "https://twitter.com/i/status/1995895585937957168",
    "https://twitter.com/1Asgore1/status/1981606629465563291",
    "https://twitter.com/1Asgore1/status/1981606629465563291",
    "https://twitter.com/slimice111/status/1998797227943202937",
    "https:/twitter.com/SaiMoo_n/status/1990705695096709503",
    "https://twitter.com/SaiMoo_n/status/1987144853847691300",
    "https://twitter.com/SaiMoo_n/status/1982812627165221297",
    "https://twitter.com/SaiMoo_n/status/1982364436527521935",  
    "https://twitter.com/i/status/2003828392173416527",
    "https://twitter.com/i/status/2002728154117317047",
    "https://twitter.com/i/status/2001285353781571800",
    "https://twitter.com/i/status/2000229082525839866",
    "https://twitter.com/i/status/1999475109594366050",
    "https://twitter.com/i/status/1998808372666339739",
    "https://twitter.com/Ramosbdjf/status/1998004065511317675",
    "https://twitter.com/Ramosbdjf/status/1997699876948504646",
    "https://twitter.com/Ramosbdjf/status/1997248592830971968",
    "https://twitter.com/Ramosbdjf/status/1996815471203471740",
    "https://twitter.com/Ramosbdjf/status/1996276662816645140",
    "https://twitter.com/Ramosbdjf/status/1996521456335724798",
    "https://twitter.com/Ramosbdjf/status/1995765064041640257",
    "https://twitter.com/Ramosbdjf/status/1995511727882977508",
    "https://twitter.com/Ramosbdjf/status/1995187018121506905",
    "https://twitter.com/Ramosbdjf/status/1994068974792003786",
    "https://twitter.com/Ramosbdjf/status/1993286047086653532",
    "https://twitter.com/Ramosbdjf/status/1992998030904275364",
    "https://twitter.com/Ramosbdjf/status/1992614517746860287",
    "https://twitter.com/Ramosbdjf/status/1992207273620361270",
    "https://twitter.com/Ramosbdjf/status/1991839457704624327",
    "https://twitter.com/Ramosbdjf/status/1991212164934148183",
    "https://twitter.com/Ramosbdjf/status/1990736315386605756",
    "https://twitter.com/Ramosbdjf/status/1990410662380466300",
    "https://twitter.com/Ramosbdjf/status/1990031860504637697",
    "https://twitter.com/Ramosbdjf/status/1989642650429915281",
    "https://twitter.com/Ramosbdjf/status/1989393441500049490",
    "https://twitter.com/Ramosbdjf/status/1988662053578428804",
    "https://twitter.com/Ramosbdjf/status/1988237796859916548",
    "https://twitter.com/Ramosbdjf/status/1987492922229457354",
    "https://twitter.com/Ramosbdjf/status/1987156062827352241",
    "https://twitter.com/Ramosbdjf/status/1986744836158877942",
    "https://twitter.com/Ramosbdjf/status/1986488738818531471",
    "https://twitter.com/Ramosbdjf/status/1986374539559797153",
    "https://twitter.com/Ramosbdjf/status/1985991179452711301",
    "https://twitter.com/Ramosbdjf/status/1985681487404875920",
    "https://twitter.com/Ramosbdjf/status/1985365881375871069",
    "https://twitter.com/Ramosbdjf/status/1985042589951672527",
    "https://twitter.com/Ramosbdjf/status/1984629957054579158",
    "https://twitter.com/Ramosbdjf/status/1983541615349100549",
    "https://twitter.com/Ramosbdjf/status/1983420620969779304",
    "https://twitter.com/Ramosbdjf/status/1983187362533572703",
    "https://twitter.com/Ramosbdjf/status/1982751628169003196",
    "https://twitter.com/i/status/2004896052164370797",
    "https://twitter.com/i/status/2004538034453135719",
    "https://twitter.com/i/status/2004171608567521455",
    "https://twitter.com/SkywayCapitan/status/1981070819897069874",
    "https://twitter.com/SkywayCapitan/status/1981799116519919762",
    "https://twitter.com/SkywayCapitan/status/1983223063689691317",
    "https://twitter.com/SkywayCapitan/status/1983301807029018854",
    "https://twitter.com/SkywayCapitan/status/1983866464064114849",
    "https://twitter.com/SkywayCapitan/status/1985462441627562495",
    "https://twitter.com/SkywayCapitan/status/1986515691303002135",
    "https://twitter.com/SkywayCapitan/status/1987186825346392082",
    "https://twitter.com/SkywayCapitan/status/1989028033542406486",
    "https://twitter.com/SkywayCapitan/status/1989785765359095917",
    "https://twitter.com/SkywayCapitan/status/1991206257026314302",
    "https://twitter.com/SkywayCapitan/status/1991522379433160793",
    "https://twitter.com/SkywayCapitan/status/1992984343233593755",
    "https://twitter.com/SkywayCapitan/status/1994049219871510667",
    "https://twitter.com/SkywayCapitan/status/1995882167415832638",
    "https://twitter.com/SkywayCapitan/status/1997062571593970004",
    "https://twitter.com/SkywayCapitan/status/1998124065077252551",
    "https://twitter.com/SkywayCapitan/status/1998747423032635489",
    "https://twitter.com/SkywayCapitan/status/1999924386531520860",
    "https://twitter.com/SkywayCapitan/status/2002451540653830252",
    "https://twitter.com/SkywayCapitan/status/2004273677962301537",
    "https://twitter.com/SkywayCapitan/status/2006425420733046790",
    "https://twitter.com/SkywayCapitan/status/2008297907259076985",
    "https://twitter.com/SkywayCapitan/status/2010607084510101665",
    "https://twitter.com/SkywayCapitan/status/1980694430811320425",
    "https://twitter.com/SkywayCapitan/status/1990864863237710086",
    "https://twitter.com/SkywayCapitan/status/1982439912038191613",
    "https://twitter.com/Vikki_arts/status/2011732479414321600",
    "https://twitter.com/nofelonyx/status/1983913742690652659",
    "https://twitter.com/SkywayCapitan/status/2013047838008098817",
    "https://twitter.com/alextropilo/status/2005947259834228784",
    "https://twitter.com/1Asgore1/status/2012246798178423031",
    "https://twitter.com/1Asgore1/status/2011877770113270236",
    "https://twitter.com/1Asgore1/status/2011156500702732661",
    "https:/twitter.com/1Asgore1/status/2010809115334136275",
    "https://twitter.com/1Asgore1/status/2008981784944656703",
    "https://twitter.com/1Asgore1/status/2005532478061105459",
    "https://twitter.com/1Asgore1/status/2013678966884966741",
    "https://twitter.com/Angelin75231626/status/1990485476332220679",
    "https://twitter.com/Angelin75231626/status/1995209251351093496",
    "https://twitter.com/Angelin75231626/status/1995729735872066029",
    "https://twitter.com/Angelin75231626/status/2000833237049073715",
    "https://twitter.com/Angelin75231626/status/2001538054864183636",
    "https://twitter.com/Angelin75231626/status/2002965119211626570",
    "https://twitter.com/Angelin75231626/status/2006757059484856603",
    "https://twitter.com/Angelin75231626/status/2009692706692645036",
    "https://twitter.com/Angelin75231626/status/2010298193981182335",
    "https://twitter.com/Angelin75231626/status/2011153054738116814",
    "https://twitter.com/Angelin75231626/status/2011796293564215671",
    "https://twitter.com/Angelin75231626/status/2013114399041474718",
    "https://twitter.com/Angelin75231626/status/2013901600515883331",
    "https://twitter.com/Angelin75231626/status/2014664545386557732",
    "https://twitter.com/Angelin75231626/status/2015685528859881541",
    "https://twitter.com/Angelin75231626/status/2016482100757639568",
    "https://twitter.com/Angelin75231626/status/2017922543173181702",
    "https://twitter.com/Angelin75231626/status/2019637015621562591",
    "https://twitter.com/Angelin75231626/status/2020164888874631427",
    "https://twitter.com/Angelin75231626/status/2020747663499485427",
    "https://twitter.com/Angelin75231626/status/2021873851668324773",
    "https://twitter.com/Angelin75231626/status/2022967243068592270",
    "https://twitter.com/Angelin75231626/status/2024388589925105775",
    "https://twitter.com/harddeki/status/2027433175257849889",
    "https://twitter.com/harddeki/status/2026335004058370501",
    "https://twitter.com/harddeki/status/2023165824614174851",
    "https://twitter.com/Skybornfx/status/1978611770437611865",
    "https://twitter.com/Skybornfx/status/1979533112666193981",
    "https://twitter.com/Skybornfx/status/1979963253020053509",
    "https://twitter.com/Skybornfx/status/1980308194405560651",
    "https://twitter.com/Skybornfx/status/1980796392315433211",
    "https://twitter.com/Skybornfx/status/1981133537945510235",
    "https://twitter.com/Skybornfx/status/1981809097910685774",
    "https://twitter.com/Skybornfx/status/1982599597081210935",
    "https://twitter.com/Skybornfx/status/1983327742948188221",
    "https://twitter.com/Skybornfx/status/1984170286535577850",
    "https://twitter.com/Skybornfx/status/1984740334283391381",
    "https://twitter.com/Skybornfx/status/1985401923512537273",
    "https://twitter.com/Skybornfx/status/1985842965617512511",
    "https://twitter.com/Skybornfx/status/1986056693487112573",
    "https://twitter.com/Skybornfx/status/1986575401859137752",
    "https://twitter.com/Skybornfx/status/1987324884272152770",
    "https://twitter.com/Skybornfx/status/1986780660460089630",
    "https://twitter.com/Skybornfx/status/1987328415557689831",
    "https://twitter.com/Skybornfx/status/1987280534716760338",
    "https://twitter.com/Skybornfx/status/1987544879136981293",
    "https://twitter.com/Skybornfx/status/1987544874581651666",
    "https://twitter.com/Skybornfx/status/1988028239864856790",
    "https://twitter.com/Skybornfx/status/1988261689049924060",
    "https://twitter.com/Skybornfx/status/1988383599767302511",
    "https://twitter.com/Skybornfx/status/1988590420830650529",
    "https://twitter.com/Skybornfx/status/1988669936617873580",
    "https://twitter.com/Skybornfx/status/1988941448813900125",
    "https://twitter.com/Skybornfx/status/1988941443705209322",
    "https://twitter.com/Skybornfx/status/1989299609387073741",
    "https://twitter.com/Skybornfx/status/1989491724490617312",
    "https://twitter.com/Skybornfx/status/1989685757368316139",
    "https://twitter.com/Skybornfx/status/1990084511518920783",
    "https://twitter.com/Skybornfx/status/1990190910093590891",
    "https://twitter.com/Skybornfx/status/1990579433191973053",
    "https://twitter.com/Skybornfx/status/1990923446994276824",
    "https://twitter.com/Skybornfx/status/1991114390058520604",
    "https://twitter.com/Skybornfx/status/1991276540139589680",
    "https://twitter.com/Skybornfx/status/1991604045040263249",
    "https://twitter.com/Skybornfx/status/1991818742662111621",
    "https://twitter.com/Skybornfx/status/1992022002727620918",
    "https://twitter.com/Skybornfx/status/1992259005889327335",
    "https://twitter.com/Skybornfx/status/1992370148259332347",
    "https://twitter.com/Skybornfx/status/1992569573560791534",
    "https://twitter.com/Skybornfx/status/1992722268921749520",
    "https://twitter.com/Skybornfx/status/1992958801969127917",
    "https://twitter.com/Skybornfx/status/1993361820531171530",
    "https://twitter.com/Skybornfx/status/1993475511612580122",
    "https://twitter.com/Skybornfx/status/1993683667021881509",
    "https://twitter.com/Skybornfx/status/1993829603492983060",
    "https://twitter.com/Skybornfx/status/1994048061031473173",
    "https://twitter.com/Skybornfx/status/1994370944056570122",
    "https://twitter.com/Skybornfx/status/1994573944956096568",
    "https://twitter.com/Skybornfx/status/1994812808400363996",
    "https://twitter.com/Skybornfx/status/1994900365431705756",
    "https://twitter.com/Skybornfx/status/1995126465612915168",
    "https://twitter.com/Skybornfx/status/1995205921354764637",
    "https://twitter.com/Skybornfx/status/1995544819024998902",
    "https://twitter.com/Skybornfx/status/1997081181477916886",
    "https://twitter.com/Skybornfx/status/1997873924042846436",
    "https://twitter.com/Skybornfx/status/1998076322946466273",
    "https://twitter.com/Skybornfx/status/1999459105086263584",
    "https://twitter.com/Skybornfx/status/1999901346900643975",
    "https://twitter.com/Skybornfx/status/2001353949602062669",
    "https://twitter.com/Skybornfx/status/2003881400932454487",
    "https://twitter.com/Skybornfx/status/2011106353537040476",
    "https://twitter.com/Skybornfx/status/2012334552237170758",
    "https://twitter.com/Skybornfx/status/2013985565117448228",
    "https://twitter.com/Skybornfx/status/2014700239555293292",
    "https://twitter.com/Skybornfx/status/2016920900214415580",
    "https://twitter.com/Skybornfx/status/2017747963485839566",
    "https://twitter.com/Skybornfx/status/2020140702378742229",
    "https://twitter.com/Skybornfx/status/2021512405466182130",
    "https://twitter.com/Skybornfx/status/2021942403515752890",
    "https://twitter.com/Skybornfx/status/2022768835401576959",
    "https://twitter.com/Skybornfx/status/2024158837280768324",
    "https://twitter.com/Skybornfx/status/2024852893711352297",
    "https://twitter.com/Skybornfx/status/2026377103659225156",
    "https://twitter.com/Skybornfx/status/2027402930488262916",
    "https://twitter.com/Skybornfx/status/2027402925832561075",
    "https://twitter.com/Skybornfx/status/2028228814300398070",
    "https://twitter.com/Skybornfx/status/2028568800795279700",
    "https://twitter.com/Skybornfx/status/2030045551278821859",
    "https://twitter.com/Skybornfx/status/2030045547294261261",
    "https://twitter.com/Skybornfx/status/2031709858345402875",
  ] 
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_tweet_id(tweet_url: str) -> str:
    parsed = urlparse(tweet_url)
    parts = parsed.path.strip("/").split("/")
    if "status" in parts:
        idx = parts.index("status")
        return parts[idx + 1].split("?")[0]
    raise ValueError(f"Не могу извлечь ID из URL: {tweet_url}")




def safe_request(url, params=None, retries=8, timeout=30):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()

        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            logging.warning(f"⛔ NETWORK ISSUE {attempt}/{retries} — retrying...")

        except requests.exceptions.RequestException as e:
            logging.warning(f"⚠ Ошибка сети ({attempt}/{retries}): {e}")

        sleep_time = min(12, 2**attempt + random.uniform(0, 1))
        logging.info(f"⏳ Жду {sleep_time:.1f} сек и повторяю...")
        time.sleep(sleep_time)

    raise RuntimeError(f"❌ API не отвечает после {retries} попыток: {url}")




def extract_best_video(media):
    if media.get("type") not in ("video", "animated_gif"):
        return None

    variants = media.get("video_info", {}).get("variants", [])
    if not variants:
        return None

    video_variants = [
        v for v in variants
        if v.get("content_type", "").startswith("video")
    ]

    if not video_variants:
        return None

    best = max(video_variants, key=lambda v: v.get("bitrate", 0))
    return best.get("url")


def extract_media(tweet):
    media = []

    if "extended_entities" in tweet and "media" in tweet["extended_entities"]:
        media = tweet["extended_entities"]["media"]
    elif "entities" in tweet and "media" in tweet["entities"]:
        media = tweet["entities"]["media"]
    elif "media" in tweet:
        media = tweet["media"]

    unique = []
    seen = set()

    for m in media:
        url = m.get("media_url_https") or m.get("media_url")
        if not url:
            continue

        if url in seen:
            continue  # удаление дубля

        seen.add(url)

        unique.append({
            "type": m.get("type"),
            "url": url,
            "thumb": m.get("url"),
            "video_url": extract_best_video(m),
        })

    return unique




def normalize_tweet(tweet: dict) -> dict:
    user = tweet.get("user", {}) or {}
    text = tweet.get("full_text") or tweet.get("text")

    return {
        "created_at": tweet.get("tweet_created_at") or tweet.get("created_at"),
        "id_str": tweet.get("id_str"),
        "text": text,
        "favorite_count": tweet.get("favorite_count", 0),
        "retweet_count": tweet.get("retweet_count", 0),
        "reply_count": tweet.get("reply_count", 0),
        "views_count": tweet.get("views_count", 0),
        "quote_count": tweet.get("quote_count", 0),
        "media": extract_media(tweet),
        "user": {
            "screen_name": user.get("screen_name"),
            "name": user.get("name"),
            "profile_image_url":
                user.get("profile_image_url_https") or user.get("profile_image_url"),
        }
    }




def fetch_community_page(cursor=None, limit=100):
    params = {"type": "Latest", "limit": limit}
    if cursor:
        params["cursor"] = cursor

    url = f"https://api.socialdata.tools/twitter/community/{COMMUNITY_ID}/tweets"
    return safe_request(url, params=params)


def collect_all_community_tweets():
    logging.info("\n=========== СБОР КОМЬЮНИТИ — УМНЫЙ РЕЖИМ ===========")

    all_tweets = []
    seen = set()
    cursor = None
    page = 0

    while True:
        page += 1
        logging.info(f"\n---- СТРАНИЦА #{page} ---- cursor={cursor}")

        data = fetch_community_page(cursor)
        tweets = data.get("tweets", [])
        next_cursor = data.get("next_cursor")

        logging.info(f"Получено твитов: {len(tweets)}, next_cursor={next_cursor}")

        new_count = 0
        for t in tweets:
            tid = t.get("id_str")
            if tid and tid not in seen:
                seen.add(tid)
                all_tweets.append(t)
                new_count += 1

        logging.info(f"➕ новых: {new_count} | всего: {len(all_tweets)}")

        if len(tweets) == 0:
            logging.warning("⚠ Пустая страница — проверяем, не ложный ли это конец...")

            retry_success = False

            # 1) 12 повторов
            for attempt in range(1, 13):
                delay = attempt
                logging.info(f"🔄 Повтор #{attempt}, жду {delay} сек...")
                time.sleep(delay)

                retry = fetch_community_page(cursor)
                retry_tweets = retry.get("tweets", [])
                retry_cursor = retry.get("next_cursor")

                if retry_tweets:
                    logging.info("✔ ЛОЖНЫЙ КОНЕЦ: данные появились!")

                    added = 0
                    for t in retry_tweets:
                        tid = t.get("id_str")
                        if tid and tid not in seen:
                            seen.add(tid)
                            all_tweets.append(t)
                            added += 1

                    logging.info(f"➕ добавлено после повтора: {added}")
                    tweets = retry_tweets
                    next_cursor = retry_cursor
                    retry_success = True
                    break

            # 2) если всё пусто — пауза 3 минуты
            if not retry_success:
                logging.warning("⏸ Пауза 3 минуты...")
                time.sleep(180)

                retry2 = fetch_community_page(cursor)
                retry2_tweets = retry2.get("tweets", [])
                retry2_cursor = retry2.get("next_cursor")

                if retry2_tweets:
                    logging.info("✔ После паузы данные появились!")

                    added = 0
                    for t in retry2_tweets:
                        tid = t.get("id_str")
                        if tid and tid not in seen:
                            seen.add(tid)
                            all_tweets.append(t)
                            added += 1

                    tweets = retry2_tweets
                    next_cursor = retry2_cursor
                else:
                    logging.info("🏁 Истинный конец — данных нет даже после паузы.")
                    break

        if next_cursor is None:
            logging.info("🏁 next_cursor=None — конец истории.")
            break

        cursor = next_cursor
        time.sleep(0.6)

    logging.info(f"\n=== ГОТОВО: собрано уникальных твитов: {len(all_tweets)} ===")
    return all_tweets




def fetch_single_tweet(tweet_id: str):
    url = f"https://api.socialdata.tools/twitter/tweets/{tweet_id}"
    return safe_request(url)


def collect_links_tweets():
    logging.info("\n=========== СБОР ТВИТОВ ПО ССЫЛКАМ ===========")
    results = []

    for url in LINK_TWEETS:
        logging.info(f"URL: {url}")

        try:
            tid = extract_tweet_id(url)
            raw = fetch_single_tweet(tid)
            results.append(normalize_tweet(raw))
            logging.info(f"✓ Успех: {tid}")

        except Exception as e:
            logging.error(f"✗ Ошибка для {url}: {e}")

    return results




def merge_tweets(community_raw, link_norm):
    logging.info("\n=========== ОБЪЕДИНЕНИЕ РЕЗУЛЬТАТОВ ===========")

    final = []
    seen = set()

    for tw in community_raw:
        n = normalize_tweet(tw)
        tid = n.get("id_str")
        if tid and tid not in seen:
            seen.add(tid)
            final.append(n)

    for tw in link_norm:
        tid = tw.get("id_str")
        if tid and tid not in seen:
            seen.add(tid)
            final.append(tw)

    logging.info(f"🔥 Итого после объединения: {len(final)} твитов")
    return final




def build_leaderboard(tweets):
    board = {}

    for t in tweets:
        user = (t.get("user") or {}).get("screen_name") or "unknown"
        pfp = (t.get("user") or {}).get("profile_image_url")

        stats = board.setdefault(user, {
            "profile_image_url": pfp,
            "posts": 0,
            "likes": 0,
            "retweets": 0,
            "comments": 0,
            "quotes": 0,
            "views": 0,
        })

        stats["posts"] += 1
        stats["likes"] += t.get("favorite_count", 0)
        stats["retweets"] += t.get("retweet_count", 0)
        stats["comments"] += t.get("reply_count", 0)
        stats["quotes"] += t.get("quote_count", 0)
        stats["views"] += t.get("views_count", 0)

    return [[user, stats] for user, stats in board.items()]




if __name__ == "__main__":
    community_raw = collect_all_community_tweets()
    link_tweets = collect_links_tweets()

    all_tweets = merge_tweets(community_raw, link_tweets)
    save_json(ALL_TWEETS_FILE, all_tweets)
    logging.info(f"💾 {ALL_TWEETS_FILE} сохранён ({len(all_tweets)} твитов)")

    leaderboard = build_leaderboard(all_tweets)
    save_json(LEADERBOARD_FILE, leaderboard)
    logging.info(f"💾 {LEADERBOARD_FILE} сохранён")















