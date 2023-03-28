import logging
import json
import io

import pandas as pd

import port.api.props as props
from port.api.commands import (CommandSystemDonate, CommandUIRender)

import port.instagram as instagram
import port.unzipddp as unzipddp

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
                "nl": "Your personal info:",
            }
    ),
    "instagram_messages_summary": props.Translatable(
            {
                "en": "Your messages summary:",
                "nl": "Your messages summary:",
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
        print('prompt_consent dataframe', df)
        table = props.PropsUIPromptConsentFormTable(f"{platform_name}_{k}", v["title"], df)
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
    """
    USE THE IMPORTEDFUNCTIONS FROM port.instagram HERE

    I LEFT SOME EXAMPLES
    """
    result = {}

    validation = instagram.validate_zip(instagram_zip)

    # interests_bytes = unzipddp.extract_file_from_zip(instagram_zip, "ads_interests.json")
    # interests_dict = unzipddp.read_json_from_bytes(interests_bytes)
    # interests = instagram.interests_to_list(interests_dict)
    # if interests:
    #     df = pd.DataFrame(interests, columns=["Interests"])
    #     result["interests"] = {"data": df, "title": TABLE_TITLES["instagram_interests"]}

    #extracting personal information file
    pinfo_bytes = unzipddp.extract_file_from_zip(instagram_zip, "personal_information.json")
    pinfo_dict = unzipddp.read_json_from_bytes(pinfo_bytes)
    your_pinfo = instagram.personal_information_to_list(pinfo_dict)

    #extracting personal information file
    followers_bytes = unzipddp.extract_file_from_zip(instagram_zip, "followers_1.json")
    followers_dict = unzipddp.read_json_from_bytes(followers_bytes)
    print('followers_dict followers_dict, ',followers_dict)
    #extracting personal information file
    following_bytes = unzipddp.extract_file_from_zip(instagram_zip, "following.json")
    following_dict = unzipddp.read_json_from_bytes(following_bytes)

    your_pinfo.append(instagram.followers_to_list(followers_dict))
    your_pinfo.append(instagram.following_to_list(following_dict))
    print('your_pinfo ',your_pinfo)
    if your_pinfo:
        # We need to perform some data wrangling in this step
        df = pd.DataFrame([tuple(your_pinfo)], columns=["insta_name", "gender", "date of birth", "private account", "n_followers", "n_following"])
        result["your_info"] = {"data": df, "title": TABLE_TITLES["instagram_your_personal_info"]}

    messages_list_dict = unzipddp.extract_messages_from_zip(instagram_zip)
    print(len(messages_list_dict))
    # print(messages_list_dict[0])
    your_messages = instagram.process_message_json(messages_list_dict)

    df = pd.DataFrame(your_messages, columns=["alter_name", "alter_insta_username", "n_messages", "n_words", "n_chars"])
    print(df.dtypes)
    # df[["n_messages", "n_words", "n_chars"]] = df[["n_messages", "n_words", "n_chars"]].apply(pd.to_numeric)
    # print(df.dtypes)
    # print('BEFORE SORT', df)

    df = df.sort_values("n_chars",ascending=False)
    # print('AFTER SORT', df)
    result["your_messages"] = {"data":  df, "title": TABLE_TITLES["instagram_messages_summary"]}
    # print('pinfo_dict: ', your_pinfo)

    # your_topics_bytes = unzipddp.extract_file_from_zip(instagram_zip, "your_topics.json")
    # your_topics_dict = unzipddp.read_json_from_bytes(your_topics_bytes)
    # your_topics = instagram.your_topics_to_list(your_topics_dict)
    # if your_topics:
    #     # We need to perform some data wrangling in this step
    #     df = pd.DataFrame(your_topics, columns=["Your Topics"])
    #     result["your_topics"] = {"data": df, "title": TABLE_TITLES["instagram_your_topics"]}

    return validation, result


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
