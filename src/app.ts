// src/app.ts
import express from 'express';

const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('<h1>Hello from AWS CI/CD Pipeline!</h1><p>Version 1.0</p>');
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});