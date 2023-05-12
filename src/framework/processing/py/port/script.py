import logging
import json
import io

import pandas as pd

import port.api.props as props
from port.api.commands import (CommandSystemDonate, CommandUIRender)

import port.instagram as instagram
import port.unzipddp as unzipddp
from port.validate import DDPFiletype

LOG_STREAM = io.StringIO()

logging.basicConfig(
    #stream=LOG_STREAM,  # comment this line if you want the logs in std out
    level=logging.INFO,  # change to DEBUG for debugging logs
    format="%(asctime)s --- %(name)s --- %(levelname)s --- %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)

LOGGER = logging.getLogger(__name__)

TABLE_TITLES = {
    "instagram_your_topics": props.Translatable(
        {
            "en": "Topics in which you are interested in according to Instagram:",
            "nl": "Onderwerpen waar jij volgens Instagram geintereseerd in bent:",
        }
    ),
    "instagram_interests": props.Translatable(
        {
            "en": "Your interests according to Instagram:",
            "nl": "Jouw interesses volgens Instagram:",
        }
    ),
    "instagram_your_personal_info": props.Translatable(
            {
                "en": "Your personal info:",
                "nl": "Jouw persoonlijke informatie:",
            }
    ),
    "instagram_your_likes": props.Translatable(
            {
                "en": "Your likes:",
                "nl": "Jouw likes:",
            }
    ),
    "instagram_messages_summary": props.Translatable(
            {
                "en": "Your messages summary:",
                "nl": "Samenvatting van de berichten:",
            }
    ),
    "empty_result_set": props.Translatable(
        {
            "en": "We could not extract any data:",
            "nl": "We konden de gegevens niet in je donatie vinden:",
        }
    ),
}


def process(sessionId):
    LOGGER.info("Starting the donation flow")
    yield donate_logs(f"{sessionId}-tracking")

    platforms = [
        ("Instagram", extract_instagram),
    ]

    # progress in %
    subflows = len(platforms)
    steps = 2
    step_percentage = (100 / subflows) / steps
    progress = 0

    for platform in platforms:
        platform_name, extraction_fun = platform
        data = None

        # STEP 1: select the file
        progress += step_percentage
        while True:
            LOGGER.info("Prompt for file for %s", platform_name)
            yield donate_logs(f"{sessionId}-tracking")

            promptFile = prompt_file("application/zip, text/plain", platform_name)
            fileResult = yield render_donation_page(platform_name, promptFile, progress)

            if fileResult.__type__ == "PayloadString":
                validation, extractionResult = extraction_fun(fileResult.value)

                # Flow: Three paths
                # 1: Extracted result: continue (regardless of validation)
                # 2: No extracted result: valid package, generated empty df: continue
                # 3: No extracted result: not a valid package, retry loop

                if extractionResult:
                    LOGGER.info("Payload for %s", platform_name)
                    yield donate_logs(f"{sessionId}-tracking")
                    data = extractionResult
                    break
                elif (validation.status_code.id == 0 and not extractionResult and validation.ddp_category is not None):
                    LOGGER.info("Valid zip for %s; No payload", platform_name)
                    yield donate_logs(f"{sessionId}-tracking")
                    data = return_empty_result_set()
                    break
                elif validation.ddp_category is None:
                    LOGGER.info("Not a valid %s zip; No payload; prompt retry_confirmation", platform_name)
                    yield donate_logs(f"{sessionId}-tracking")
                    retry_result = yield render_donation_page(platform_name, retry_confirmation(platform_name), progress)

                    if retry_result.__type__ == "PayloadTrue":
                        continue
                    else:
                        LOGGER.info("Skipped during retry %s", platform_name)
                        yield donate_logs(f"{sessionId}-tracking")
                        #data = return_empty_result_set()
                        break
            else:
                LOGGER.info("Skipped %s", platform_name)
                yield donate_logs(f"{sessionId}-tracking")
                break

        # STEP 2: ask for consent
        progress += step_percentage

        if data is not None:
            LOGGER.info("Prompt consent; %s", platform_name)
            yield donate_logs(f"{sessionId}-tracking")

            prompt = prompt_consent(platform_name, data)
            consent_result = yield render_donation_page(platform_name, prompt, progress)

            if consent_result.__type__ == "PayloadJSON":
                LOGGER.info("Data donated; %s", platform_name)
                yield donate_logs(f"{sessionId}-tracking")
                yield donate(platform_name, consent_result.value)
            else:
                LOGGER.info("Skipped ater reviewing consent: %s", platform_name)
                yield donate_logs(f"{sessionId}-tracking")

    yield render_end_page()



##################################################################
# helper functions

def prompt_consent(platform_name, data):
    """
    Function collects extracted in data and assembles them in
    PropsUIPromptConsentForm which can be rendered on screen
    for the participant to approve

    Args:
        platform_name: name of the platform
        data: dict with keys with references to {df, title}

    Returns:
        return_type: PropsUIPromptConsentFormTable
    """

    table_list = []

    for k, v in data.items():
        df = v["data"]
        adjustable = v.get("adjustable", True)
        table = props.PropsUIPromptConsentFormTable(f"{platform_name}_{k}", v["title"], df, adjustable)
        table_list.append(table)

    return props.PropsUIPromptConsentForm(table_list, [])


def return_empty_result_set():
    result = {}

    df = pd.DataFrame(["No data found"], columns=["No data found"])
    result["empty"] = {"data": df, "title": TABLE_TITLES["empty_result_set"]}

    return result


def donate_logs(key):
    log_string = LOG_STREAM.getvalue()  # read the log stream

    if log_string:
        log_data = log_string.split("\n")
    else:
        log_data = ["no logs"]

    return donate(key, json.dumps(log_data))


def extract_instagram(instagram_zip):

    validation = instagram.validate_zip(instagram_zip)
    result = {}

    if validation.ddp_category is None:
        pass
    elif validation.ddp_category.ddp_filetype == DDPFiletype.JSON:
        result = extract_instagram_json(instagram_zip)
    elif validation.ddp_category.ddp_filetype == DDPFiletype.HTML:
        result = extract_instagram_html(instagram_zip)

    return validation, result


##############################################################
# Extract json

def extract_instagram_json(instagram_zip):
    result = {}

    #extracting personal information file
    pinfo_bytes = unzipddp.extract_file_from_zip(instagram_zip, "personal_information.json")
    pinfo_dict = unzipddp.read_json_from_bytes(pinfo_bytes)

    if pinfo_dict:
        your_pinfo = instagram.personal_information_to_list(pinfo_dict)

        #extracting followers file
        followers_bytes = unzipddp.extract_file_from_zip(instagram_zip, "followers_1.json")
        followers_dict = unzipddp.read_json_from_bytes(followers_bytes)

        #extracting following_dict file
        following_bytes = unzipddp.extract_file_from_zip(instagram_zip, "following.json")
        following_dict = unzipddp.read_json_from_bytes(following_bytes)

        your_pinfo.append(instagram.followers_to_list(followers_dict))
        your_pinfo.append(instagram.following_to_list(following_dict))

        df = pd.DataFrame([tuple(your_pinfo)], columns=["Username", "Hashed Username","Display Name","Hashed Display Name","Gender", "Date of birth", "Private account", "Number Followers", "Number Following"])
        result["your_info"] = {"data": df, "title": TABLE_TITLES["instagram_your_personal_info"], "adjustable": False}

    # extracting messages
    messages_list_dict = unzipddp.extract_messages_from_zip(instagram_zip)
    your_messages = instagram.process_message_json(messages_list_dict)

    if your_messages:
        df = pd.DataFrame(your_messages, columns=["Display Name","Hashed Display Name", "Number of Messages", "Number of Words", "Number of Characters"])
        df = df.sort_values("Number of Messages", ascending=False).reset_index(drop=True)
        result["your_messages"] = {"data":  df, "title": TABLE_TITLES["instagram_messages_summary"]}

    # extracting liked_posts file
    liked_posts_bytes = unzipddp.extract_file_from_zip(instagram_zip, "liked_posts.json")
    liked_posts_dict = unzipddp.read_json_from_bytes(liked_posts_bytes)
    liked_comments_bytes = unzipddp.extract_file_from_zip(instagram_zip, "liked_comments.json")
    liked_comments_dict = unzipddp.read_json_from_bytes(liked_comments_bytes)

    if liked_posts_dict and liked_posts_dict:
        df = instagram.liked_posts_comments_to_df(liked_posts_dict, liked_comments_dict)
        df = df.sort_values("Number Liked Posts", ascending=False).reset_index(drop=True)
        if not df.empty:
            result["your_likes"] = {"data": df, "title": TABLE_TITLES["instagram_your_likes"]}

    return result

##############################################################
# Extract html

def extract_instagram_html(instagram_zip):
    result = {}

    # extracting personal information file
    pinfo_bytes = unzipddp.extract_file_from_zip(instagram_zip, "personal_information.html")
    your_pinfo = instagram.personal_information_to_list_html(pinfo_bytes)

    if your_pinfo:

        # add n followers
        followers_bytes = unzipddp.extract_file_from_zip(instagram_zip, "followers_1.html")
        followers = instagram.followers_to_list_html(followers_bytes)
        your_pinfo.append(followers)

        # add n following
        following_bytes = unzipddp.extract_file_from_zip(instagram_zip, "following.html")
        following = instagram.followers_to_list_html(following_bytes)
        your_pinfo.append(following)

        df = pd.DataFrame([tuple(your_pinfo)], columns=["Username", "Hashed Username","Display Name","Hashed Display Name","Gender", "Date of birth", "Private account", "Number Followers", "Number Following"])
        result["your_info"] = {"data": df, "title": TABLE_TITLES["instagram_your_personal_info"], "adjustable": False}

    # extracting messages
    your_messages = instagram.process_message_html(instagram_zip)

    if your_messages:
        df = pd.DataFrame(your_messages, columns=["Display Name","Hashed Display Name", "Number of Messages", "Number of Words", "Number of Characters"])
        df = df.sort_values("Number of Messages", ascending=False).reset_index(drop=True)
        result["your_messages"] = {"data":  df, "title": TABLE_TITLES["instagram_messages_summary"]}

    # extracting liked_posts file
    liked_posts_bytes = unzipddp.extract_file_from_zip(instagram_zip, "liked_posts.html")
    liked_comments_bytes = unzipddp.extract_file_from_zip(instagram_zip, "liked_comments.html")

    df = instagram.liked_posts_comments_to_df_html(liked_posts_bytes, liked_comments_bytes)
    if not df.empty:
        df = df.sort_values("Number Liked Posts", ascending=False).reset_index(drop=True)
        if not df.empty:
            result["your_likes"] = {"data": df, "title": TABLE_TITLES["instagram_your_likes"]}

    return result

##########################################
# Functions provided by Eyra did not change

def render_end_page():
    page = props.PropsUIPageEnd()
    return CommandUIRender(page)


def render_donation_page(platform, body, progress):
    header = props.PropsUIHeader(props.Translatable({"en": platform, "nl": platform}))
    footer = props.PropsUIFooter(progress)
    page = props.PropsUIPageDonation(platform, header, body, footer)
    return CommandUIRender(page)


def retry_confirmation(platform):
    text = props.Translatable(
        {
            "en": f"Unfortunately, we could not process your {platform} file. If you are sure that you selected the correct file, press Continue. To select a different file, press Try again.",
            "nl": f"Helaas, kunnen we uw {platform} bestand niet verwerken. Weet u zeker dat u het juiste bestand heeft gekozen? Ga dan verder. Probeer opnieuw als u een ander bestand wilt kiezen."
        }
    )
    ok = props.Translatable({"en": "Try again", "nl": "Probeer opnieuw"})
    cancel = props.Translatable({"en": "Continue", "nl": "Verder"})
    return props.PropsUIPromptConfirm(text, ok, cancel)


def prompt_file(extensions, platform):
    description = props.Translatable(
        {
            "en": f"Please follow the download instructions and choose the file that you stored on your device. Click “Skip” at the right bottom, if you do not have a file from {platform}.",
            "nl": f"Volg de download instructies en kies het bestand dat u opgeslagen heeft op uw apparaat. Als u geen {platform} bestand heeft klik dan op “Overslaan” rechts onder."
        }
    )
    return props.PropsUIPromptFileInput(description, extensions)


def donate(key, json_string):
    return CommandSystemDonate(key, json_string)
