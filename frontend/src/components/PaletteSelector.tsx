import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Typography,
} from '@mui/material';

export type DiagramPalette = 'greyscale' | 'bold' | 'pastel';

interface PaletteSelectorProps {
  selectedPalette: DiagramPalette;
  onChange: (palette: DiagramPalette) => void;
  disabled?: boolean;
}

// Define color sets for each palette
const palettes: Record<DiagramPalette, string[]> = {
  greyscale: ['#424242', '#757575', '#9e9e9e'],
  bold: ['#1976d2', '#d32f2f', '#388e3c'],
  pastel: ['#90caf9', '#ffcc80', '#a5d6a7']
};

// Helper to format palette name for display
const formatPaletteName = (name: DiagramPalette): string => {
  return name.charAt(0).toUpperCase() + name.slice(1);
};

// Helper to generate color theme string
export const getPaletteColors = (palette: DiagramPalette): string => {
  return `[${palettes[palette].join(', ')}]`;
};

const PaletteSelector: React.FC<PaletteSelectorProps> = ({
  selectedPalette,
  onChange,
  disabled = false
}) => {
  const handleChange = (event: SelectChangeEvent) => {
    onChange(event.target.value as DiagramPalette);
  };

  // Component to preview palette colors
  const PalettePreview = ({ colors }: { colors: string[] }) => (
    <Box sx={{ display: 'flex', gap: 0.5, ml: 1 }}>
      {colors.map((color, index) => (
        <Box 
          key={index}
          sx={{ 
            width: 16, 
            height: 16, 
            backgroundColor: color,
            borderRadius: '50%',
          }} 
        />
      ))}
    </Box>
  );

  return (
    <FormControl size="small" fullWidth disabled={disabled}>
      <InputLabel>Color Palette</InputLabel>
      <Select
        value={selectedPalette}
        label="Color Palette"
        onChange={handleChange}
      >
        {(Object.keys(palettes) as DiagramPalette[]).map((palette) => (
          <MenuItem 
            key={palette} 
            value={palette}
            sx={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Typography>{formatPaletteName(palette)}</Typography>
            <PalettePreview colors={palettes[palette]} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default PaletteSelector;