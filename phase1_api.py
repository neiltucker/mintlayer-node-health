# File: phase1_api.py
from flask import Flask, jsonify

app = Flask(__name__)
PORT = 3033

# Dummy in-memory example data
nodes = [
    {'id': 1, 'name': 'Node A', 'version': 'v1.2.0', 'block_height': 1234567, 'peer_count': 12, 'online': True},
    {'id': 2, 'name': 'Node B', 'version': 'v1.1.9', 'block_height': 1234550, 'peer_count': 10, 'online': True}
]

alerts = [
    {'id': 1, 'node_id': 2, 'type': 'VersionOutdated', 'message': 'Node is behind network version', 'severity': 'warning'}
]

network_min_version = 'v1.2.0'

# --- Endpoints ---

@app.route('/health')
def health():
    local_node = nodes[0]
    return jsonify({
        'node_version': local_node['version'],
        'block_height': local_node['block_height'],
        'peer_count': local_node['peer_count'],
        'online_status': local_node['online']
    })

@app.route('/nodes')
def get_nodes():
    return jsonify(nodes)

@app.route('/node_alerts')
def get_alerts():
    return jsonify(alerts)

@app.route('/node/<int:node_id>')
def get_node(node_id):
    node = next((n for n in nodes if n['id'] == node_id), None)
    if not node:
        return jsonify({'error': 'Node not found'}), 404
    node_alerts = [a for a in alerts if a['node_id'] == node_id]
    return jsonify({**node, 'alerts': node_alerts})

@app.route('/fork_min_version')
def fork_min_version():
    return jsonify({'min_version': network_min_version})

if __name__ == '__main__':
    # Bind to localhost for security
    app.run(host='127.0.0.1', port=PORT)
