import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import { createVuetify, type ThemeDefinition } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

const lightTheme: ThemeDefinition = {
  dark: false,
  colors: {
    primary: '#6750A4',
    secondary: '#625B71',
    surface: '#FEF7FF',
    background: '#FEF7FF',
    'surface-variant': '#E7E0EC',
    'on-surface': '#1D1B20',
    'on-surface-variant': '#49454F',
    error: '#B3261E',
  },
}

const darkTheme: ThemeDefinition = {
  dark: true,
  colors: {
    primary: '#D0BCFF',
    secondary: '#CCC2DC',
    surface: '#141218',
    background: '#141218',
    'surface-variant': '#49454F',
    'on-surface': '#E6E0E9',
    'on-surface-variant': '#CAC4D0',
    error: '#F2B8B5',
  },
}

export const vuetify = createVuetify({
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: 'darkTheme',
    themes: {
      lightTheme,
      darkTheme,
    },
  },
  defaults: {
    VBtn: {
      rounded: 'lg',
      variant: 'tonal',
    },
    VCard: {
      rounded: 'xl',
    },
    VDialog: {
      maxWidth: 880,
    },
    VSelect: {
      density: 'comfortable',
      variant: 'outlined',
    },
    VSwitch: {
      color: 'primary',
      inset: true,
    },
    VTextField: {
      density: 'comfortable',
      variant: 'outlined',
    },
    VTextarea: {
      autoGrow: true,
      density: 'comfortable',
      variant: 'outlined',
    },
    VAutocomplete: {
      chips: true,
      closableChips: true,
      density: 'comfortable',
      variant: 'outlined',
    },
  },
})

export default vuetify
