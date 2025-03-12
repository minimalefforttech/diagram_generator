import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ClearIcon from '@mui/icons-material/Clear';

interface LogEntry {
  type: 'error' | 'llm' | 'info';
  message: string;
  timestamp: string;
  details?: any;
}

interface OutputLogProps {
  entries?: LogEntry[];
}

const OutputLog: React.FC<OutputLogProps> = ({ entries = [] }) => {
  const [expanded, setExpanded] = useState(false);
  const [internalEntries, setInternalEntries] = useState<LogEntry[]>(entries);
  
  // Update internal entries when props change
  useEffect(() => {
    setInternalEntries(entries);
  }, [entries]);

  const handleClear = () => {
    setInternalEntries([]);
  };

  return (
    <Paper
      sx={{
        p: 1,
        maxHeight: expanded ? '40vh' : '2.5rem',
        transition: 'max-height 0.3s ease-in-out',
        overflow: 'hidden',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="subtitle2" color="textSecondary">
          Output Log
        </Typography>
        <Box>
          <IconButton size="small" onClick={handleClear}>
            <ClearIcon fontSize="small" />
          </IconButton>
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            <ExpandMoreIcon
              sx={{
                transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.3s ease-in-out',
              }}
            />
          </IconButton>
        </Box>
      </Box>

      {expanded && (
        <Box sx={{ mt: 1, maxHeight: '35vh', overflow: 'auto' }}>
          {internalEntries.map((entry, index) => (
            <Accordion
              key={index}
              sx={{ mb: 1 }}
              defaultExpanded={entry.type === 'error'}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography
                  color={
                    entry.type === 'error'
                      ? 'error'
                      : entry.type === 'llm'
                      ? 'info'
                      : 'textPrimary'
                  }
                  sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
                >
                  {entry.timestamp} - {entry.message}
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                {entry.type === 'llm' || (entry.type === 'error' && typeof entry.details === 'object') ? (
                  <pre
                    style={{
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      margin: 0,
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                    }}
                  >
                    {JSON.stringify(entry.details, null, 2)}
                  </pre>
                ) : (
                  <Typography
                    sx={{
                      fontFamily: entry.type === 'error' ? 'monospace' : 'inherit',
                      whiteSpace: entry.type === 'error' ? 'pre-wrap' : 'normal',
                      fontSize: entry.type === 'error' ? '0.875rem' : 'inherit',
                    }}
                  >
                    {entry.details}
                  </Typography>
                )}
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}
    </Paper>
  );
};

export default OutputLog;
