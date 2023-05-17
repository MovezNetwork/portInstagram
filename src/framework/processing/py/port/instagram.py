"""
DDP Instagram module

This module contains functions to handle *.jons files contained within an instagram ddp
"""

from typing import Any
from pathlib import Path
import logging
import zipfile
import re
import string
import pandas as pd
import hashlib
import io

from collections import Counter
from lxml import etree

from port.validate import (
    DDPCategory,
    StatusCode,
    ValidateInput,
    Language,
    DDPFiletype,
)

logger = logging.getLogger(__name__)

DDP_CATEGORIES = [
    DDPCategory(
        id="json",
        ddp_filetype=DDPFiletype.JSON,
        language=Language.EN,
        known_files=["secret_conversations.json", "personal_information.json", "account_privacy_changes.json", "account_based_in.json", "recently_deleted_content.json", "liked_posts.json", "stories.json", "profile_photos.json", "followers.json", "signup_information.json", "comments_allowed_from.json", "login_activity.json", "your_topics.json", "camera_information.json", "recent_follow_requests.json", "devices.json", "professional_information.json", "follow_requests_you've_received.json", "eligibility.json", "pending_follow_requests.json", "videos_watched.json", "ads_interests.json", "account_searches.json", "following.json", "posts_viewed.json", "recently_unfollowed_accounts.json", "post_comments.json", "account_information.json", "accounts_you're_not_interested_in.json", "use_cross-app_messaging.json", "profile_changes.json", "reels.json", "message_1.json"],
    ),
    DDPCategory(
        id="html",
        ddp_filetype=DDPFiletype.HTML,
        language=Language.EN,
        known_files=["liked_comments.html", "liked_posts.html", "recently_deleted_content.html", "stories.html", "reels.html", "profile_photos.html", "posts_you're_not_interested_in.html", "posts_viewed.html", "accounts_you're_not_interested_in.html", "your_topics.html", "restricted_accounts.html", "followers_1.html", "pending_follow_requests.html", "recent_follow_requests.html", "following.html", "removed_suggestions.html", "profile_changes.html", "personal_information.html", "account_information.html", "professional_information.html", "logout_activity.html", "login_activity.html", "signup_information.html", "last_known_location.html", "account_privacy_changes.html", "use_cross-app_messaging.html", "comments_allowed_from.html", "chats.html", "secret_conversations.html", "word_or_phrase_searches.html", "account_searches.html", "account_based_in.html", "ads_interests.html", "devices.html", "camera_information.html", "index.html", "advertisers_using_your_activity_or_information.html", "post_comments.html", "story_likes.html", "polls.html", "eligibility.html"]
    )
]

STATUS_CODES = [
    StatusCode(id=0, description="Valid zip", message="Valid zip"),
    StatusCode(id=1, description="Bad zipfile", message="Bad zipfile"),
]


def validate_zip(zfile: Path) -> ValidateInput:
    """
    Validates the input of an Instagram zipfile
    """

    validate = ValidateInput(STATUS_CODES, DDP_CATEGORIES)

    try:
        paths = []
        with zipfile.ZipFile(zfile, "r") as zf:
            for f in zf.namelist():
                p = Path(f)
                if p.suffix in (".html", ".json"):
                    logger.debug("Found: %s in zip", p.name)
                    paths.append(p.name)

        validate.set_status_code(0)
        validate.infer_ddp_category(paths)
    except zipfile.BadZipFile:
        validate.set_status_code(1)

    return validate


def fix_string_encoding(input: str) -> str:
    """
    Fixes the string encoding by attempting to encode it using the 'latin1' encoding and then decoding it.

    Args:
        input (str): The input string that needs to be fixed.

    Returns:
        str: The fixed string after encoding and decoding, or the original string if an exception occurs.
    """
    try:
        fixed_string = input.encode("latin1").decode()
        return fixed_string
    except Exception:
        return input


