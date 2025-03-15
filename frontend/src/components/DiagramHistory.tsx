import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import { diagramService } from '../services/api';
import { DiagramHistoryItem } from '../types/generation';

interface DiagramHistoryProps {
  onSelectDiagram: (diagramId: string, syntax: string) => void;
  currentDiagramId?: string;
  alwaysExpanded?: boolean;
}

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

// Create a ref interface to expose methods
export interface DiagramHistoryRefHandle {
  refresh: () => Promise<void>;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({ open, title, message, onConfirm, onCancel }) => (
  <Dialog open={open} onClose={onCancel}>
    <DialogTitle>{title}</DialogTitle>
    <DialogContent>
      <DialogContentText>{message}</DialogContentText>
    </DialogContent>
    <DialogActions>
      <Button onClick={onCancel} color="primary">Cancel</Button>
      <Button onClick={onConfirm} color="error" variant="contained">Delete</Button>
    </DialogActions>
  </Dialog>
);

const DiagramHistory = forwardRef<DiagramHistoryRefHandle, DiagramHistoryProps>(({ 
  onSelectDiagram, 
  currentDiagramId, 
  alwaysExpanded = false 
}, ref) => {
  const [history, setHistory] = useState<DiagramHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState<boolean>(false);
  const [clearDialogOpen, setClearDialogOpen] = useState<boolean>(false);
  const [diagramToDelete, setDiagramToDelete] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const historyData = await diagramService.getDiagramHistory();
      // Ensure history is properly sorted by creation date
      const sortedHistory = [...historyData].sort((a, b) => 
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
      setHistory(sortedHistory);
    } catch (error) {
      console.error('Failed to fetch diagram history:', error);
      setError('Failed to load diagram history');
    } finally {
      setLoading(false);
    }
  };

  // Expose the refresh method via ref
  useImperativeHandle(ref, () => ({
    refresh: () => {
      return fetchHistory();
    }
  }));

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleRefresh = (e: React.MouseEvent) => {
    e.stopPropagation();
    fetchHistory();
  };

  const handleDeleteDiagram = async (id: string) => {
    try {
      await diagramService.deleteDiagram(id);
      fetchHistory();
    } catch (error) {
      console.error('Failed to delete diagram:', error);
      setError('Failed to delete diagram');
    }
  };

  const handleClearHistory = async () => {
    try {
      await diagramService.clearHistory();
      fetchHistory();
    } catch (error) {
      console.error('Failed to clear history:', error);
      setError('Failed to clear history');
    }
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
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Clear all history">
            <IconButton
              size="small"
              onClick={() => setClearDialogOpen(true)}
              disabled={loading || history.length === 0}
            >
              <DeleteSweepIcon />
            </IconButton>
          </Tooltip>
          <IconButton
            size="small"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshIcon />
          </IconButton>
        </Box>
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
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(item.createdAt)}
                    </Typography>
                    <Tooltip title="Delete diagram">
                      <IconButton 
                        edge="end" 
                        size="small" 
                        onClick={(e) => {
                          e.stopPropagation();
                          setDiagramToDelete(item.id);
                          setDeleteDialogOpen(true);
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                }
              >
                <Tooltip 
                  title={item.prompt}
                  placement="left"
                  enterDelay={500}
                >
                  <ListItemButton
                    selected={item.id === currentDiagramId}
                    onClick={() => onSelectDiagram(item.id, item.syntax)}
                  >
                    <ListItemText
                      primary={item.description || item.prompt}
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
                </Tooltip>
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Diagram"
        message="Are you sure you want to delete this diagram?"
        onConfirm={() => {
          if (diagramToDelete) {
            handleDeleteDiagram(diagramToDelete);
          }
          setDeleteDialogOpen(false);
          setDiagramToDelete(null);
        }}
        onCancel={() => {
          setDeleteDialogOpen(false);
          setDiagramToDelete(null);
        }}
      />

      <ConfirmDialog
        open={clearDialogOpen}
        title="Clear History"
        message="Are you sure you want to clear all diagram history? This action cannot be undone."
        onConfirm={() => {
          handleClearHistory();
          setClearDialogOpen(false);
        }}
        onCancel={() => setClearDialogOpen(false)}
      />
    </Paper>
  );
});

export default DiagramHistory;
