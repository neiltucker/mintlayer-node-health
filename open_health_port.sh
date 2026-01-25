# Allow only your monitoring server IP to access 3033
sudo ufw allow from <monitoring-server-IP> to any port 3033 proto tcp

# Deny all other access (optional, default policy)
sudo ufw deny 3033
