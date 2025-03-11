import { useState, useRef, useEffect } from 'react';
import { 
  Box, Typography, TextField, Button, Paper, 
  CircularProgress, Alert, Divider, Avatar, 
  List, ListItem, ListItemAvatar, ListItemText,
  useTheme
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { toast } from 'react-toastify';
import { diagramService, ConversationResponse, ConversationMessage } from '../../services/api';

interface ConversationPanelProps {
  diagramId: string;
  className?: string;
}

export function ConversationPanel({ diagramId, className = '' }: ConversationPanelProps) {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const theme = useTheme();

  // Scroll to bottom when new messages are added
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load existing conversation or create new one
  useEffect(() => {
    async function loadConversation() {
      try {
        try {
          // Try to use the actual API
          const conversations = await diagramService.listConversations(diagramId);
          if (conversations.length > 0) {
            const latestConversation = conversations[0];
            setConversationId(latestConversation.id);
            setMessages(latestConversation.messages);
            return;
          }
        } catch (apiError) {
          console.error('API Error when loading conversations:', apiError);
        }
        
        // Fallback to mock data if API fails or no conversations exist
        const mockMessages: ConversationMessage[] = [
          {
            role: 'system',
            content: 'Welcome to the diagram assistant. How can I help you with your diagram?',
            timestamp: new Date().toISOString(),
            metadata: {}
          }
        ];
        setMessages(mockMessages);
      } catch (err) {
        setError('Failed to load conversation history');
        console.error(err);
        toast.error('Failed to load conversation history');
      }
    }

    loadConversation();
  }, [diagramId]);

  const handleSubmit = async () => {
    if (!newMessage.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      // Add user message immediately for better UX
      const userMessage: ConversationMessage = {
        role: 'user',
        content: newMessage,
        timestamp: new Date().toISOString(),
        metadata: {}
      };
      
      setMessages(prev => [...prev, userMessage]);
      const currentMessage = newMessage;
      setNewMessage('');
      
      try {
        // Try to use the actual API
        let response: ConversationResponse;
        if (conversationId) {
          response = await diagramService.continueConversation(conversationId, currentMessage);
        } else {
          response = await diagramService.createConversation({
            diagram_id: diagramId,
            message: currentMessage,
          });
          setConversationId(response.id);
        }
        setMessages(response.messages);
      } catch (apiError) {
        console.error('API Error when sending message:', apiError);
        toast.warning('Using fallback response due to API error');
        
        // Fallback to mock response if API fails
        setTimeout(() => {
          const assistantMessage: ConversationMessage = {
            role: 'assistant',
            content: `I've analyzed your diagram and made some improvements. The structure looks good, but I've optimized the connections between nodes. (Mock response)`,
            timestamp: new Date().toISOString(),
            metadata: {}
          };
          
          setMessages(prev => [...prev, assistantMessage]);
        }, 1000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      toast.error('Failed to send message');
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      borderTop: `1px solid ${theme.palette.divider}`
    }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
        <Typography variant="subtitle1">Diagram Assistant</Typography>
      </Box>
      
      {/* Messages Area */}
      <Box sx={{ 
        flexGrow: 1, 
        overflow: 'auto', 
        p: 2,
        bgcolor: theme.palette.background.default
      }}>
        <List sx={{ p: 0 }}>
          {messages.map((message, index) => (
            <ListItem 
              key={index}
              alignItems="flex-start"
              sx={{ 
                flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                px: 1,
                py: 0.5
              }}
            >
              <ListItemAvatar sx={{ minWidth: 40 }}>
                <Avatar 
                  sx={{ 
                    width: 32, 
                    height: 32,
                    bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main'
                  }}
                >
                  {message.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                </Avatar>
              </ListItemAvatar>
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  maxWidth: '70%',
                  borderRadius: 2,
                  bgcolor: message.role === 'user' ? 'primary.light' : 'background.paper',
                  color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                  border: `1px solid ${theme.palette.divider}`
                }}
              >
                <Typography variant="body2">{message.content}</Typography>
              </Paper>
            </ListItem>
          ))}
          <div ref={messagesEndRef} />
        </List>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mx: 2, mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Input Area */}
      <Box sx={{ 
        p: 2, 
        borderTop: `1px solid ${theme.palette.divider}`,
        bgcolor: theme.palette.background.paper
      }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            size="small"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
            placeholder="Type your message..."
            disabled={isLoading}
            variant="outlined"
            sx={{ flexGrow: 1 }}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={handleSubmit}
            disabled={isLoading || !newMessage.trim()}
            endIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          >
            {isLoading ? 'Sending' : 'Send'}
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
