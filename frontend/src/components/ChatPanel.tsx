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
  Collapse,
  IconButton,
  useTheme,
} from '@mui/material';
import ModelSelector from './ModelSelector';
import PaletteSelector, { DiagramPalette, getPaletteColors } from './PaletteSelector';
import DiagramTypeSelector from './DiagramTypeSelector';
import SendIcon from '@mui/icons-material/Send';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  model?: string;
}

interface ChatPanelProps {
  currentDiagram?: string;
  onRequestChanges: (message: string, model: string) => void;
  onSyntaxChange?: (syntax: string) => void;
  onTypeChange?: (type: string) => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  currentDiagram,
  onRequestChanges,
  onSyntaxChange,
  onTypeChange,
}) => {
  const theme = useTheme();
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [modelError, setModelError] = useState<string | null>(null);
  const [lastSelectedModel, setLastSelectedModel] = useState('');
  const [selectedPalette, setSelectedPalette] = useState<DiagramPalette>('greyscale');
  const [currentSyntax, setCurrentSyntax] = useState('mermaid');
  const [currentType, setCurrentType] = useState('auto');
  const [settingsExpanded, setSettingsExpanded] = useState(true);

  const toggleSettings = () => {
    setSettingsExpanded(!settingsExpanded);
  };

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
    // Send palette change as a message with theme mode context
    const paletteMessage = `Use this color theme: ${getPaletteColors(palette)} on ${theme.palette.mode} background`;
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

  const handleSyntaxChange = (syntax: string) => {
    setCurrentSyntax(syntax);
    if (onSyntaxChange) {
      onSyntaxChange(syntax);
    }
    // Send syntax change as a message
    handleSubmitMessage(`Change diagram syntax to: ${syntax}`);
  };

  const handleTypeChange = (type: string) => {
    setCurrentType(type);
    if (onTypeChange) {
      onTypeChange(type);
    }
    // Send type change as a message
    handleSubmitMessage(`Change diagram type to: ${type}`);
  };

  return (
    <Paper sx={{ 
      flexGrow: 1,
      minHeight: 0,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      <Box sx={{ 
        p: 1.5, 
        borderBottom: 1, 
        borderColor: 'divider', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        flexShrink: 0,
        bgcolor: 'background.paper',
        cursor: 'pointer',
      }}
      onClick={toggleSettings}
      >
        <Typography variant="h6">
          Diagram Settings
        </Typography>
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            toggleSettings();
          }}
        >
          {settingsExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      <Collapse in={settingsExpanded}>
        <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2, flexShrink: 0, bgcolor: 'background.paper' }}>
          <DiagramTypeSelector
            currentSyntax={currentSyntax}
            currentType={currentType}
            onSyntaxChange={handleSyntaxChange}
            onTypeChange={handleTypeChange}
          />

          <PaletteSelector
            selectedPalette={selectedPalette}
            onChange={handlePaletteChange}
          />

          <ModelSelector
            selectedModel={selectedModel}
            onModelChange={handleModelChange}
          />
        </Box>
      </Collapse>

      <Divider />

      {/* Messages List */}
      <List sx={{ 
        flexGrow: 1, 
        overflow: 'auto', 
        px: 2,
        py: 1,
        minHeight: 0,
        bgcolor: (theme) => theme.palette.mode === 'dark' ? 'background.default' : 'grey.50',
        scrollbarWidth: 'thin',
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: 'rgba(255, 255, 255, 0.2)',
          borderRadius: '4px',
        }
      }}>
        {messages.map((msg, index) => (
          <React.Fragment key={index}>
            <ListItem
              alignItems="flex-start"
              sx={{
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                mb: 1,
              }}
            >
              <ListItemText
                primary={ 
                  <Typography
                    variant="body1"
                    sx={{
                      textAlign: msg.role === 'user' ? 'right' : 'left',
                      bgcolor: msg.role === 'user' ? 'primary.dark' : 'background.paper',
                      p: 1.5,
                      borderRadius: 2,
                      display: 'inline-block',
                      maxWidth: '80%',
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
                      mt: 0.5,
                    }}
                  >
                    <Typography variant="caption" color="textSecondary">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </Typography>
                    {msg.model && (
                      <Typography
                        variant="caption"
                        sx={{
                          backgroundColor: 'primary.main',
                          color: 'primary.contrastText',
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
            {index < messages.length - 1 && <Divider sx={{ my: 1 }} />}
          </React.Fragment>
        ))}
      </List>

      {/* Error Alert */}
      {modelError && (
        <Box sx={{ px: 2, py: 1, flexShrink: 0, bgcolor: 'background.paper' }}>
          <Alert severity="error" onClose={() => setModelError(null)}>
            {modelError}
          </Alert>
        </Box>
      )}

      {/* Chat Input */}
      <Box 
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: 2,
          display: 'flex',
          gap: 1,
          borderTop: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          flexShrink: 0,
        }}
      >
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Request diagram changes..."
          variant="outlined"
          size="small"
          sx={{
            '& .MuiOutlinedInput-root': {
              bgcolor: 'background.paper',
            }
          }}
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
    </Paper>
  );
};

export default ChatPanel;