def personal_information_to_list(dict_with_pinfo: dict[Any, Any] | Any) -> list[str]:
    """
    This function extracts instagram personal information from a dict
    This dict should be obtained from personal_information.json
    personal_information.json content is language dependent

    This function should be rewritten as personal_information.json changes
    """
    out = []

    try:
        if not isinstance(dict_with_pinfo, dict):
            raise TypeError("The input to this function was not dict")

        #print('dict_with_pinfo: ',dict_with_pinfo)
        # dict_with_pinfo["profile_user"][0]["string_map_data"]["Username"]
        username = ''
        hashed_uname = ''
        displayname = ''
        hashed_dname = ''
        gender = ''
        dateofbirth = ''
        private_account = ''

        # we are handling english and dutch only for now
        if dict_with_pinfo["profile_user"][0]["string_map_data"].get('Username') is not None:
            username = dict_with_pinfo["profile_user"][0]["string_map_data"]["Username"]["value"]
        elif dict_with_pinfo["profile_user"][0]["string_map_data"].get('Gebruikersnaam') is not None:
            username = dict_with_pinfo["profile_user"][0]["string_map_data"]["Gebruikersnaam"]["value"]


        if dict_with_pinfo["profile_user"][0]["string_map_data"].get('Name') is not None:
            displayname = dict_with_pinfo["profile_user"][0]["string_map_data"]["Name"]["value"]
        elif dict_with_pinfo["profile_user"][0]["string_map_data"].get('Naam') is not None:
            displayname = dict_with_pinfo["profile_user"][0]["string_map_data"]["Naam"]["value"]


        if dict_with_pinfo["profile_user"][0]["string_map_data"].get('Gender') is not None:
            gender = dict_with_pinfo["profile_user"][0]["string_map_data"]["Gender"]["value"]
        elif dict_with_pinfo["profile_user"][0]["string_map_data"].get('Geslacht') is not None:
            gender = dict_with_pinfo["profile_user"][0]["string_map_data"]["Geslacht"]["value"]



        # What is the english version of it? Get insta examples.
        if dict_with_pinfo["profile_user"][0]["string_map_data"].get('Dateofbirth') is not None:
            dateofbirth = dict_with_pinfo["profile_user"][0]["string_map_data"]["Dateofbirth"]["value"]
        elif dict_with_pinfo["profile_user"][0]["string_map_data"].get('Geboortedatum') is not None:
            dateofbirth = dict_with_pinfo["profile_user"][0]["string_map_data"]["Geboortedatum"]["value"]



        if dict_with_pinfo["profile_user"][0]["string_map_data"].get('Private Account') is not None:
            private_account = dict_with_pinfo["profile_user"][0]["string_map_data"]["Private Account"]["value"]
        elif dict_with_pinfo["profile_user"][0]["string_map_data"].get(u'PrivÃ©account') is not None:
            private_account = dict_with_pinfo["profile_user"][0]["string_map_data"][u"PrivÃ©account"]["value"]


        out.append(username)
        hashed_uname = username.encode()
        out.append(hashlib.sha256(hashed_uname).hexdigest())

        out.append(displayname)
        hashed_dname = displayname.encode()
        out.append(hashlib.sha256(hashed_dname).hexdigest())

        out.append(gender)
        out.append(dateofbirth)
        out.append(private_account)



    except TypeError as e:
        logger.error("TypeError: %s", e)
    except KeyError as e:
        logger.error("The a dict did not contain the key: %s", e)
    except Exception as e:
        logger.error("Exception was caught:  %s", e)

    finally:
        return out

# Personal information to list html
def personal_information_to_list_html(html_in: io.BytesIO) -> list[Any]:
    html = html_in.read()

    info = {
        "Username": "username",
        "Gebruikersnaam": "username",
        "Name": "displayname",
        "Naam": "displayname",
        "Gender": "gender",
        "Geslacht": "gender",
        "Date of birth": "dateofbirth",
        "Geboortedatum": "dateofbirth",
        "Private Account": "private_account",
        "PRIVATE ACCOUNT IN DUTCH": "private_account",
    }

    extracted_info = {}
    try:
        tree = etree.HTML(html)
        table_with_personal_info_class = "_2pin _a6_q"
        r = tree.xpath(f"//td[@class='{table_with_personal_info_class}']")

        for e in r:
            for x in e:
                if e.text in info:
                    extracted_info[info[e.text]] = x.getchildren()[0].text
    except Exception as e:
        logger.error("Error: %s", e)

    username = extracted_info.get("username", "")
    hashed_uname = hashlib.sha256(username.encode()).hexdigest()
    displayname = extracted_info.get("displayname", "")
    hashed_dname = hashlib.sha256(displayname.encode()).hexdigest()

    out = [
        username,
        hashed_uname,
        displayname,
        hashed_dname,
        extracted_info.get("gender", ""),
        extracted_info.get("dateofbirth", ""),
        extracted_info.get("private_account", ""),
    ]

    return out


