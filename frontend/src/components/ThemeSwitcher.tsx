import React from 'react';
import { 
  Box, 
  IconButton, 
  Tooltip,
  Menu,
  MenuItem,
  Typography,
  ButtonGroup,
  Button
} from '@mui/material';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import PaletteIcon from '@mui/icons-material/Palette';
import { ColorPalette, useTheme } from '../contexts/ThemeContext';

const ThemeSwitcher: React.FC = () => {
  const { mode, colorPalette, toggleMode, setColorPalette } = useTheme();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };
  
  const handleClose = () => {
    setAnchorEl(null);
  };
  
  const handlePaletteChange = (palette: ColorPalette) => {
    setColorPalette(palette);
    handleClose();
  };
  
  // Color preview boxes for each palette
  const palettePreview = (palette: ColorPalette) => {
    let colors: string[] = [];
    
    switch(palette) {
      case 'greyscale':
        colors = ['#424242', '#757575', '#9e9e9e'];
        break;
      case 'bold':
        colors = ['#1976d2', '#d32f2f', '#388e3c'];
        break;
      case 'pastel':
        colors = ['#90caf9', '#ffcc80', '#a5d6a7'];
        break;
    }
    
    return (
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
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <Tooltip title={mode === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
        <IconButton onClick={toggleMode} color="inherit">
          {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
        </IconButton>
      </Tooltip>
      
      <Tooltip title="Color Palette">
        <IconButton
          color="inherit"
          onClick={handleClick}
          aria-controls={open ? 'palette-menu' : undefined}
          aria-haspopup="true"
          aria-expanded={open ? 'true' : undefined}
        >
          <PaletteIcon />
        </IconButton>
      </Tooltip>
      
      <Menu
        id="palette-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        MenuListProps={{
          'aria-labelledby': 'palette-button',
        }}
      >
        <MenuItem 
          onClick={() => handlePaletteChange('greyscale')}
          selected={colorPalette === 'greyscale'}
          sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            minWidth: 180 
          }}
        >
          <Typography>Greyscale</Typography>
          {palettePreview('greyscale')}
        </MenuItem>
        
        <MenuItem 
          onClick={() => handlePaletteChange('bold')}
          selected={colorPalette === 'bold'}
          sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <Typography>Bold</Typography>
          {palettePreview('bold')}
        </MenuItem>
        
        <MenuItem 
          onClick={() => handlePaletteChange('pastel')}
          selected={colorPalette === 'pastel'}
          sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <Typography>Pastel</Typography>
          {palettePreview('pastel')}
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ThemeSwitcher;