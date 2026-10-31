# Start server in one terminal:
opencode serve --hostname 127.0.0.1 --port 4096

# Set password from above command in another terminal:
export OPENCODE_SERVER_USERNAME=opencode
export OPENCODE_SERVER_PASSWORD='YOUR_PASSWORD'

# Then run this in second terminal (new session each time)
opencode run --server http://127.0.0.1:4096 --model opencode/deepseek-v4.1-flash-free "Remember this test code: PIE-73921. Reply only OK."

# List sessions
opencode session list --max-count 10 --format json

# With session persistance
opencode run --server http://127.0.0.1:4096 --session ses_e7e6899fdffe8GGC5w6mEgv77t --model opencode/deepseek-v4.1-flash-free \
  "What test code did I give you?"

