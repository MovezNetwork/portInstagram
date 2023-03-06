import port.api.props as props
from port.api.commands import (CommandSystemDonate, CommandUIRender)
import port.whatsapp

def process(sessionId):
    yield donate(f"{sessionId}-tracking", '[{ "message": "user entered script" }]')

    platforms = ["Whatsapp","Whatsapp","Whatsapp","Whatsapp","Whatsapp"]

    subflows = len(platforms)
    steps = 2
    step_percentage = (100/subflows)/steps
    counter = 0
    # progress in %
    progress = 0

    donatedFileFlag = [False, False, False, False, False]

    for _, platform in enumerate(platforms):

        data = None
        progress += step_percentage
        counter = counter + 1

        while True:
            promptFile = prompt_file(platform,counter, "application/zip, text/plain",donatedFileFlag)
            fileResult = yield render_donation_page(platform, counter, promptFile, progress)
            if fileResult.__type__ == 'PayloadString':

                df_with_chats = port.whatsapp.parse_chat(fileResult.value)

                # If data extracted was successful
                if not df_with_chats.empty:

                    df_with_chats = port.whatsapp.remove_empty_chats(df_with_chats)
                    selection = yield prompt_radio_menu(platform, counter, progress, df_with_chats)
                    if selection.__type__ == "PayloadString":
                        # steps after selection
                        df_with_chats = port.whatsapp.filter_username(df_with_chats, selection.value)
                        df_with_chats = port.whatsapp.remove_name_column(df_with_chats)
                        df_with_chats = port.whatsapp.remove_date_column(df_with_chats)
                        list_with_df_with_chats = port.whatsapp.split_dataframe(df_with_chats, 5000)

                        data = list_with_df_with_chats

                        donatedFileFlag[counter-1] = True
                        break
                # If not enter retry flow
                else:
                    retry_result = yield render_donation_page(platform, counter, retry_confirmation(platform), progress)
                    if retry_result.__type__ == "PayloadTrue":
                        continue
                    else:
                        break
            else:
                break

        # STEP 2: ask for consent
        progress += step_percentage
        if not (data is None):
            prompt = prompt_consent(data)
            consent_result = yield render_donation_page(platform, counter, prompt, progress)
            if consent_result.__type__ == "PayloadJSON":
                yield donate(f"{sessionId}-{platform}", consent_result.value)

    yield render_end_page()



def prompt_radio_menu(platform, counter, progress, df_with_chats):

    title = props.Translatable({
        "en": f"",
        "nl": f""
    })
    description = props.Translatable({
        "en": f"Please select your username",
        "nl": f"Selecteer uw gebruikersnaam"
    })
    header = props.PropsUIHeader(props.Translatable({
        "en": 'Conversation ' + str(counter),
        "nl": 'Gesprek ' + str(counter)
    }))

    list_with_users = port.whatsapp.extract_users(df_with_chats)
    radio_input = [{"id": index, "value": username} for index, username in enumerate(list_with_users)]
    body = props.PropsUIPromptRadioInput(title, description, radio_input)
    footer = props.PropsUIFooter(progress)
    page = props.PropsUIPageDonation(platform, header, body, footer)
    return CommandUIRender(page)


def render_end_page():
    page = props.PropsUIPageEnd()
    return CommandUIRender(page)


def render_donation_page(platform,counter, body, progress):
    header = props.PropsUIHeader(props.Translatable({
        "en": 'Conversation ' + str(counter) + ' of 5',
        "nl": 'Conversation ' + str(counter) + ' of 5'
    }))


    footer = props.PropsUIFooter(progress)
    page = props.PropsUIPageDonation(platform, header, body, footer)
    return CommandUIRender(page)


def retry_confirmation(platform):
    text = props.Translatable({
        "en": f"Unfortunately, we cannot process your {platform} file. Continue, if you are sure that you selected the right file. Try again to select a different file.",
        "nl": f"Helaas, kunnen we uw {platform} bestand niet verwerken. Weet u zeker dat u het juiste bestand heeft gekozen? Ga dan verder. Probeer opnieuw als u een ander bestand wilt kiezen."
    })
    ok = props.Translatable({
        "en": "Try again",
        "nl": "Probeer opnieuw"
    })
    cancel = props.Translatable({
        "en": "Continue",
        "nl": "Verder"
    })
    return props.PropsUIPromptConfirm(text, ok, cancel)


def prompt_file(platform,counter, extensions,donatedFileFlag):
    promptStringsSuccess = ['Hi, you are about to donate your first whatsapp file. ',
    f'You have successfully donated your first file. It\'s time for the second one.',
    'Nice, your second upload was successful. Let\'s move to the third file.',
    'Great, we got that. You have two files left. Expecting your fourth whatsapp now.',
    'Fourth file done! We are almost there, you are about to donate your last whatsapp file. ']

    # only valid from the second round.
    promptStringNoSuscess = ['Ups, no file was donated in the previous step (File 1). Want to try from stratch again?',
    'Ups, no file was donated in the previous step (File 2). Want to try from stratch again?',
    'Ups, no file was donated in the previous step (File 3). Want to try from stratch again?',
    'Ups, no file was donated in the previous step (File 4). Want to try from stratch again?']

    descriptionString = ''

    print('prompt_file counter: ', counter)
    print('prompt_file promptStrings: ', promptStringsSuccess[counter-1])
    print('prompt_file donatedFileFlag: ', donatedFileFlag)

    if(counter >=2 and donatedFileFlag[counter-2] == False):
        descriptionString = promptStringNoSuscess[counter-2]
    else:
        descriptionString = promptStringsSuccess[counter-1]


    description = props.Translatable({
        "en": f"Please follow the download instructions and choose the file that you stored on your device. Click “Skip” at the right bottom, if you do not have a {platform} file. ",
        "nl": descriptionString
    })

    return props.PropsUIPromptFileInput(description, extensions)



def prompt_consent(list_with_df_with_chats):

    table_title = props.Translatable({
        "en": "Zip file contents",
        "nl": "Inhoud zip bestand"
    })

    table_list = [props.PropsUIPromptConsentFormTable(f"zip_content: {index}", table_title, df)
        for index, df in enumerate(list_with_df_with_chats)]

    return props.PropsUIPromptConsentForm(table_list, [])


def donate(key, json_string):
    return CommandSystemDonate(key, json_string)
