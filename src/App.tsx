import React, { useState, useRef, useEffect } from 'react';
import { Container, TextField, Button, Box, List, ListItem, ListItemText, Paper, Typography, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import './App.css';

// Define an interface for your message objects
interface Message {
  text: string;
  sender: 'user' | 'ai' | 'error'; // Union type for sender
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]); // Explicitly type useState
  const [inputMessage, setInputMessage] = useState<string>(''); // Explicitly type useState
  const [loading, setLoading] = useState<boolean>(false); // Explicitly type useState
  const messagesEndRef = useRef<HTMLDivElement>(null); // Type for useRef

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (inputMessage.trim() === '') return;

    const userMessage: Message = { text: inputMessage, sender: 'user' }; // Explicitly type message
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8080/api/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json', // Ensure content type is JSON
        },
        body: JSON.stringify({ message: inputMessage }), // Send as JSON string
      });

      if (!response.ok) {
        const errorData = await response.json(); // Assuming error response is also JSON
        throw new Error(errorData.response || `HTTP error! status: ${response.status}`);
      }

      const data: { response: string } = await response.json(); // Type the expected response
      const aiMessage: Message = { text: data.response, sender: 'ai' };
      setMessages((prevMessages) => [...prevMessages, aiMessage]);
    } catch (err: any) { // Type 'err' as any for simplicity in a quick demo
      console.error('Error sending message:', err);
      setMessages((prevMessages) => [...prevMessages, { text: `Error: ${err.message}`, sender: 'error' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLDivElement>) => { // Type the event
    if (event.key === 'Enter' && !loading) {
      sendMessage();
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4, display: 'flex', flexDirection: 'column', height: '85vh', borderRadius: 2, boxShadow: 3, overflow: 'hidden' }}>
      <Typography variant="h5" component="h1" gutterBottom sx={{ p: 2, backgroundColor: '#1976d2', color: 'white', borderRadius: '4px 4px 0 0' }}>
        HuggingFace Chatbot
      </Typography>

      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2, backgroundColor: '#e8f5e9' }}>
        <List>
          {messages.map((msg, index) => (
            <ListItem key={index} sx={{
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              textAlign: msg.sender === 'user' ? 'right' : 'left',
              mb: 1
            }}>
              <Paper
                elevation={1}
                sx={{
                  p: 1.5,
                  borderRadius: '15px',
                  backgroundColor: msg.sender === 'user' ? '#dcf8c6' : '#ffffff',
                  maxWidth: '80%',
                  wordBreak: 'break-word',
                  color: msg.sender === 'error' ? 'red' : 'inherit'
                }}
              >
                <ListItemText primary={msg.text} />
              </Paper>
            </ListItem>
          ))}
          <div ref={messagesEndRef} />
        </List>
      </Box>

      <Box sx={{ p: 2, display: 'flex', gap: 1, borderTop: '1px solid #e0e0e0', backgroundColor: '#f0f0f0' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          sx={{ '& fieldset': { borderRadius: '25px' } }}
        />
        <Button
          variant="contained"
          endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          onClick={sendMessage}
          disabled={loading || !inputMessage.trim()}
          sx={{ borderRadius: '25px', pl: 3, pr: 3 }}
        >
          Send
        </Button>
      </Box>
    </Container>
  );
}

export default App;