def followers_to_list(dict_with_followers: list[Any] | Any) -> list[str]:
    """
    This function extracts instagram your_topics from a dict
    This dict should be obtained from your_topics.json

    This function should be rewritten as your_topics.json changes
    """
    out = 0

    try:
        if not isinstance(dict_with_followers, list):
            raise TypeError("The input to this function was not dict followers_to_list")

        #print('Followers length ', len(dict_with_followers))
        out = len(dict_with_followers)

    except TypeError as e:
        logger.error("TypeError: %s", e)
    except KeyError as e:
        logger.error("The a dict did not contain the key: %s", e)
    except Exception as e:
        logger.error("Exception was caught:  %s", e)

    finally:
        return out


def following_to_list(dict_with_following: dict[Any, Any] | Any) -> list[str]:
    """
    This function extracts instagram your_topics from a dict
    This dict should be obtained from your_topics.json

    This function should be rewritten as your_topics.json changes
    """
    out = 0

    try:
        if not isinstance(dict_with_following, dict):
            raise TypeError("The input to this function was not dict")

        #print('Following length ', len(dict_with_following['relationships_following']))
        out = len(dict_with_following['relationships_following'])

    except TypeError as e:
        logger.error("TypeError: %s", e)
    except KeyError as e:
        logger.error("The a dict did not contain the key: %s", e)
    except Exception as e:
        logger.error("Exception was caught: %s", e)

    finally:
        return out


def followers_to_list_html(html_in: io.BytesIO) -> str:
    """
    Works for followers_1.html and for following.html
    """
    html = html_in.read()
    out = ""
    try:
        tree = etree.HTML(html)
        follows_div_class = "pam _3-95 _2ph- _a6-g uiBoxWhite noborder"
        r = tree.xpath(f"//div[@class='{follows_div_class}']")
        out = str(len(r))

    except Exception as e:
        logger.error("Error: %s", e)

    return out


def following_to_list_html(html) -> str:
    return followers_to_list_html(html)


def process_message_json(messages_list_dict: list[Any] | Any) -> list[str]:
    """
    This function extracts instagram your_topics from a dict
    This dict should be obtained from your_topics.json

    This function should be rewritten as your_topics.json changes
    """
    out = []
    printable = set(string.printable)

    try:
        if not isinstance(messages_list_dict, list):
            raise TypeError("The input to this function was not list")
        # loop through every dict
        for mes in messages_list_dict:
            alter_username = mes["title"]
            # alter_insta = mes["thread_path"][6:mes["thread_path"].rfind("_")]
            alter_husername = ''
            # alter_hinsta = ''

            num_chars = 0
            num_words = 0
            num_messages = 0
            #print(mes["title"],mes["thread_path"],mes["thread_path"][6:mes["thread_path"].rfind("_")])
            #print('Chats with ', alter_username,alter_insta)

            #skipping all the group chats
            if(len(mes["participants"])==2):
                for m in mes["messages"]:

                    if(m["sender_name"] != alter_username and m.get("content") is not None):
                        num_messages = num_messages + 1
                        # removing potential non-ascii characters
                        sender_mes = ''.join(filter(lambda x: x in printable, m["content"]))
                        # removing potential extra white spaces
                        sender_mes = " ".join(sender_mes.split())
                        # counting the words
                        num_words = num_words + len(re.findall(r'\w+', sender_mes))
                        # counting the chars
                        num_chars = num_chars + len(sender_mes)
                        # Comment out if you want to see message details
                        #print(m["sender_name"], sender_mes, num_words, num_chars)

                        #print(m["content"],''.join(filter(lambda x: x in #printable, m["content"])),m["sender_name"])
                #print(alter_username, alter_insta, num_messages, num_words, num_chars)
                alter_username = fix_string_encoding(alter_username)
                alter_husername = alter_username.encode()
                # alter_hinsta = alter_insta.encode()

                out.append((alter_username,hashlib.sha256(alter_husername).hexdigest(), num_messages, num_words, num_chars))

    except TypeError as e:
        logger.error("TypeError: %s", e)
    except KeyError as e:
        logger.error("The a dict did not contain the key: %s", e)
    except Exception as e:
        logger.error("Exception was caught:  %s", e)

    finally:
        return out


