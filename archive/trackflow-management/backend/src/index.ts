import express from 'express';

const app = express();
app.use(express.json());

app.get('/', (req, res) => {
  res.send('TrackFlow Management System API');
});

// Placeholder routes for each module
app.use('/warehouse', (req, res) => res.send('Warehouse Operations API'));
app.use('/carrier', (req, res) => res.send('Carrier Management API'));
app.use('/reverse-logistics', (req, res) => res.send('Reverse Logistics API'));
app.use('/customer', (req, res) => res.send('Customer Experience API'));
app.use('/client', (req, res) => res.send('Client Relations API'));
app.use('/dashboard', (req, res) => res.send('Executive Dashboard API'));

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`);
});
