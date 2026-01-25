const express = require('express');
const app = express();
const PORT = 3033;

// Dummy example: replace with real polling logic
app.get('/health', (req, res) => {
  res.json({
    node_version: 'v1.2.0',
    block_height: 1234567,
    peer_count: 12,
    online_status: true
  });
});

// Bind only to localhost by default for safety
app.listen(PORT, '127.0.0.1', () => {
  console.log(`Read-only monitoring API running on 127.0.0.1:${PORT}`);
});
