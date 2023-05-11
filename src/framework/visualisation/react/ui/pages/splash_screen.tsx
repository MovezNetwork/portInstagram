import React from 'react'
import { Weak } from '../../../../helpers'
import TextBundle from '../../../../text_bundle'
import { Translator } from '../../../../translator'
import { PropsUIPageSplashScreen } from '../../../../types/pages'
import { ReactFactoryContext } from '../../factory'
import { PrimaryButton } from '../elements/button'
import { CheckBox } from '../elements/check_box'
import { Label, Title1 } from '../elements/text'
// import LogoSvg from '../../../../../assets/images/logo.svg'
import { Footer } from './templates/footer'
import { Page } from './templates/page'
import { Bullet } from '../elements/bullet'

interface Copy {
  title: string
  continueButton: string
  privacyLabel: string
}

type Props = Weak<PropsUIPageSplashScreen> & ReactFactoryContext

function prepareCopy ({ locale }: Props): Copy {
  return {
    title: Translator.translate(title, locale),
    continueButton: Translator.translate(continueButton, locale),
    privacyLabel: Translator.translate(privacyLabel, locale)
  }
}

export const SplashScreen = (props: Props): JSX.Element => {
  const [checked, setChecked] = React.useState<boolean>(false)
  const [waiting, setWaiting] = React.useState<boolean>(false)
  const { title, continueButton, privacyLabel } = prepareCopy(props)
  const { locale, resolve } = props

  function handleContinue (): void {
    if (checked && !waiting) {
      setWaiting(true)
      resolve?.({ __type__: 'PayloadVoid', value: undefined })
    }
  }

  function handleCheck (): void {
    setChecked(true)
  }

  function renderDescription (): JSX.Element {
    if (locale === 'nl') return nlDescription
    return enDescription
  }

  const enDescription: JSX.Element = (
    <>
      <div className='text-bodylarge font-body text-grey1'>
        <div className='mb-4 text-bodylarge font-body text-grey1'>
          You are about to start the process of donating your data to research institute ASCoR at Amsterdam University. The data that we ask you to donate will be used for academic research to gain insight into how social media platforms work.
        </div>
        <div className='mb-4 text-bodylarge font-body text-grey1'>
          We will walk you through this process step by step. During this process no data is stored or sent to ASCoR. You can delete rows from the data before donating. Data will only be donated and stored when you click the button “Yes, donate” on the page that shows your data.
        </div>
        <div className='mb-6 text-bodylarge font-body text-grey1'>
          By clicking the button “<span className='font-bodybold'>Yes, donate</span>”:
        </div>
        <div className='flex flex-col gap-3 mb-6'>
          <Bullet>
            <div>you fully and voluntarily agree to donate your data for this research.</div>
          </Bullet>
          <Bullet>
            <div>you are aware that when your data is used for academic publications, or made publicly available in some other form, this will be anonymous.</div>
          </Bullet>
          <Bullet>
            <div>you are aware that you have the right to withdraw your permission within 7 days by contacting Panel Inzicht.</div>
          </Bullet>
        </div>
        <div className='mb-10'>
          This website keeps track of your activity - for example on which pages of this website you click - as part of this research. More information can be found on our privacy page.
        </div>
      </div>
    </>
  )

  const nlDescription: JSX.Element = (
    <>
      <div className='text-bodylarge font-body text-grey1'>
        <div className='mb-4'>
          Via deze website kun je veilig je sociale media gesprekken delen met de onderzoekers van de Erasmus Universiteit Rotterdam.
        </div>
        <div className='mb-4'>
          Deze keer vragen we om de gehele Instagram data (als .zip bestand) met ons te delen. Deze website zal alleen de personen waarmee je praat op Instagram opslaan en hoevaak je met deze mensen praat. Alle namen worden vervangen door codes zodat er wij niet weten wie het zijn. Foto's en video's worden nooit met ons gedeeld, ook niet als deze voorkomen in de gesprekken.
        </div>
        <div className='mb-4'>
          We leggen stap voor stap uit hoe je dit kunt doen.
          </div>
        <div className='flex flex-col gap-3 mb-6'>
          <Bullet>
            <div> Eerst sleep je het .zip bestand in het kader, of kies je het .zip bestand vanaf je computer. Vervolgens zie je de gegevens zoals deze gedeeld zullen worden. Hier kun je ook kiezen om bepaalde mensen niet met ons te delen  door ze te verwijderen. Je  kunt hiervoor de zoekfunctie gebruiken om bepaalde mensen te zoeken en te verwijderen.  </div>
          </Bullet>
          <Bullet>
            <div> Pas als je op de knop "Versturen" klikt, worden de gegevens verstuurd en opgeslagen. Door op de knop “Versturen” te klikken geef je aan goed geïnformeerd te zijn over het onderzoek en vrijwillig je Instagram data met ons te delen.   </div>
          </Bullet>
        </div>

      </div>
    </>
  )

  const footer: JSX.Element = <Footer />

  const body: JSX.Element = (
    <>
      <Title1 text={title} />
      {renderDescription()}
      <div className='flex flex-col gap-8'>
        <div className='flex flex-row gap-4 items-center'>
          <CheckBox id='0' selected={checked} onSelect={() => handleCheck()} />
          <Label text={privacyLabel} />
        </div>
        <div className={`flex flex-row gap-4 ${checked ? '' : 'opacity-30'}`}>
          <PrimaryButton label={continueButton} onClick={handleContinue} enabled={checked} spinning={waiting} />
        </div>
      </div>
    </>
  )

  return (
    <Page
      body={body}
      footer={footer}
    />
  )
}

const title = new TextBundle()
  .add('en', 'Welcome')
  .add('nl', 'Welkom')

const continueButton = new TextBundle()
  .add('en', 'Start')
  .add('nl', 'Start')

const privacyLabel = new TextBundle()
  .add('en', 'I have read and agree with the above terms.')
  .add('nl', 'Ik heb deze voorwaarden gelezen en ben hiermee akkoord.')
