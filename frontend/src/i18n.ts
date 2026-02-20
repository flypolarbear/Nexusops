import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import enJSON from './locales/en.json'
import zhJSON from './locales/zh.json'

const resources = {
  en: {
    translation: enJSON,
  },
  zh: {
    translation: zhJSON,
  },
}

// Ensure default language is English if not previously set
const savedLang = localStorage.getItem('nexusops-lang') || 'en'

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: savedLang,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  })

// Add listener to persist language selection
i18n.on('languageChanged', (lng) => {
  localStorage.setItem('nexusops-lang', lng)
})

export default i18n