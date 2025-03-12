import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Alert,
} from '@mui/material';
import ModelSelector from './ModelSelector';
import AddIcon from '@mui/icons-material/Add';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatPanelProps {
  currentDiagram?: string;
  onRequestChanges: (message: string, model: string) => void;
  onNewDiagram: () => void;
  onCreateDiagram: (description: string, model: string) => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  currentDiagram,
  onRequestChanges,
  onNewDiagram,
  onCreateDiagram,
}) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [modelError, setModelError] = useState<string | null>(null);

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    setModelError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const newMessage = {
      role: 'user' as const,
      content: message,
      timestamp: new Date().toISOString(),
    };

    setMessages([...messages, newMessage]);
    
    if (currentDiagram) {
      onRequestChanges(message, selectedModel);
    } else {
      if (!selectedModel) {
        setModelError('Please select a model');
        return;
      }
      onCreateDiagram(message, selectedModel);
    }
    
    setMessage('');
  };

  return (
    <Paper
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">
          {currentDiagram ? 'Request Changes' : 'Create New Diagram'}
        </Typography>
      </Box>

      {/* Messages List */}
      <List sx={{ flexGrow: 1, overflow: 'auto', px: 2 }}>
        {messages.map((msg, index) => (
          <React.Fragment key={index}>
            <ListItem
              alignItems="flex-start"
              sx={{
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              <ListItemText
                primary={
                  <Typography
                    variant="body1"
                    sx={{
                      textAlign: msg.role === 'user' ? 'right' : 'left',
                    }}
                  >
                    {msg.content}
                  </Typography>
                }
                secondary={
                  <Typography
                    variant="caption"
                    color="textSecondary"
                    sx={{
                      textAlign: msg.role === 'user' ? 'right' : 'left',
                      display: 'block',
                    }}
                  >
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </Typography>
                }
              />
            </ListItem>
            {index < messages.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>

      {modelError && (
        <Box sx={{ px: 2, pb: 2 }}>
          <Alert severity="error" onClose={() => setModelError(null)}>
            {modelError}
          </Alert>
        </Box>
      )}

      <Box sx={{ px: 2 }}>
        <ModelSelector
          selectedModel={selectedModel}
          onModelChange={handleModelChange}
        />
      </Box>

      {/* Input Area */}
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          display: 'flex',
          gap: 1,
        }}
      >
        {currentDiagram && (
          <IconButton
            onClick={onNewDiagram}
            size="small"
            sx={{ alignSelf: 'center' }}
          >
            <AddIcon />
          </IconButton>
        )}
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={
            currentDiagram
              ? 'Request changes to the current diagram...'
              : 'Describe the diagram you want to create...'
          }
          variant="outlined"
          size="small"
        />
        <Button
          type="submit"
          variant="contained"
          disabled={!message.trim()}
          sx={{ alignSelf: 'stretch' }}
        >
          {currentDiagram ? 'Request Changes' : 'Create'}
        </Button>
      </Box>
    </Paper>
  );
};

export default ChatPanel;
