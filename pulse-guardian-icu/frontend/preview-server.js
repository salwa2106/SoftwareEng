const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
app.use('/api', createProxyMiddleware({ target: 'http://localhost:8000', changeOrigin: true }));
app.use(express.static(path.join(__dirname, 'build')));
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});
app.listen(3000, () => console.log('Preview server on http://localhost:3000'));
