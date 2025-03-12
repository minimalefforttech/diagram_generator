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
  Alert,
  Tooltip,
} from '@mui/material';
import ModelSelector from './ModelSelector';
import PaletteSelector, { DiagramPalette, getPaletteColors } from './PaletteSelector';
import AddIcon from '@mui/icons-material/Add';
import SendIcon from '@mui/icons-material/Send';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  model?: string;
}

interface ChatPanelProps {
  currentDiagram?: string;
  onRequestChanges: (message: string, model: string) => void;
  onNewDiagram: () => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  currentDiagram,
  onRequestChanges,
  onNewDiagram,
}) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [modelError, setModelError] = useState<string | null>(null);
  const [lastSelectedModel, setLastSelectedModel] = useState('');
  const [selectedPalette, setSelectedPalette] = useState<DiagramPalette>('greyscale');

  useEffect(() => {
    // Reset messages when diagram changes
    if (!currentDiagram) {
      setMessages([]);
    }
  }, [currentDiagram]);

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    setModelError(null);
    
    // Store last selected model to enable submitting with just model change
    if (model && model !== lastSelectedModel) {
      setLastSelectedModel(model);
    }
  };

  const handlePaletteChange = (palette: DiagramPalette) => {
    setSelectedPalette(palette);
    // Send palette change as a message
    const paletteMessage = `Use this color theme: ${getPaletteColors(palette)}`;
    handleSubmitMessage(paletteMessage);
  };

  const handleSubmitMessage = (messageContent: string) => {
    if (!selectedModel) {
      setModelError('Please select a model');
      return;
    }
    
    const newMessage = {
      role: 'user' as const,
      content: messageContent,
      timestamp: new Date().toISOString(),
      model: selectedModel,
    };

    setMessages([...messages, newMessage]);
    
    if (currentDiagram) {
      onRequestChanges(messageContent, selectedModel);
    } else {
      onNewDiagram(); // Should not reach here in the new UI flow, but handle it anyway
    }
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
    }
    
    if (!message.trim()) return;
    
    handleSubmitMessage(message);
    setMessage('');
    setLastSelectedModel(selectedModel);
  };

  // Allow submitting when only model is changed (no text input)
  const canSubmit = selectedModel && (message.trim() || (selectedModel !== lastSelectedModel));

  return (
    <Paper
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        minHeight: 0
      }}
    >
      {/* Header */}
      <Box sx={{ 
        p: 2, 
        borderBottom: 1, 
        borderColor: 'divider', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        flexShrink: 0
      }}>
        <Typography variant="h6">
          Chat
        </Typography>
        <Button
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={onNewDiagram}
          size="small"
        >
          New Diagram
        </Button>
      </Box>

      {/* Messages List */}
      <List sx={{ flexGrow: 1, overflow: 'auto', px: 2, minHeight: 0 }}>
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
                  <Box
                    sx={{
                      textAlign: msg.role === 'user' ? 'right' : 'left',
                      display: 'flex',
                      flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    <Typography variant="caption" color="textSecondary">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </Typography>
                    {msg.model && (
                      <Typography
                        variant="caption"
                        sx={{
                          backgroundColor: 'rgba(25, 118, 210, 0.1)',
                          borderRadius: 1,
                          px: 1,
                          py: 0.25,
                        }}
                      >
                        {msg.model}
                      </Typography>
                    )}
                  </Box>
                }
              />
            </ListItem>
            {index < messages.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>

      {modelError && (
        <Box sx={{ px: 2, pb: 2, flexShrink: 0 }}>
          <Alert severity="error" onClose={() => setModelError(null)}>
            {modelError}
          </Alert>
        </Box>
      )}

      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2, flexShrink: 0 }}>
        <PaletteSelector
          selectedPalette={selectedPalette}
          onChange={handlePaletteChange}
        />

        <ModelSelector
          selectedModel={selectedModel}
          onModelChange={handleModelChange}
        />

        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{
            display: 'flex',
            gap: 1,
          }}
        >
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Request diagram changes or just change the model..."
            variant="outlined"
            size="small"
          />
          <Tooltip title={message.trim() ? "Send message" : "Generate with selected model"}>
            <Button
              type="submit"
              variant="contained"
              disabled={!canSubmit}
              sx={{ alignSelf: 'stretch' }}
              endIcon={<SendIcon />}
              onClick={() => handleSubmit()}
            >
              Send
            </Button>
          </Tooltip>
        </Box>
      </Box>
    </Paper>
  );
};

export default ChatPanel;
