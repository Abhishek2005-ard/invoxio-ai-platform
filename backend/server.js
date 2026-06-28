const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const connectDB = require('./config/db');

// Load environment variables
dotenv.config();

// Connect to MongoDB
connectDB();

const app = express();

// Middleware
app.use(cors({
  origin: ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:3000'],
  credentials: true,
}));
app.use(express.json());

// Routes
app.use('/api/auth', require('./routes/auth'));

// Health check
app.get('/', (req, res) => {
  res.json({
    service: 'Invoxio Auth Server',
    status: 'running',
    version: '1.0.0',
    endpoints: {
      register: 'POST /api/auth/register',
      login: 'POST /api/auth/login',
      profile: 'GET /api/auth/me',
    },
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log('\n' + '='.concat('='.repeat(54)));
  console.log('  Invoxio Auth Server');
  console.log(`  Port:  ${PORT}`);
  console.log(`  Env:   ${process.env.NODE_ENV || 'development'}`);
  console.log(`  API:   http://localhost:${PORT}`);
  console.log('='.concat('='.repeat(54)) + '\n');
});
