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
  Alert,
  Collapse
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { diagramService } from '../services/api';

interface DiagramHistoryItem {
  id: string;
  createdAt: string;
  description: string;
  syntax: string;
  type: string;
  iterations?: number;
}

interface DiagramHistoryProps {
  onSelectDiagram: (diagramId: string) => void;
  currentDiagramId?: string;
}

const DiagramHistory: React.FC<DiagramHistoryProps> = ({ onSelectDiagram, currentDiagramId }) => {
  const [history, setHistory] = useState<DiagramHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<boolean>(false);

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

  const handleRefresh = () => {
    fetchHistory();
  };

  const toggleExpanded = () => {
    setExpanded(!expanded);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <Paper sx={{ 
      flexBasis: 200, 
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      <Box sx={{ 
        p: 1.5,
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: 1,
        borderColor: 'divider',
        cursor: 'pointer'
      }}
      onClick={toggleExpanded}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HistoryIcon />
          <Typography variant="subtitle1">Diagram History</Typography>
        </Box>
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            handleRefresh();
          }}
          disabled={loading}
        >
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      
      <Collapse in={expanded}>
        <Box sx={{ maxHeight: 300, overflow: 'auto',
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
      </Collapse>
    </Paper>
  );
};

export default DiagramHistory;