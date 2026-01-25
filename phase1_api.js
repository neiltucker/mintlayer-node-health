// File: phase1_api.js
const express = require('express');
const app = express();
const PORT = 3033;

// Dummy in-memory example data
const nodes = [
  { id: 1, name: 'Node A', version: 'v1.2.0', block_height: 1234567, peer_count: 12, online: true },
  { id: 2, name: 'Node B', version: 'v1.1.9', block_height: 1234550, peer_count: 10, online: true }
];

const alerts = [
  { id: 1, node_id: 2, type: 'VersionOutdated', message: 'Node is behind network version', severity: 'warning' }
];

const networkMinVersion = 'v1.2.0';

// Middleware for logging (optional)
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// --- Endpoints ---

// Health of the local node or server
app.get('/health', (req, res) => {
  res.json({
    node_version: nodes[0].version,
    block_height: nodes[0].block_height,
    peer_count: nodes[0].peer_count,
    online_status: nodes[0].online
  });
});

// List all nodes
app.get('/nodes', (req, res) => {
  res.json(nodes);
});

// Get node alerts
app.get('/node_alerts', (req, res) => {
  res.json(alerts);
});

// Get single node metrics
app.get('/node/:id', (req, res) => {
  const node = nodes.find(n => n.id === parseInt(req.params.id));
  if (!node) return res.status(404).json({ error: 'Node not found' });

  const nodeAlerts = alerts.filter(a => a.node_id === node.id);
  res.json({ ...node, alerts: nodeAlerts });
});

// Current network minimum version
app.get('/fork_min_version', (req, res) => {
  res.json({ min_version: networkMinVersion });
});

// Start server bound to localhost for security
app.listen(PORT, '127.0.0.1', () => {
  console.log(`Phase-1 read-only API running on http://127.0.0.1:${PORT}`);
});