def process_messages(html: bytes) -> list[Any]:
    """
    Extracts the relevant characteristics from an html
    containing messages (message_1.html)
    """
    printable = set(string.printable)

    num_chars = 0
    num_words = 0
    num_messages = 0
    alter_username = ""
    alter_husername = ""

    try:
        tree = etree.HTML(html)

        # Obtain the name of the alter
        alter_div_class="_3-8y _3-95 _a70a"
        r = tree.xpath(f"//div[@class='{alter_div_class}']//div[@class='_a70e']")
        alter_username = r[0].text
        alter_husername = hashlib.sha256(alter_username.encode()).hexdigest()

        # Loop through all messages that are not send by the alter
        # and all plain text components from those messages
        messages = []

        message_class="pam _3-95 _2ph- _a6-g uiBoxWhite noborder"
        r = tree.xpath(f"//div[@class='{message_class}']")
        for e in r:
            children = e.getchildren()
            sender_name = children[0].text
            if alter_username != sender_name:
                num_messages += 1

                # Text is stored in plain divs look for all plain divs
                plain_divs = e.xpath("div//div")
                for e in plain_divs:
                    if e.text:
                        messages.append(e.text)

        # Extract meta data from the messages
        for message in messages:
            sender_mes = ''.join(filter(lambda x: x in printable, message))
            # removing potential extra white spaces
            sender_mes = " ".join(sender_mes.split())
            # counting the words
            num_words = num_words + len(re.findall(r'\w+', sender_mes))
            # counting the chars
            num_chars = num_chars + len(sender_mes)

    except Exception as e:
        logger.error("Error: %s", e)

    return [alter_username, alter_husername, num_messages, num_words, num_chars]



def process_message_html(path_to_zip) -> list[list[Any]]:
    """
    Reads all files with message_1.html in the file name
    processes those htmls with process_messages
    """

    out = []

    try:
        with zipfile.ZipFile(path_to_zip, 'r') as zf:
            for filename in zf.namelist():
                if 'message_1.html' in filename:
                    with zf.open(filename, 'r') as f:
                        html_with_messages = f.read()
                        out.append(process_messages(html_with_messages))

    except Exception as e:
        logger.error("Error: %s", e)

    return out


def liked_posts_comments_to_df(liked_posts_dict: dict[Any, Any], liked_comments_dict: dict[Any, Any] | Any) -> pd.DataFrame:
    #print(liked_posts_dict,liked_comments_dict)
    df_posts = pd.DataFrame(liked_posts_dict["likes_media_likes"])
    df_posts = df_posts.groupby('title').count().reset_index()

    df_posts.columns = ['alter_username', 'nliked_posts']

    df_comments = pd.DataFrame(liked_comments_dict["likes_comment_likes"])
    df_comments = df_comments.groupby('title').count().reset_index()
    df_comments.columns = ['alter_username', 'nliked_comments']


    df_likes = pd.merge(df_posts, df_comments, on="alter_username", how="outer")
    df_likes = df_likes.fillna(0)
    df_likes = df_likes.sort_values("nliked_posts",ascending=False)
    df_likes['alter_username'] = df_likes['alter_username'].astype(str)
    # Apply hashing function to the column
    df_likes['hashed_alter_username'] = df_likes['alter_username'].apply(
        lambda x:
            hashlib.sha256(x.encode()).hexdigest()
    )

    df_likes.columns = ['Gebruikersnaam', 'Berichten met likes', 'Reacties met likes', 'Hashed Gebruikersnaam']
    df_likes = df_likes[['Gebruikersnaam', 'Hashed Gebruikersnaam', 'Berichten met likes', 'Reacties met likes']]
    #print('df_likes df_posts df_commentsshape', df_likes.shape,df_posts.shape,df_comments.shape)
    #print('df.duplicated ',df_likes[df_likes.duplicated(['alter_username'])])
    return df_likes



def extract_likes_html(html_in: io.BytesIO) -> pd.DataFrame:
    """
    Works for liked_posts.html and liked_comments.html
    """
    html = html_in.read()

    out = pd.DataFrame()
    try:
        liked_posts = []
        tree = etree.HTML(html)
        liked_post_class = "_3-95 _2pim _a6-h _a6-i"
        r = tree.xpath(f"//div[@class='{liked_post_class}']")
        for e in r:
            liked_posts.append(e.text)

        data_points = [
            (alter_name, hashlib.sha256(alter_name.encode()).hexdigest(), count)
            for alter_name, count in Counter(liked_posts).items()
        ]
        out = pd.DataFrame(data_points)

    except Exception as e:
        logger.error("Error: %s", e)

    return out


def liked_posts_comments_to_df_html(posts_html: io.BytesIO, comments_html: io.BytesIO) -> pd.DataFrame:

    posts = extract_likes_html(posts_html)
    comments =  extract_likes_html(comments_html)

    out = pd.DataFrame()
    try:
        merged_df = pd.merge(posts, comments, on=[0, 1], how="outer").fillna(0)
        merged_df.columns = ["Gebruikersnaam", "Hashed Gebruikersnaam", "Berichten met likes", "Reacties met likes"]
        out = merged_df.sort_values("Berichten met likes", ascending=False).reset_index(drop=True)
    except Exception as e:
        logger.error("Error: %s", e)

    return out
