import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import RefreshIcon from '@mui/icons-material/Refresh';
import { diagramService } from '../services/api';
import { DiagramHistoryItem } from '../types';

interface DiagramHistoryProps {
  onSelectDiagram: (diagramId: string) => void;
  currentDiagramId?: string;
  alwaysExpanded?: boolean;
}

const DiagramHistory: React.FC<DiagramHistoryProps> = ({ onSelectDiagram, currentDiagramId, alwaysExpanded = false }) => {
  const [history, setHistory] = useState<DiagramHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const historyData = await diagramService.getDiagramHistory();
      setHistory(historyData);
    } catch (error) {
      console.error('Failed to fetch diagram history:', error);
      setError('Failed to load diagram history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleRefresh = (e: React.MouseEvent) => {
    e.stopPropagation();
    fetchHistory();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
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
        borderColor: 'divider'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HistoryIcon />
          <Typography variant="subtitle1">Diagram History</Typography>
        </Box>
        <IconButton
          size="small"
          onClick={handleRefresh}
          disabled={loading}
        >
          <RefreshIcon />
        </IconButton>
      </Box>
      
      <Box sx={{ 
        maxHeight: alwaysExpanded ? '100%' : 300, 
        flexGrow: 1,
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
        {loading ? (
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
            <CircularProgress size={24} />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ m: 1 }}>
            {error}
          </Alert>
        ) : history.length === 0 ? (
          <Typography sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
            No diagram history found
          </Typography>
        ) : (
          <List dense disablePadding>
            {history.map((item) => (
              <ListItem 
                key={item.id}
                disablePadding
                secondaryAction={
                  <Tooltip title="Time created">
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(item.createdAt)}
                    </Typography>
                  </Tooltip>
                }
              >
                <ListItemButton
                  selected={item.id === currentDiagramId}
                  onClick={() => onSelectDiagram(item.id)}
                >
                  <ListItemText 
                    primary={item.description}
                    secondary={
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Typography variant="caption" color="primary">
                          {item.syntax}
                        </Typography>
                        {item.iterations && (
                          <Typography variant="caption" color="text.secondary">
                            Iterations: {item.iterations}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Box>
    </Paper>
  );
};

export default DiagramHistory;