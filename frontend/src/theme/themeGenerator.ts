import { createTheme, PaletteOptions, ThemeOptions } from '@mui/material';
import { ColorPalette, ThemeMode } from '../contexts/ThemeContext';

// Define color palette options
const palettes: Record<ColorPalette, {
  light: PaletteOptions,
  dark: PaletteOptions
}> = {
  greyscale: {
    light: {
      primary: {
        main: '#424242',
        light: '#6d6d6d',
        dark: '#1b1b1b',
      },
      secondary: {
        main: '#757575',
        light: '#a4a4a4',
        dark: '#494949',
      },
      background: {
        default: '#f5f5f5',
        paper: '#ffffff',
      },
      text: {
        primary: '#212121',
        secondary: '#616161',
      },
    },
    dark: {
      primary: {
        main: '#9e9e9e',
        light: '#cfcfcf',
        dark: '#707070',
      },
      secondary: {
        main: '#757575',
        light: '#a4a4a4',
        dark: '#494949',
      },
      background: {
        default: '#121212',
        paper: '#1e1e1e',
      },
      text: {
        primary: '#e0e0e0',
        secondary: '#aaaaaa',
      },
    }
  },
  bold: {
    light: {
      primary: {
        main: '#1976d2',
        light: '#63a4ff',
        dark: '#004ba0',
      },
      secondary: {
        main: '#d32f2f',
        light: '#ff6659',
        dark: '#9a0007',
      },
      background: {
        default: '#f5f5f5',
        paper: '#ffffff',
      },
      success: {
        main: '#388e3c',
      },
      warning: {
        main: '#f57c00',
      },
      error: {
        main: '#d32f2f',
      },
    },
    dark: {
      primary: {
        main: '#42a5f5',
        light: '#80d6ff',
        dark: '#0077c2',
      },
      secondary: {
        main: '#ef5350',
        light: '#ff867c',
        dark: '#b61827',
      },
      background: {
        default: '#121212',
        paper: '#1e1e1e',
      },
      success: {
        main: '#4caf50',
      },
      warning: {
        main: '#ff9800',
      },
      error: {
        main: '#f44336',
      },
    }
  },
  pastel: {
    light: {
      primary: {
        main: '#90caf9',
        light: '#c3fdff',
        dark: '#5d99c6',
      },
      secondary: {
        main: '#ffcc80',
        light: '#ffffb0',
        dark: '#ca9b52',
      },
      background: {
        default: '#f8f8ff',
        paper: '#ffffff',
      },
      success: {
        main: '#a5d6a7',
      },
      warning: {
        main: '#ffe082',
      },
      error: {
        main: '#ef9a9a',
      },
    },
    dark: {
      primary: {
        main: '#80cbc4',
        light: '#b2fef7',
        dark: '#4f9a94',
      },
      secondary: {
        main: '#ce93d8',
        light: '#ffc4ff',
        dark: '#9c64a6',
      },
      background: {
        default: '#1a1a2e',
        paper: '#282a36',
      },
      success: {
        main: '#81c784',
      },
      warning: {
        main: '#ffb74d',
      },
      error: {
        main: '#e57373',
      },
    }
  }
};

// Common theme settings regardless of palette or mode
const commonOptions: ThemeOptions = {
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 4,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
  },
};

export function generateTheme(mode: ThemeMode, colorPalette: ColorPalette) {
  // Get the palette for the selected mode and color scheme
  const selectedPalette = palettes[colorPalette][mode];

  // Create and return the theme
  return createTheme({
    ...commonOptions,
    palette: {
      mode,
      ...selectedPalette,
    },
  });
}