import React, { createContext, useContext, useState, useEffect } from 'react';

export type ThemeMode = 'light' | 'dark';
export type ColorPalette = 'greyscale' | 'bold' | 'pastel';

export interface ThemeContextType {
  mode: ThemeMode;
  colorPalette: ColorPalette;
  toggleMode: () => void;
  setColorPalette: (palette: ColorPalette) => void;
}

const defaultThemeContext: ThemeContextType = {
  mode: 'dark',
  colorPalette: 'greyscale',
  toggleMode: () => {},
  setColorPalette: () => {},
};

export const ThemeContext = createContext<ThemeContextType>(defaultThemeContext);

export const useTheme = () => useContext(ThemeContext);

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // Load saved theme settings from localStorage or use defaults
  const [mode, setMode] = useState<ThemeMode>(() => {
    const savedMode = localStorage.getItem('themeMode') as ThemeMode;
    return savedMode || 'dark';
  });

  const [colorPalette, setColorPalette] = useState<ColorPalette>(() => {
    const savedPalette = localStorage.getItem('colorPalette') as ColorPalette;
    return savedPalette || 'greyscale';
  });

  // Save theme settings to localStorage when they change
  useEffect(() => {
    localStorage.setItem('themeMode', mode);
  }, [mode]);

  useEffect(() => {
    localStorage.setItem('colorPalette', colorPalette);
  }, [colorPalette]);

  const toggleMode = () => {
    setMode(prevMode => (prevMode === 'light' ? 'dark' : 'light'));
  };

  const handleSetColorPalette = (palette: ColorPalette) => {
    setColorPalette(palette);
  };

  const value = {
    mode,
    colorPalette,
    toggleMode,
    setColorPalette: handleSetColorPalette,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};