import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  FormControl,
  Select,
  MenuItem,
  SelectChangeEvent,
  Collapse,
  Grid,
  Tooltip
} from '@mui/material';
import { LogEntry } from '../types';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

interface OutputLogProps {
  entries: LogEntry[];
  alwaysExpanded?: boolean;
}

const OutputLog: React.FC<OutputLogProps> = ({ entries, alwaysExpanded = false }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [logLevel, setLogLevel] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [expanded, setExpanded] = useState(true);

  const handleLogLevelChange = (event: SelectChangeEvent) => {
    setLogLevel(event.target.value);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };

  const toggleExpanded = () => {
    if (!alwaysExpanded) {
      setExpanded(!expanded);
    }
  };

  // Filter logs based on search term and level
  const filteredEntries = entries.filter(entry => {
    const matchesSearch = 
      entry.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.type.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesLevel = logLevel === 'all' || entry.type === logLevel;
    
    return matchesSearch && matchesLevel;
  });

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  // Get color for log level
  const getLevelColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'error':
        return 'error';
      case 'llm':
        return 'info';
      case 'info':
        return 'default';
      default:
        return 'default';
    }
  };

  return (
    <Paper sx={{ 
      flexGrow: 1,
      display: 'flex', 
      flexDirection: 'column',
      overflow: 'hidden',
      height: '100%',
      borderRadius: alwaysExpanded ? 0 : undefined
    }}>
      <Box sx={{ 
        p: 1.5, 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: 1,
        borderColor: 'divider',
        cursor: alwaysExpanded ? 'default' : 'pointer'
      }}
      onClick={alwaysExpanded ? undefined : toggleExpanded}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle1">Log Output</Typography>
          <Chip 
            label={`${filteredEntries.length} entries`} 
            size="small" 
            color="primary" 
            variant="outlined"
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Toggle Filters">
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                toggleFilters();
              }}
            >
              <FilterListIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {!alwaysExpanded && (
            <IconButton size="small">
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          )}
        </Box>
      </Box>

      <Collapse in={showFilters}>
        <Box sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider' }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search logs..."
                value={searchTerm}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <Select
                  value={logLevel}
                  onChange={handleLogLevelChange}
                  displayEmpty
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="info">Info</MenuItem>
                  <MenuItem value="llm">LLM</MenuItem>
                  <MenuItem value="error">Error</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Box>
      </Collapse>

      <Collapse in={alwaysExpanded || expanded} sx={{ flexGrow: 1, minHeight: 0 }}>
        <List dense sx={{ 
          height: showFilters ? 'calc(100% - 60px)' : '100%',  
          overflow: 'auto',
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            borderRadius: '4px',
          }
        }}>
          {filteredEntries.length > 0 ? (
            filteredEntries.map((entry, index) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                        <Typography variant="body2" component="span" color="text.secondary" sx={{ minWidth: 65 }}>
                          {formatTime(entry.timestamp)}
                        </Typography>

                        <Chip
                          label={entry.type}
                          size="small"
                          color={getLevelColor(entry.type) as any}
                          variant="outlined"
                          sx={{ height: 20, minWidth: 60 }}
                        />

                        <Typography variant="body2" sx={{ wordBreak: 'break-word', flexGrow: 1 }}>
                          {entry.message}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                {index < filteredEntries.length - 1 && <Divider component="li" />}
              </React.Fragment>
            ))
          ) : (
            <ListItem>
              <ListItemText
                primary={
                  <Typography variant="body2" color="text.secondary" align="center">
                    {entries.length > 0 ? 'No matching logs found' : 'No logs available'}
                  </Typography>
                }
              />
            </ListItem>
          )}
        </List>
      </Collapse>
    </Paper>
  );
};

export default OutputLog;
