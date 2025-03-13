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

  const createEnhancedPrompt = (userMessage: string, isStyleChange = false): string => {
    // Ensure we have proper instructions based on diagram syntax
    const syntaxType = currentSyntax.toLowerCase();
    
    if (!currentDiagram) {
      return userMessage;
    }

    // Add current diagram code as context
    let enhancedPrompt = `Here is the current ${syntaxType} diagram:\n\n${currentDiagram}\n\n`;
    
    if (isStyleChange) {
      // For style changes, use a specific instruction set
      enhancedPrompt += `IMPORTANT: DO NOT CREATE A NEW DIAGRAM. Apply the requested styling to the EXISTING ${syntaxType} diagram above.\n\n`;
      enhancedPrompt += `Do ONLY the following actions:\n`;
      enhancedPrompt += `1. Keep all nodes, connections, and text from the existing diagram exactly as they are\n`;
      enhancedPrompt += `2. Only add style statements to apply the requested styles\n`;
      
      if (syntaxType === 'mermaid') {
        enhancedPrompt += `3. For nodes, add style statements like: style NodeName fill:#color\n`;
        enhancedPrompt += `4. For edges, add style statements like: linkStyle default stroke:#color\n`;
      } else if (syntaxType === 'plantuml') {
        enhancedPrompt += `3. Use skinparam commands for styling\n`;
        enhancedPrompt += `4. Use color keywords like: #color\n`;
      }
      
      enhancedPrompt += `5. Use contrasting text colors for readability\n\n`;
      enhancedPrompt += `Remember to preserve ALL existing diagram elements and connections. ONLY add style statements.\n\n`;
    } else {
      // For regular changes, use general instructions
      enhancedPrompt += `Please modify the ${syntaxType} diagram above according to this request:\n\n`;
    }

    // Add the user's actual request
    enhancedPrompt += userMessage;
    
    return enhancedPrompt;
  };

  const handlePaletteChange = (palette: DiagramPalette) => {
    setSelectedPalette(palette);
    
    // Get palette colors
    const colors = getPaletteColors(palette);
    const colorMode = theme.palette.mode;
    
    // Create a user-friendly message for display
    const paletteMessage = `Apply these colors to the diagram: ${colors} for a ${colorMode} background theme.`;
    
    // Store only the user-visible message in chat history
    addMessageToHistory(paletteMessage);
    
    // Send the enhanced message to the backend
    if (selectedModel && currentDiagram) {
      onRequestChanges(createEnhancedPrompt(paletteMessage, true), selectedModel);
    }
  };

  const addMessageToHistory = (displayContent: string) => {
    const newMessage = {
      role: 'user' as const,
      content: displayContent,
      timestamp: new Date().toISOString(),
      model: selectedModel,
    };

    setMessages([...messages, newMessage]);
  };

  const handleSubmitMessage = (userMessage: string) => {
    if (!selectedModel) {
      setModelError('Please select a model');
      return;
    }
    
    // Add user message to chat history (without the enhanced prompt)
    addMessageToHistory(userMessage);
    
    if (currentDiagram) {
      // Send the enhanced prompt to the backend
      const enhancedPrompt = createEnhancedPrompt(userMessage);
      onRequestChanges(enhancedPrompt, selectedModel);
    } else {
      // If no diagram exists yet, send the message as-is
      onRequestChanges(userMessage, selectedModel);
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
    
    // Add a user-friendly message to the chat
    const displayMessage = `Change diagram syntax to: ${syntax}`;
    addMessageToHistory(displayMessage);
    
    // Create enhanced message for the backend
    if (currentDiagram) {
      const enhancedPrompt = `Convert the current diagram to ${syntax} syntax while preserving all elements and relationships.`;
      onRequestChanges(createEnhancedPrompt(enhancedPrompt), selectedModel);
    }
  };

  const handleTypeChange = (type: string) => {
    setCurrentType(type);
    if (onTypeChange) {
      onTypeChange(type);
    }
    
    // Add a user-friendly message to the chat
    const displayMessage = `Change diagram type to: ${type}`;
    addMessageToHistory(displayMessage);
    
    // Create enhanced message for the backend
    if (currentDiagram) {
      const enhancedPrompt = `Convert the current diagram to a ${type} diagram while preserving the core information.`;
      onRequestChanges(createEnhancedPrompt(enhancedPrompt), selectedModel);
    }
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
