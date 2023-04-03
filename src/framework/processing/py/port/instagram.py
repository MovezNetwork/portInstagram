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
import json
from itertools import groupby
import pandas as pd
import hashlib

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
        id="json_en",
        ddp_filetype=DDPFiletype.JSON,
        language=Language.EN,
        known_files=[
            "secret_conversations.json",
            "personal_information.json",
            "account_privacy_changes.json",
            "account_based_in.json",
            "recently_deleted_content.json",
            "liked_posts.json",
            "stories.json",
            "profile_photos.json",
            "followers.json",
            "signup_information.json",
            "comments_allowed_from.json",
            "login_activity.json",
            "your_topics.json",
            "camera_information.json",
            "recent_follow_requests.json",
            "devices.json",
            "professional_information.json",
            "follow_requests_you've_received.json",
            "eligibility.json",
            "pending_follow_requests.json",
            "videos_watched.json",
            "ads_interests.json",
            "account_searches.json",
            "following.json",
            "posts_viewed.json",
            "recently_unfollowed_accounts.json",
            "post_comments.json",
            "account_information.json",
            "accounts_you're_not_interested_in.json",
            "use_cross-app_messaging.json",
            "profile_changes.json",
            "reels.json",
            "message_1.json"
        ],
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


def interests_to_list(dict_with_interests: dict[Any, Any]) -> list[str]:
    """
    This function extracts instagram interests from a dict
    This dict should be obtained from ads_interests.json

    This function should be rewritten as ads_interests.json changes
    """
    out = []

    try:
        if not isinstance(dict_with_interests, dict):
            raise TypeError("The input to this function was not dict")

        # The compleet lookup is:
        # "inferred_data_ig_interest" -> "string_map_data" -> "Interesse"
        # "Interesse is the only key, and the spelling is dutch
        # I suspect this might change with difference language settings
        # Therefore popitem()
        for item in dict_with_interests["inferred_data_ig_interest"]:
            res = item["string_map_data"].popitem()
            out.append(res[1]["value"])

    except TypeError as e:
        logger.error("TypeError: %s", e)
    except KeyError as e:
        logger.error("The a dict did not contain key: %s", e)
    except Exception as e:
        logger.error("Exception was caught:  %s", e)

    finally:
        return out


def your_topics_to_list(dict_with_topics: dict[Any, Any] | Any) -> list[str]:
    """
    This function extracts instagram your_topics from a dict
    This dict should be obtained from your_topics.json

    This function should be rewritten as your_topics.json changes
    """
    out = []

    try:
        if not isinstance(dict_with_topics, dict):
            raise TypeError("The input to this function was not dict")

        # The compleet lookup is:
        # "topics_your_topics" -> "string_map_data" -> "Name" -> "value"
        # Dutch Language DDP is: "topics_your_topics" -> "string_map_data" -> "Naam" -> "value"
        # Note: popitem avoids hardcoding "Name" or "Naam"
        for item in dict_with_topics["topics_your_topics"]:
            res = item["string_map_data"].popitem()
            out.append(res[1]["value"])

    except TypeError as e:
        logger.error("TypeError: %s", e)
    except KeyError as e:
        logger.error("The a dict did not contain the key: %s", e)
    except Exception as e:
        logger.error("Exception was caught:  %s", e)

    finally:
        return out


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
        logger.error("Exception was caught:  %s", e)

    finally:
        return out


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

def liked_posts_comments_to_df(liked_posts_dict: dict[Any, Any], liked_comments_dict: dict[Any, Any] | Any) -> list[str]:
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

    df_likes.columns = ['Username', 'Number Liked Posts', 'Number Liked Comments', 'Hashed Username']
    df_likes = df_likes[['Username', 'Hashed Username', 'Number Liked Posts', 'Number Liked Comments']]
    #print('df_likes df_posts df_commentsshape', df_likes.shape,df_posts.shape,df_comments.shape)
    #print('df.duplicated ',df_likes[df_likes.duplicated(['alter_username'])])
    return df_likes
