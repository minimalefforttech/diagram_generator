import React, { createContext, useContext, useState, useEffect } from 'react';

interface UIPreferences {
  sidebarWidth: number;
  chatPanelWidth: number;
}

interface UIPreferencesContextType {
  preferences: UIPreferences;
  updateSidebarWidth: (width: number) => void;
  updateChatPanelWidth: (width: number) => void;
}

const DEFAULT_PREFERENCES: UIPreferences = {
  sidebarWidth: 300,
  chatPanelWidth: 400
};

const UI_PREFERENCES_STORAGE_KEY = 'diagramGeneratorUIPreferences';

const UIPreferencesContext = createContext<UIPreferencesContextType | undefined>(undefined);

export const useUIPreferences = () => {
  const context = useContext(UIPreferencesContext);
  if (!context) {
    throw new Error('useUIPreferences must be used within a UIPreferencesProvider');
  }
  return context;
};

export const UIPreferencesProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [preferences, setPreferences] = useState<UIPreferences>(() => {
    try {
      const stored = localStorage.getItem(UI_PREFERENCES_STORAGE_KEY);
      return stored ? { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) } : DEFAULT_PREFERENCES;
    } catch (error) {
      console.error('Failed to parse stored UI preferences:', error);
      return DEFAULT_PREFERENCES;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(UI_PREFERENCES_STORAGE_KEY, JSON.stringify(preferences));
    } catch (error) {
      console.error('Failed to save UI preferences:', error);
    }
  }, [preferences]);

  const updateSidebarWidth = (width: number) => {
    setPreferences(prev => ({ ...prev, sidebarWidth: width }));
  };

  const updateChatPanelWidth = (width: number) => {
    setPreferences(prev => ({ ...prev, chatPanelWidth: width }));
  };

  return (
    <UIPreferencesContext.Provider value={{ 
      preferences, 
      updateSidebarWidth,
      updateChatPanelWidth
    }}>
      {children}
    </UIPreferencesContext.Provider>
  );
};