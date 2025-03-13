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
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Card,
  CardContent,
  CardHeader
} from '@mui/material';
import { LogEntry } from '../types';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import InfoIcon from '@mui/icons-material/Info';

interface OutputLogProps {
  entries: LogEntry[];
  alwaysExpanded?: boolean;
}

const OutputLog: React.FC<OutputLogProps> = ({ entries, alwaysExpanded = false }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [logLevel, setLogLevel] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [selectedEntry, setSelectedEntry] = useState<LogEntry | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

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

  const handleEntryClick = (entry: LogEntry) => {
    setSelectedEntry(entry);
    setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
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

  // Format details for display
  const formatDetails = (details: any): string => {
    if (!details) return 'No details available';
    
    if (typeof details === 'string') return details;
    
    try {
      return JSON.stringify(details, null, 2);
    } catch (e) {
      return String(details);
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
                <ListItem 
                  button 
                  onClick={() => handleEntryClick(entry)}
                  sx={{ 
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.08)'
                    }
                  }}
                >
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
                        
                        {entry.details && (
                          <Tooltip title="Has details">
                            <InfoIcon fontSize="small" color="action" />
                          </Tooltip>
                        )}
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
      
      {/* Log Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={handleCloseDetails}
        maxWidth="md"
        fullWidth
      >
        {selectedEntry && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label={selectedEntry.type}
                  size="small"
                  color={getLevelColor(selectedEntry.type) as any}
                />
                <Typography variant="h6">Log Entry Details</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                  {new Date(selectedEntry.timestamp).toLocaleString()}
                </Typography>
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              <Card variant="outlined" sx={{ mb: 2 }}>
                <CardHeader title="Message" />
                <CardContent>
                  <Typography variant="body1">{selectedEntry.message}</Typography>
                </CardContent>
              </Card>
              
              {selectedEntry.details && (
                <Card variant="outlined">
                  <CardHeader title="Details" />
                  <CardContent>
                    <Box
                      sx={{
                        backgroundColor: 'background.paper',
                        p: 2,
                        borderRadius: 1,
                        overflow: 'auto',
                        maxHeight: '400px',
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                      }}
                    >
                      {formatDetails(selectedEntry.details)}
                    </Box>
                  </CardContent>
                </Card>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDetails}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Paper>
  );
};

export default OutputLog;
